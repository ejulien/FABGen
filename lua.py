import gen


#
class LuaTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type, storage_ref=''):
		super().__init__(type, storage_ref)

	def return_void_from_c(self):
		return 'return 0;'

	def to_c_ptr(self, var, var_p):
		return '%s(L, %s, %s);\n' % (self.to_c, var, var_p)

	def from_c_ptr(self, ctype, var, var_p):
		own_policy = self.get_ownership_policy(ctype.get_ref())
		return "%s(L, %s, %s);\n" % (self.from_c, var_p, own_policy)


#
class LuaNativeTypeConverter(LuaTypeConverterCommon):
	def __init__(self, type):
		super().__init__(type)


#
class LuaClassTypeDefaultConverter(LuaTypeConverterCommon):
	def __init__(self, type):
		super().__init__(type, '*')

	def tmpl_check(self):
		return '''
	auto p = lua_touserdata(L, idx);
	if (!p)
		return false;

	auto w = reinterpret_cast<NativeObjectWrapper *>(p);
	return w->IsNativeObjectWrapper() && w->GetTypeTag() == %s;
''' % self.type_tag

	def tmpl_to_c(self):
		return '''
	auto p = lua_touserdata(L, idx);
	auto w = reinterpret_cast<NativeObjectWrapper *>(p);
	*obj = reinterpret_cast<%s*>(w->GetObj());
''' % self.fully_qualified_name

	def tmpl_from_c(self):
		return '''
	switch (own_policy) {
		default:
		case NonOwning:
			return _wrap_obj<NativeObjectPtrWrapper<%s>>(L, obj, %s);
		case ByValue:
			return _wrap_obj<NativeObjectValueWrapper<%s>>(L, obj, %s);
	}
''' % (self.fully_qualified_name, self.type_tag, self.fully_qualified_name, self.type_tag)


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
				self.tmpl_to_c = "*obj = lua_tonumber(L, idx);"
				self.tmpl_from_c = "lua_pushinteger(L, *obj); return 1;"

		self.bind_type(LuaNumberConverter('int'))
		self.bind_type(LuaNumberConverter('float'))

		class LuaStringConverter(LuaNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return lua_isstring(L, idx) ? true : false;"
				self.tmpl_to_c = "*obj = lua_tostring(L, idx);"
				self.tmpl_from_c = "lua_pushstring(L, obj->c_str()); return 1;"

		self.bind_type(LuaStringConverter('std::string'))

		class LuaConstCharPtrConverter(LuaNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return lua_isstring(L, idx) ? true : false;"
				self.tmpl_to_c = "*obj = lua_tostring(L, idx);"
				self.tmpl_from_c = "lua_pushstring(L, *obj); return 1;"

		self.bind_type(LuaConstCharPtrConverter('const char *'))

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

	# function call return values
	def begin_convert_rvals(self):
		self._source += 'int rval_count = 0;\n'

	def rval_from_c_ptr(self, ctype, var, conv, rval_p):
		self._source += 'rval_count += ' + conv.from_c_ptr(ctype, var, rval_p)

	def commit_rvals(self, rvals, rval_names):
		self._source += "return rval_count;\n"

	#
	def get_class_default_converter(self):
		return LuaClassTypeDefaultConverter
