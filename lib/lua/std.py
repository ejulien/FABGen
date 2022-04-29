# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

import lang.lua


def bind_std(gen):
	gen.add_include('cstdint', True)

	class LuaBoolConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(lua_State *L, int idx) { return lua_isboolean(L, idx) ? true : false; }\n' % self.check_func +\
			'void %s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_toboolean(L, idx) == 1; }\n' % (self.to_c_func, self.ctype) +\
			'int %s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushboolean(L, *((%s*)obj) ? 1 : 0); return 1; }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(LuaBoolConverter('bool'))

	class LuaIntConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(lua_State *L, int idx) { return lua_isinteger(L, idx); }\n' % self.check_func +\
			'void %s(lua_State *L, int idx, void *obj) { *((%s*)obj) = (%s)lua_tointeger(L, idx); }\n' % (self.to_c_func, self.ctype, self.ctype) +\
			'int %s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushinteger(L, *((%s*)obj)); return 1; }\n' % (self.from_c_func, self.ctype)

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
	gen.bind_type(LuaIntConverter('intptr_t'))
	gen.bind_type(LuaIntConverter('size_t'))

	class LuaDoubleConverter(lang.lua.LuaTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(lua_State *L, int idx) { return lua_isnumber(L, idx); }\n' % self.check_func +\
			'void %s(lua_State *L, int idx, void *obj) { *((%s*)obj) = (%s)lua_tonumber(L, idx); }\n' % (self.to_c_func, self.ctype, self.ctype) +\
			'int %s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushnumber(L, *((%s*)obj)); return 1; }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(LuaDoubleConverter('float'))
	gen.bind_type(LuaDoubleConverter('double'))

	class LuaConstCharPtrConverter(lang.lua.LuaTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, True)

		def get_type_glue(self, gen, module_name):
			return 'struct %s { std::string s; };\n' % self.c_storage_class +\
			'bool %s(lua_State *L, int idx) { return lua_isstring(L, idx); }\n' % self.check_func +\
			'''void %s(lua_State *L, int idx, void *obj, %s &storage) {
	storage.s = lua_tostring(L, idx);
	*((%s*)obj) = storage.s.data();
}
''' % (self.to_c_func, self.c_storage_class, self.ctype) +\
			'int %s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushstring(L, (*(%s*)obj)); return 1; }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(LuaConstCharPtrConverter('const char *'))
