import gen


#
class LuaTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type, storage_type=None):
		super().__init__(type, storage_type)

	def get_type_api(self, module_name):
		return '// type API for %s\n' % self.ctype +\
		'bool check_%s(lua_State *L, int idx);\n' % self.bound_name +\
		'void to_c_%s(lua_State *L, int idx, void *obj);\n' % self.bound_name +\
		'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy);\n' % self.bound_name +\
		'\n'

	def to_c_call(self, in_var, out_var_p):
		return 'to_c_%s(L, %s, %s);\n' % (self.bound_name, in_var, out_var_p)

	def from_c_call(self, out_var, expr, ownership):
		return "from_c_%s(L, %s, %s);\n" % (self.bound_name, expr, ownership)

	def check_call(self, in_var):
		return "check_%s(L, %s)" % (self.bound_name, in_var)


#
class LuaClassTypeDefaultConverter(LuaTypeConverterCommon):
	def __init__(self, type, arg_storage_type=None, bound_name=None, rval_storage_type=None):
		super().__init__(type, arg_storage_type, bound_name, rval_storage_type)

	def get_type_glue(self, gen, module_name):
		out = ''

		# to/from C
		out += '''bool check_%s(lua_State *L, int idx) {
	auto p = lua_touserdata(L, idx);
	if (!p)
		return false;

	auto w = reinterpret_cast<NativeObjectWrapper *>(p);
	return w->IsNativeObjectWrapper() && w->GetTypeTag() == %s;
}\n''' % (self.bound_name, self.type_tag)

		out += '''void to_c_%s(lua_State *L, int idx, void *obj) {
	auto p = lua_touserdata(L, idx);
	auto w = reinterpret_cast<NativeObjectWrapper *>(p);
	*obj = reinterpret_cast<%s*>(w->GetObj());
}\n''' % (self.bound_name, self.ctype)

		out += '''int from_c_%s(lua_State *L, void *obj, OwnershipPolicy own_policy) {
	switch (own_policy) {
		default:
		case NonOwning:
			return _wrap_obj<NativeObjectPtrWrapper<%s>>(L, obj, %s);
		case Owning:
			return _wrap_obj<NativeObjectValueWrapper<%s>>(L, obj, %s);
	}
}\n''' % (self.bound_name, self.type_tag, self.ctype, self.type_tag, self.type_tag)

		return out

	def finalize_type(self):
		out = ''
		return out


#
class LuaGenerator(gen.FABGen):
	default_class_converter = LuaClassTypeDefaultConverter

	def get_language(self):
		return "Lua"

	def output_includes(self):
		super().output_includes()

		self._source += '''extern "C" {
#include "lauxlib.h"
#include "lua.h"
}
\n'''

	def start(self, module_name):
		super().start(module_name)

		# templates for class type exchange
		self.insert_code('''// wrap a C object
template<typename NATIVE_OBJECT_WRAPPER_T> int _wrap_obj(lua_State *L, void *obj, const char *type_tag) {
	auto p = lua_newuserdata(L, sizeof(NATIVE_OBJECT_WRAPPER_T));
	if (!p)
		return 0;

	new (p) NATIVE_OBJECT_WRAPPER_T(obj, type_tag);
	return 1;
}\n
''', True, False)

		# bind basic types
		class LuaIntConverter(LuaTypeConverterCommon):
			def get_type_glue(self, gen, module_name):
				return 'bool check_%s(lua_State *L, int idx) { return lua_isnumber(L, idx) ? true : false; }\n' % self.bound_name +\
				'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = (%s)lua_tonumber(L, idx); }\n' % (self.bound_name, self.ctype, self.ctype) +\
				'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushinteger(L, *((%s*)obj)); return 1; }\n' % (self.bound_name, self.ctype)

		self.bind_type(LuaIntConverter('int'))

		class LuaDoubleConverter(LuaTypeConverterCommon):
			def get_type_glue(self, gen, module_name):
				return 'bool check_%s(lua_State *L, int idx) { return lua_isnumber(L, idx) ? true : false; }\n' % self.bound_name +\
				'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = (%s)lua_tonumber(L, idx); }\n' % (self.bound_name, self.ctype, self.ctype) +\
				'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushnumber(L, *((%s*)obj)); return 1; }\n' % (self.bound_name, self.ctype)

		self.bind_type(LuaDoubleConverter('float'))

		class LuaStringConverter(LuaTypeConverterCommon):
			def get_type_glue(self, gen, module_name):
				return 'bool check_%s(lua_State *L, int idx) { return lua_isstring(L, idx) ? true : false; }\n' % self.bound_name +\
				'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_tostring(L, idx); }\n' % (self.bound_name, self.ctype) +\
				'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushstring(L, ((%s*)obj)->c_str()); return 1; }\n' % (self.bound_name, self.ctype)

		self.bind_type(LuaStringConverter('std::string'))

		class LuaConstCharPtrConverter(LuaTypeConverterCommon):
			def get_type_glue(self, gen, module_name):
				return 'bool check_%s(lua_State *L, int idx) { return lua_isstring(L, idx) ? true : false; }\n' % self.bound_name +\
				'void to_c_%s(lua_State *L, int idx, void *obj) { *((%s*)obj) = lua_tostring(L, idx); }\n' % (self.bound_name, self.ctype) +\
				'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushstring(L, (*(%s*)obj)); return 1; }\n' % (self.bound_name, self.ctype)

		self.bind_type(LuaConstCharPtrConverter('const char *'))

	#
	def set_error(self, type, reason):
		return 'return luaL_error(L, "%s");\n' % reason

	#
	def get_self(self, ctx):
		return 'self'

	def get_arg(self, i, ctx):
		return "%d" % (i+1)

	def open_proxy(self, name, max_arg_count, ctx):
		return '''static int %s(lua_State *L) {
	int arg_count = lua_gettop(L), rval_count = 0;

''' % name

	def close_proxy(self, ctx):
		return '	return 0;\n}\n'

	def proxy_call_error(self, msg, ctx):
		out = self.set_error('runtime', msg)

		if ctx == 'setter':
			out += 'return -1;\n'
		else:
			out += 'return NULL;\n'

		return out

	# function call return values
	def return_void_from_c(self):
		return 'return 0;'

	def rval_from_c_ptr(self, conv, out_var, expr, ownership):
		return 'rval_count += ' + conv.from_c_call(out_var, expr, ownership)

	def commit_rvals(self, rvals, ctx='default'):
		return "return rval_count;\n"

	#
	def finalize(self):
		super().finalize()

		# output module functions table
		self._source += 'static const luaL_Reg %s_funcs[] = {\n' % self._name
		for f in self._bound_functions:
			self._source += '	{"%s", %s},\n' % (f['bound_name'], f['proxy_name'])
		self._source += '	{NULL, NULL}};\n\n'

		# registration function
		self._source += '''\
#if WIN32
 #define _DLL_EXPORT_ __declspec(dllexport)
#endif
\n'''

		self._source += 'extern "C" _DLL_EXPORT_ int luaopen_%s(lua_State* L) {\n' % self._name
		self._source += '	lua_newtable(L);\n'
		self._source += '	luaL_setfuncs(L, %s_funcs, 0);\n' % self._name
		self._source += '	return 1;\n'
		self._source += '}\n'
