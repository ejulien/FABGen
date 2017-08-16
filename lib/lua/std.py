import lang.lua


def bind_std(gen):
	gen.add_include('cstdint', True)

	class LuaBoolConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool check_%s(lua_State *L, int idx) { return lua_isboolean(L, idx) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_toboolean(L, idx) == 1; }\n' % (self.bound_name, self.ctype) +\
			'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushboolean(L, *((%s*)obj) ? 1 : 0); return 1; }\n' % (self.bound_name, self.ctype)

	gen.bind_type(LuaBoolConverter('bool'))

	class LuaIntConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool check_%s(lua_State *L, int idx) { return lua_isnumber(L, idx) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = (%s)lua_tonumber(L, idx); }\n' % (self.bound_name, self.ctype, self.ctype) +\
			'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushinteger(L, *((%s*)obj)); return 1; }\n' % (self.bound_name, self.ctype)

	gen.bind_type(LuaIntConverter('char'))
	gen.bind_type(LuaIntConverter('short'))
	gen.bind_type(LuaIntConverter('int'))
	gen.bind_type(LuaIntConverter('long'))
	gen.bind_type(LuaIntConverter('int8_t'))
	gen.bind_type(LuaIntConverter('int16_t'))
	gen.bind_type(LuaIntConverter('int32_t'))
	gen.bind_type(LuaIntConverter('int64_t'))
	gen.bind_type(LuaIntConverter('char16_t'))
	gen.bind_type(LuaIntConverter('char32_t'))
	gen.bind_type(LuaIntConverter('unsigned char'))
	gen.bind_type(LuaIntConverter('unsigned short'))
	gen.bind_type(LuaIntConverter('unsigned int'))
	gen.bind_type(LuaIntConverter('unsigned long'))
	gen.bind_type(LuaIntConverter('uint8_t'))
	gen.bind_type(LuaIntConverter('uint16_t'))
	gen.bind_type(LuaIntConverter('uint32_t'))
	gen.bind_type(LuaIntConverter('uint64_t'))
	gen.bind_type(LuaIntConverter('size_t'))

	class LuaDoubleConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool check_%s(lua_State *L, int idx) { return lua_isnumber(L, idx) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = (%s)lua_tonumber(L, idx); }\n' % (self.bound_name, self.ctype, self.ctype) +\
			'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushnumber(L, *((%s*)obj)); return 1; }\n' % (self.bound_name, self.ctype)

	gen.bind_type(LuaDoubleConverter('float'))
	gen.bind_type(LuaDoubleConverter('double'))

	class LuaConstCharPtrConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool check_%s(lua_State *L, int idx) { return lua_isstring(L, idx) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_tostring(L, idx); }\n' % (self.bound_name, self.ctype) +\
			'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushstring(L, (*(%s*)obj)); return 1; }\n' % (self.bound_name, self.ctype)

	gen.bind_type(LuaConstCharPtrConverter('const char *'))
