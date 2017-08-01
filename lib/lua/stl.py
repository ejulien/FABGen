import lang.lua


def bind_stl(gen):
	gen.add_include('vector', True)

	gen.add_include('string', True)

	class LuaStringConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool check_%s(lua_State *L, int idx) { return lua_isstring(L, idx) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_tostring(L, idx); }\n' % (self.bound_name, self.ctype) +\
			'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushstring(L, ((%s*)obj)->c_str()); return 1; }\n' % (self.bound_name, self.ctype)

	gen.bind_type(LuaStringConverter('std::string'))
