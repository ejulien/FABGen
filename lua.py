import gen


#
class LuaTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type):
		super().__init__(type)

	def return_void_from_c(self):
		return 'return 0;'


class LuaNativeTypeConverter(LuaTypeConverterCommon):
	def __init__(self, type):
		super().__init__(type)

	def new_var(self, name):
		out = '%s %s;\n' % (gen.get_fully_qualified_ctype_name(self.ctype), name)
		return (out, '&%s' % name)

	def to_c_ptr(self, obj, var_p):
		return '%s(L, %d, %s);\n' % (self.to_c, obj, var_p)

	def rval_from_c(self, i, count, var, func, own_policy):
		src = 'int rval_count = 0;\n' if i == 0 else ''
		src += 'rval_count += %s(L, %s, %s);\n' % (func, var, own_policy)
		if i == count - 1:
			src += 'return rval_count;'
		return src


#
class LuaGenerator(gen.FABGen):
	def start(self, namespace = None):
		super().start(namespace)

		# templates for class type exchange
		self.insert_code('''
// wrap a C object
template<typename NATIVE_OBJECT_WRAPPER_T> int _wrap_obj(lua_State *L, void *obj, const char *type_tag)
{
	auto p = lua_newuserdata(L, sizeof(NATIVE_OBJECT_WRAPPER_T));
	if (!p)
		return 0;

	new (p) NATIVE_OBJECT_WRAPPER_T(obj, type_tag);
	return 1;
}\n
''', True, False)

		# bind basic types
		class LuaNumberConverter(LuaNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return lua_isnumber(L, idx) ? true : false;"
				self.tmpl_to_c = "*val = lua_tonumber(L, idx);"
				self.tmpl_from_c = "lua_pushinteger(L, *val); return 1;"

		self.bind_type('int', LuaNumberConverter('int'))
		self.bind_type('float', LuaNumberConverter('float'))

		class LuaStringConverter(LuaNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return lua_isstring(L, idx) ? true : false;"
				self.tmpl_to_c = "*val = lua_tostring(L, idx);"
				self.tmpl_from_c = "lua_pushstring(L, val->c_str()); return 1;"

		self.bind_type('std::string', LuaStringConverter('std::string'))

		class LuaConstCharPtrConverter(LuaNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return lua_isstring(L, idx) ? true : false;"
				self.tmpl_to_c = "*val = lua_tostring(L, idx);"
				self.tmpl_from_c = "lua_pushstring(L, *val); return 1;"

	def proto_check(self, name, ctype):
		return 'bool %s(lua_State *L, int idx)' % (name)

	def proto_to_c(self, name, ctype):
		return 'void %s(lua_State *L, int idx, %s *obj)' % (name, gen.get_fully_qualified_ctype_name(ctype))

	def proto_from_c(self, name, ctype):
		return 'int %s(lua_State *L, %s *obj, OwnershipPolicy own_policy)' % (name, gen.get_fully_qualified_ctype_name(ctype))
