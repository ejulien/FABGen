import gen


#
class LuaTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type, storage_type=None):
		super().__init__(type, storage_type)

	def get_type_api(self, module_name):
		return '// type API for %s\n' % self.fully_qualified_name +\
		'bool check_%s(lua_State *L, int idx);\n' % self.clean_name +\
		'void to_c_%s(lua_State *L, int idx, void *obj);\n' % self.clean_name +\
		'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy);\n' % self.clean_name

	def to_c_call(self, var, var_p):
		return 'to_c_%s(L, %s, %s);\n' % (self.clean_name, var, var_p)

	def from_c_call(self, ctype, var, var_p):
		return "from_c_%s(L, %s, %s);\n" % (self.clean_name, var_p, self.get_ownership_policy(ctype.get_ref()))


#
class LuaClassTypeDefaultConverter(LuaTypeConverterCommon):
	def __init__(self, type):
		super().__init__(type, type + '*')

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
	def get_langage(self):
		return "Lua"

	def start(self, module_name, namespace = None):
		super().start(module_name, namespace)

		# templates for class type exchange
		self.insert_code('''// wrap a C object
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
		class LuaNumberConverter(LuaTypeConverterCommon):
			def __init__(self, type):
				super().__init__(type)

			def output_type_glue(self):
				return 'bool check_%s(lua_State *L, int idx) { return lua_isnumber(L, idx) ? true : false; }\n' % self.clean_name +\
				'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_tonumber(L, idx); }\n' % (self.clean_name, self.ctype) +\
				'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushinteger(L, *((%s*)obj)); return 1; }\n' % (self.clean_name, self.ctype)

		self.bind_type(LuaNumberConverter('int'))
		self.bind_type(LuaNumberConverter('float'))

		class LuaStringConverter(LuaTypeConverterCommon):
			def __init__(self, type):
				super().__init__(type)

			def output_type_glue(self):
				return 'bool check_%s(lua_State *L, int idx) { return lua_isstring(L, idx) ? true : false; }\n' % self.clean_name +\
				'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_tostring(L, idx); }\n' % (self.clean_name, self.ctype) +\
				'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushstring(L, ((%s*)obj)->c_str()); return 1; }\n' % (self.clean_name, self.ctype)

		self.bind_type(LuaStringConverter('std::string'))

		class LuaConstCharPtrConverter(LuaTypeConverterCommon):
			def __init__(self, type):
				super().__init__(type)

			def output_type_glue(self):
				return 'bool check_%s(lua_State *L, int idx) { return lua_isstring(L, idx) ? true : false; }\n' % self.clean_name +\
				'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_tostring(L, idx); }\n' % (self.clean_name, self.ctype) +\
				'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushstring(L, (*(%s*)obj)); return 1; }\n' % (self.clean_name, self.ctype)

		self.bind_type(LuaConstCharPtrConverter('const char *'))

	def raise_exception(self, type, reason):
		self.__source += 'return 0; // FIXME'

	#
	def new_function(self, name, args):
		return "static int %s(lua_State *L) {\n" % name

	def get_arg(self, i, args):
		return "%d" % i

	# function call return values
	def begin_convert_rvals(self, rval):
		self._source += 'int rval_count = 0;\n'

	def return_void_from_c(self):
		return 'return 0;'

	def rval_from_c_ptr(self, ctype, var, conv, rval_p):
		self._source += 'rval_count += ' + conv.from_c_call(ctype, var, rval_p)

	def commit_rvals(self, rval):
		self._source += "return rval_count;\n"

	#
	def get_class_default_converter(self):
		return LuaClassTypeDefaultConverter
