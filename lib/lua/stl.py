import lang.lua


def bind_stl(gen):
	gen.add_include('vector', True)

	gen.add_include('string', True)

	class LuaStringConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(lua_State *L, int idx) { return lua_isstring(L, idx) ? true : false; }\n' % self.check_func +\
			'void %s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_tostring(L, idx); }\n' % (self.to_c_func, self.ctype) +\
			'int %s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushstring(L, ((%s*)obj)->c_str()); return 1; }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(LuaStringConverter('std::string'))


class LuaTableToStdVectorConverter(lang.lua.LuaTypeConverterCommon):
	def __init__(self, type, T_conv):
		native_type = 'std::vector<%s>' % T_conv.ctype
		super().__init__(type, native_type, None, native_type)
		self.T_conv = T_conv

	def get_type_glue(self, gen, module_name):
		out = '''bool %s(lua_State *L, int idx) {
	if(!lua_istable(L, idx)) {
		return false;
	}
	lua_pushnil(L);
	while(lua_next(L,idx)) {
		if(!%s(L,-1)) {
			return false;
		}
		lua_pop(L,1);
	}
	return true;
}\n''' % (self.check_func, self.T_conv.check_func)

		out += '''void %s(lua_State *L, int idx, void *obj) {
	std::vector<%s> *sv = (std::vector<%s> *)obj;

	int size = (int)lua_rawlen(L, idx);
	sv->resize(size);
	for (int i = 0; i < size; ++i) {
		lua_rawgeti(L, idx, i+1);  
		%s v;
		%s(L, -1, &v);
		(*sv)[i] = %s;
	}
}\n''' % (self.to_c_func, self.T_conv.ctype, self.T_conv.ctype, self.T_conv.arg_storage_ctype, self.T_conv.to_c_func, self.T_conv.prepare_var_from_conv('v', ''))

		out += '''int %s(lua_State *L, void *obj, OwnershipPolicy own) {
	std::vector<%s> *sv = (std::vector<%s> *)obj;
	
	size_t size = sv->size();
	lua_newtable(L);
	for (int i = 0; i < size; ++i) {
		%s(L, &sv->at(i), Copy);
		lua_rawseti(L,-2,i+1);
	}
	return 1;
}\n''' % (self.from_c_func, self.T_conv.ctype, self.T_conv.ctype, self.T_conv.from_c_func)
		return out
