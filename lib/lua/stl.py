# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

import lang.lua


def bind_stl(gen):
	gen.add_include('vector', True)
	gen.add_include('string', True)

	class LuaStringConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(lua_State *L, int idx) { return lua_type(L, idx) == LUA_TSTRING; }\n' % self.check_func +\
			'void %s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_tostring(L, idx); }\n' % (self.to_c_func, self.ctype) +\
			'int %s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushstring(L, ((%s*)obj)->c_str()); return 1; }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(LuaStringConverter('std::string'))


def bind_function_T(gen, type, bound_name=None):
	gen.add_include('functional', True)

	class LuaStdFunctionConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			check = 'bool %s(lua_State *L, int idx) { return lua_isfunction(L, idx); }\n' % self.check_func

			func = self.ctype.template.function

			if hasattr(func, 'void_return'):
				return_type = 'void'
			else:
				return_type = str(func.return_type)

			parms = []
			if hasattr(func, 'parms'):
				parms = [str(parm) for parm in func.parms]

			to_c = '''\
void %s(lua_State *L, int idx, void *obj) {
	LuaValueRef ref(L, idx);
	*((%s*)obj) = [=](%s) -> %s {
		ref.Push();
	};
}
''' % (self.to_c_func, self.ctype, ', '.join(['%s v%d' % (parm, idx) for idx, parm in enumerate(parms)]), return_type)

			from_c = '''\
int %s(lua_State *L, void *obj, OwnershipPolicy) {
	lua_pushcfunction(L, [](lua_State *L) -> int {
		return 0; // TODO
	});
	return 1;
}
''' % (self.from_c_func)
			return check + to_c + from_c

	return gen.bind_type(LuaStdFunctionConverter(type))


class LuaTableToStdVectorConverter(lang.lua.LuaTypeConverterCommon):
	def __init__(self, type, T_conv):
		native_type = 'std::vector<%s>' % T_conv.ctype
		super().__init__(type, native_type, None, native_type)
		self.T_conv = T_conv

	def get_type_glue(self, gen, module_name):
		out = '''bool %s(lua_State *L, int idx) {
	if (!lua_istable(L, idx))
		return false;

	lua_pushnil(L);
	while (lua_next(L, idx)) {
		if (!%s(L, -1))
			return false;
		lua_pop(L, 1);
	}

	return true;
}\n''' % (self.check_func, self.T_conv.check_func)

		out += '''void %s(lua_State *L, int idx, void *obj) {
	std::vector<%s> *sv = (std::vector<%s> *)obj;

	size_t size = lua_rawlen(L, idx);
	sv->resize(size);
	for (size_t i = 0; i < size; ++i) {
		lua_rawgeti(L, idx, lua_Integer(i+1));
		%s v;
		%s(L, -1, &v);
		(*sv)[i] = %s;
	}
}\n''' % (self.to_c_func, self.T_conv.ctype, self.T_conv.ctype, self.T_conv.arg_storage_ctype, self.T_conv.to_c_func, self.T_conv.prepare_var_from_conv('v', ''))

		out += '''int %s(lua_State *L, void *obj, OwnershipPolicy own) {
	std::vector<%s> *sv = (std::vector<%s> *)obj;
	
	size_t size = sv->size();
	lua_newtable(L);
	for (size_t i = 0; i < size; ++i) {
		%s(L, &sv->at(i), Copy);
		lua_rawseti(L, -2, lua_Integer(i+1));
	}
	return 1;
}\n''' % (self.from_c_func, self.T_conv.ctype, self.T_conv.ctype, self.T_conv.from_c_func)
		return out
