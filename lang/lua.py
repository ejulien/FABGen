import gen


#
class LuaTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type, storage_type=None, bound_name=None, rval_storage_type=None):
		super().__init__(type, storage_type, bound_name, rval_storage_type)

	def get_type_api(self, module_name):
		return '// type API for %s\n' % self.ctype +\
		'bool check_%s(lua_State *L, int idx);\n' % self.bound_name +\
		'void to_c_%s(lua_State *L, int idx, void *obj);\n' % self.bound_name +\
		'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy);\n' % self.bound_name +\
		'\n'

	def to_c_call(self, in_var, out_var_p):
		return 'to_c_%s(L, %s, %s);\n' % (self.bound_name, in_var, out_var_p)

	def from_c_call(self, out_var, expr, ownership):
		return "from_c_%s(L, (void *)%s, %s);\n" % (self.bound_name, expr, ownership)

	def check_call(self, in_var):
		return "check_%s(L, %s)" % (self.bound_name, in_var)


#
class LuaClassTypeDefaultConverter(LuaTypeConverterCommon):
	def __init__(self, type, arg_storage_type=None, bound_name=None, rval_storage_type=None):
		super().__init__(type, arg_storage_type, bound_name, rval_storage_type)

	def get_type_glue(self, gen, module_name):
		out = ''

		# type index dispatching logic
		gen.add_include('map', True)
		gen.add_include('string', True)

		out += 'std::map<std::string, int (*)(lua_State *)> mt_get_index_map_%s = {\n' % self.bound_name
		entries = []
		for m in self.get_all_members():
			entries.append('	{"%s", %s}' % (m['name'], m['getter']))
		for m in self.get_all_static_members():
			entries.append('	{"%s", %s}' % (m['name'], m['getter']))
		out += ',\n'.join(entries)
		out += '\n};\n\n'

		out += 'static int mt_get_index_%s(lua_State *L) {\n' % self.bound_name
		out += '''\
	std::string key = lua_tostring(L, -1);
	lua_pop(L, 1);
	auto i = mt_get_index_map_%s.find(key);
	return i == mt_get_index_map_%s.end() ? 0 : i->second(L);
}\n\n''' % (self.bound_name, self.bound_name)

		out += 'std::map<std::string, int (*)(lua_State *)> mt_set_index_map_%s = {\n' % self.bound_name
		entries = []
		for m in self.get_all_members():
			if m['setter']:
				entries.append('	{"%s", %s}' % (m['name'], m['setter']))
		for m in self.get_all_static_members():
			if m['setter']:
				entries.append('	{"%s", %s}' % (m['name'], m['setter']))
		out += ',\n'.join(entries)
		out += '\n};\n\n'

		out += 'static int mt_set_index_%s(lua_State *L) {\n' % self.bound_name
		out += '''\
	std::string key = lua_tostring(L, -2);
	lua_remove(L, -2);
	auto i = mt_set_index_map_%s.find(key);
	return i == mt_set_index_map_%s.end() ? 0 : i->second(L);
}\n\n''' % (self.bound_name, self.bound_name)

		# type meta
		out += 'static const luaL_Reg %s_meta[] = {\n' % self.bound_name
		out += '	{"__gc", wrapped_Object_gc},\n'
		out += '	{"__index", mt_get_index_%s},\n' % self.bound_name
		out += '	{"__newindex", mt_set_index_%s},\n' % self.bound_name
		out += '	{NULL, NULL}};\n\n'

		# type registration
		out += 'void register_%s(lua_State *L) {\n' % self.bound_name
		out += '	luaL_newmetatable(L, "%s");\n' % self.bound_name
		out += '	luaL_setfuncs(L, %s_meta, 0);\n' % self.bound_name
		out += '	lua_pop(L, 1);\n'  # pop metatable
		out += '}\n\n'

		# delete delegate
		out += 'static void delete_%s(void *o) { delete (%s *)o; }\n\n' % (self.bound_name, self.ctype)

		# to/from C
		out += '''bool check_%s(lua_State *L, int idx) {
	wrapped_Object *w = cast_to_wrapped_Object_safe(L, idx);
	if (!w)
		return false;
	return _type_tag_can_cast(w->type_tag, %s);
}\n''' % (self.bound_name, self.type_tag)

		out += '''void to_c_%s(lua_State *L, int idx, void *obj) {
	wrapped_Object *w = cast_to_wrapped_Object_unsafe(L, idx);
	*(void **)obj = _type_tag_cast(w->obj, w->type_tag, %s);
}\n''' % (self.bound_name, self.type_tag)

		if self._non_copyable:
			if self._moveable:
				copy_code = 'obj = new %s(std::move(*(%s *)obj));' % (self.ctype, self.ctype)
			else:
				copy_code = 'return luaL_error(L, "type %s is non-copyable and non-moveable");' % self.bound_name
		else:
			copy_code = 'obj = new %s(*(%s *)obj);' % (self.ctype, self.ctype)

		out += '''int from_c_%s(lua_State *L, void *obj, OwnershipPolicy own) {
	wrapped_Object *w = (wrapped_Object *)lua_newuserdata(L, sizeof(wrapped_Object));
	if (own == Copy) {
		%s
	}
	init_wrapped_Object(w, %s, obj);
	if (own != NonOwning)
		w->on_delete = &delete_%s;
	luaL_setmetatable(L, "%s");
	return 1;
}
\n''' % (self.bound_name, copy_code, self.type_tag, self.bound_name, self.bound_name)

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

		self._source += '''\
typedef struct {
	uint32_t magic_u32; // wrapped_Object marker
	const char *type_tag; // wrapped pointer type tag

	void *obj;

	void (*on_delete)(void *);
} wrapped_Object;

static void init_wrapped_Object(wrapped_Object *o, const char *type_tag, void *obj) {
	o->magic_u32 = 0x46414221;
	o->type_tag = type_tag;

	o->obj = obj;

	o->on_delete = NULL;
}

static wrapped_Object *cast_to_wrapped_Object_safe(lua_State *L, int idx) {
	wrapped_Object *w = (wrapped_Object *)lua_touserdata(L, idx);
	if (!w || w->magic_u32 != 0x46414221)
		return NULL;
	return w;
}

static wrapped_Object *cast_to_wrapped_Object_unsafe(lua_State *L, int idx) { return (wrapped_Object *)lua_touserdata(L, idx); }

static int wrapped_Object_gc(lua_State *L) {
	wrapped_Object *w = cast_to_wrapped_Object_unsafe(L, 1);

	if (w->on_delete)
		w->on_delete(w->obj);

	return 0;
}
\n'''

	#
	def set_error(self, type, reason):
		return 'return luaL_error(L, "%s");\n' % reason

	#
	def get_self(self, ctx):
		return '1'  # always first arg

	def get_arg(self, i, ctx):
		i += 1  # Lua stack starts at 1
		if ctx in ['setter', 'method']:
			i += 1  # account for self in those methods
		return str(i)

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
		self._source += 'static const luaL_Reg %s_global_functions[] = {\n' % self._name
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
		self._source += '	// register type metatables\n'
		for t in self._bound_types:
			if isinstance(t, LuaClassTypeDefaultConverter):
				self._source += '	register_%s(L);\n' % t.bound_name
		self._source += '\n'
		self._source += '	// register global functions\n'
		self._source += '	lua_newtable(L);\n'
		self._source += '	luaL_setfuncs(L, %s_global_functions, 0);\n' % self._name
		self._source += '	return 1;\n'
		self._source += '}\n'
