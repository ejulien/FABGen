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

	def to_c_ptr(self, var, var_p):
		return '%s(L, %s, %s);\n' % (self.to_c, var, var_p)

	def from_c_ptr(self, var, var_p):
		return "%s(L, %s, ByValue);\n" % (self.from_c, var_p)


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

		self.bind_type(LuaNumberConverter('int'))
		self.bind_type(LuaNumberConverter('float'))

		class LuaStringConverter(LuaNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return lua_isstring(L, idx) ? true : false;"
				self.tmpl_to_c = "*val = lua_tostring(L, idx);"
				self.tmpl_from_c = "lua_pushstring(L, val->c_str()); return 1;"

		self.bind_type(LuaStringConverter('std::string'))

		class LuaConstCharPtrConverter(LuaNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return lua_isstring(L, idx) ? true : false;"
				self.tmpl_to_c = "*val = lua_tostring(L, idx);"
				self.tmpl_from_c = "lua_pushstring(L, *val); return 1;"

		self.bind_type(LuaStringConverter('const char *'))

	def proto_check(self, name, ctype):
		return 'bool %s(lua_State *L, int idx)' % (name)

	def proto_to_c(self, name, ctype):
		return 'void %s(lua_State *L, int idx, %s *obj)' % (name, gen.get_fully_qualified_ctype_name(ctype))

	def proto_from_c(self, name, ctype):
		return 'int %s(lua_State *L, %s *obj, OwnershipPolicy own_policy)' % (name, gen.get_fully_qualified_ctype_name(ctype))

	def new_function(self, name, args):
		return "static int %s(lua_State *L) {\n" % name

	def get_arg(self, i, args):
		return "%d" % i

	def commit_rvals(self, rvals, rval_names):
		return 'return %d;\n' % len(rvals)
