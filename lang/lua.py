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
class LuaClassTypeConverter(LuaTypeConverterCommon):
	def __init__(self, type, arg_storage_type=None, bound_name=None, rval_storage_type=None):
		super().__init__(type, arg_storage_type, bound_name, rval_storage_type)

	def get_type_glue(self, gen, module_name):
		out = ''

		# sequence feature support
		has_sequence = 'sequence' in self._features

		if has_sequence:
			out += '// sequence protocol for %s\n' % self.bound_name
			seq = self._features['sequence']

			# get_size
			out += 'static int __len_%s(lua_State *L) {\n' % self.bound_name
			out += gen._prepare_c_arg_self(self, '_self')
			out += '	lua_Integer size;\n'
			out += seq.get_size('_self', 'size')
			out += '	lua_pushinteger(L, size);\n'
			out += '	return 1;\n'
			out += '}\n\n'

			# get_item
			out += 'static int seq__index_%s(lua_State *L) {\n' % self.bound_name
			out += '	int rval_count = 0;\n'
			out += gen._prepare_c_arg_self(self, '_self')
			out += gen._prepare_c_arg(0, gen.get_conv('int'), 'idx', 'getter')
			out += gen.decl_var(seq.wrapped_conv.ctype, 'rval')
			out += '	bool error = false;\n'
			out += seq.get_item('_self', 'idx', 'rval', 'error')
			out += '''	if (error)
		return luaL_error(L, "invalid lookup");
'''
			out += gen.prepare_c_rval(seq.wrapped_conv, seq.wrapped_conv.ctype, 'rval')
			out += gen.commit_rvals(['rval'])
			out += '	return rval_count;\n'
			out += '}\n\n'

			# set_item
			out += 'static int seq__newindex_%s(lua_State *L) {\n' % self.bound_name
			out += '	if (!%s)\n' % seq.wrapped_conv.check_call('-1')
			out += '		return luaL_error(L, "invalid type in assignation, expected %s");\n' % seq.wrapped_conv.ctype
			out += gen._prepare_c_arg_self(self, '_self')
			out += gen._prepare_c_arg(0, gen.get_conv('int'), 'idx', 'setter')
			out += gen._prepare_c_arg(1, seq.wrapped_conv, 'cval', 'setter')
			out += '	bool error = false;\n'
			out += seq.set_item('_self', 'idx', 'cval', 'error')
			out += '''	if (error)
		return luaL_error(L, "invalid assignation");
'''
			out += '	return 0;\n'
			out += '}\n\n'

		# type metatable maps
		gen.add_include('map', True)
		gen.add_include('string', True)

		def build_index_map(name, values, filter, gen_output):
			out = 'std::map<std::string, int (*)(lua_State *)> %s = {' % name
			if len(values) > 0:
				entries = [gen_output(v) for v in values if filter(v)]
				out += '\n' + ',\n'.join(entries) + '\n'
			out += '};\n\n'
			return out

		out += build_index_map('__index_member_map_%s' % self.bound_name, self.get_all_members() + self.get_all_static_members(), lambda v: True, lambda v: '	{"%s", %s}' % (v['name'], v['getter']))
		out += build_index_map('__index_static_member_map_%s' % self.bound_name, self.get_all_static_members(), lambda v: True, lambda v: '	{"%s", %s}' % (v['name'], v['getter']))
		out += build_index_map('__index_method_map_%s' % self.bound_name, self.get_all_methods() + self.get_all_static_methods(), lambda v: True, lambda v: '	{"%s", %s}' % (v['bound_name'], v['proxy_name']))
		out += build_index_map('__index_static_method_map_%s' % self.bound_name, self.get_all_static_methods(), lambda v: True, lambda v: '	{"%s", %s}' % (v['bound_name'], v['proxy_name']))
		out += build_index_map('__newindex_member_map_%s' % self.bound_name, self.get_all_members() + self.get_all_static_members(), lambda v: v['setter'], lambda v: '	{"%s", %s}' % (v['name'], v['setter']))
		out += build_index_map('__newindex_static_member_map_%s' % self.bound_name, self.get_all_static_members(), lambda v: v['setter'], lambda v: '	{"%s", %s}' % (v['name'], v['setter']))

		# __index
		out += 'static int __index_%s_instance(lua_State *L) {\n' % self.bound_name

		if has_sequence:
			out += '''\
	if (lua_isinteger(L, -1)) {
		return seq__index_%s(L);
	}
\n''' % self.bound_name

		out += '''\
	if (lua_isstring(L, -1)) {
		std::string key = lua_tostring(L, -1);
		lua_pop(L, 1);

		auto i = __index_member_map_%s.find(key); // member lookup
		if (i != __index_member_map_%s.end())
			return i->second(L);

		i = __index_method_map_%s.find(key); // method lookup
		if (i != __index_method_map_%s.end()) {
			lua_pushcfunction(L, i->second);
			return 1;
		}
	}
	return 0; // lookup failed
}\n\n''' % (self.bound_name, self.bound_name, self.bound_name, self.bound_name)

		out += '''static int __index_%s_class(lua_State *L) {
	if (lua_isstring(L, -1)) {
		std::string key = lua_tostring(L, -1);
		lua_pop(L, 1);

		auto i = __index_static_member_map_%s.find(key); // member lookup
		if (i != __index_static_member_map_%s.end())
			return i->second(L);

		i = __index_static_method_map_%s.find(key); // method lookup
		if (i != __index_static_method_map_%s.end()) {
			lua_pushcfunction(L, i->second);
			return 1;
		}
	}
	return 0; // lookup failed
}\n\n''' % (self.bound_name, self.bound_name, self.bound_name, self.bound_name, self.bound_name)

		# __newindex
		out += 'static int __newindex_%s_instance(lua_State *L) {\n' % self.bound_name
		if has_sequence:
			out += '''\
	if (lua_isinteger(L, -2)) {
		return seq__newindex_%s(L);
	}
\n''' % self.bound_name

		out += '''\
	if (lua_isstring(L, -2)) {
		std::string key = lua_tostring(L, -2);
		lua_remove(L, -2);

		auto i = __newindex_member_map_%s.find(key);
		if (i != __newindex_member_map_%s.end())
			return i->second(L);
	}
	return 0; // lookup failed
}\n\n''' % (self.bound_name, self.bound_name)

		out += '''static int __newindex_%s_class(lua_State *L) {
	if (lua_isstring(L, -2)) {
		std::string key = lua_tostring(L, -2);
		lua_remove(L, -2);

		auto i = __newindex_static_member_map_%s.find(key);
		if (i != __newindex_static_member_map_%s.end())
			return i->second(L);
	}
	return 0; // lookup failed
}\n\n''' % (self.bound_name, self.bound_name, self.bound_name)

		# type class metatable
		out += 'static const luaL_Reg %s_class_meta[] = {\n' % self.bound_name
		out += '	{"__index", __index_%s_class},\n' % self.bound_name
		out += '	{"__newindex", __newindex_%s_class},\n' % self.bound_name
		if self.constructor:
			out += '	{"__call", %s},\n' % self.constructor['proxy_name']
		out += '	{NULL, NULL}};\n\n'

		# type instance metatable
		comp_op_to_metaevent = {'<': '__lt', '<=': '__le', '==': '__eq' }
		arit_op_to_metaevent = {'+': '__add', '-': '__sub', '*': '__mul', '/': '__div' }

		out += 'static const luaL_Reg %s_instance_meta[] = {\n' % self.bound_name
		out += '	{"__gc", wrapped_Object_gc},\n'
		out += '	{"__index", __index_%s_instance},\n' % self.bound_name
		out += '	{"__newindex", __newindex_%s_instance},\n' % self.bound_name
		for i, ops in enumerate(self.comparison_ops):
			if ops['op'] in comp_op_to_metaevent:
				out += '	{"%s", %s},\n' % (comp_op_to_metaevent[ops['op']], ops['proxy_name'])
		for i, ops in enumerate(self.arithmetic_ops):
			if ops['op'] in arit_op_to_metaevent:
				out += '	{"%s", %s},\n' % (arit_op_to_metaevent[ops['op']], ops['proxy_name'])
		if has_sequence:
			out += '	{"__len", __len_%s},\n' % self.bound_name
		out += '	{NULL, NULL}};\n\n'

		# type registration
		out += '''void register_%s(lua_State *L) {
	// setup class object
	lua_newtable(L); // class object
	lua_newtable(L); // class metatable
	luaL_setfuncs(L, %s_class_meta, 0);
	lua_setmetatable(L, -2);
	lua_setfield(L, -2, "%s");

	// setup type instance metatable
	luaL_newmetatable(L, "%s");
	luaL_setfuncs(L, %s_instance_meta, 0);
	lua_pop(L, 1);
}\n\n''' % (self.bound_name, self.bound_name, self.bound_name, self.bound_name, self.bound_name)

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
class LuaPtrTypeConverter(LuaTypeConverterCommon):
	def get_type_glue(self, gen, module_name):
		out = '''bool check_%s(lua_State *L, int idx) {
	if (lua_isinteger(L, idx))
		return true;
	if (wrapped_Object *w = cast_to_wrapped_Object_safe(L, idx))
		return _type_tag_can_cast(w->type_tag, %s);
	return false;
}\n''' % (self.bound_name, self.type_tag)

		out += '''void to_c_%s(lua_State *L, int idx, void *obj) {
	if (lua_isinteger(L, idx)) {
		*((%s*)obj) = (%s)lua_tointeger(L, idx);
	} else if (wrapped_Object *w = cast_to_wrapped_Object_unsafe(L, idx)) {
		*(void **)obj = _type_tag_cast(w->obj, w->type_tag, %s);
	}
}\n''' % (self.bound_name, self.ctype, self.ctype, self.type_tag)

		out += 'int from_c_%s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushinteger(L, (lua_Integer)*((%s*)obj)); return 1; }\n' % (self.bound_name, self.ctype)
		return out


#
class LuaGenerator(gen.FABGen):
	default_ptr_converter = LuaPtrTypeConverter
	default_class_converter = LuaClassTypeConverter

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
		if ctx in ['getter', 'setter', 'method', 'arithmetic_op', 'comparison_op']:
			i += 1  # account for self in those methods
		return str(i)

	def open_proxy(self, name, max_arg_count, ctx):
		out = 'static int %s(lua_State *L) {\n' % name
		if ctx in ['method']:
			out += '	int arg_count = lua_gettop(L) - 1, rval_count = 0;\n\n'
		else:
			if ctx == 'constructor':
				out += '	lua_remove(L, 1);\n'  # remove func from the stack (as passed in by the __call metamethod)
			out += '	int arg_count = lua_gettop(L), rval_count = 0;\n\n'
		return out

	def close_proxy(self, ctx):
		return '	return rval_count;\n}\n'

	def proxy_call_error(self, msg, ctx):
		return self.set_error('runtime', msg)

	# function call return values
	def return_void_from_c(self):
		return 'return 0;'

	def rval_from_c_ptr(self, conv, out_var, expr, ownership):
		return 'rval_count += ' + conv.from_c_call(out_var, expr, ownership)

	def commit_rvals(self, rvals, ctx='default'):
		return ''  #'return rval_count;\n'

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

		self._source += '''static void declare_enum_value(lua_State *L, int idx, const char *name, int value) {
	lua_pushinteger(L, value);
	lua_setfield(L, idx, name);
}\n\n'''

		self._source += 'extern "C" _DLL_EXPORT_ int luaopen_%s(lua_State* L) {\n' % self._name

		self._source += '	// custom initialization code'
		self._source += self._custom_init_code

		self._source += '	// new module table\n'
		self._source += '	lua_newtable(L);\n'
		self._source += '\n'

		if len(self._enums) > 0:
			for name, enum in self._enums.items():
				self._source += '	// enumeration %s\n' % name
				for name, value in enum.items():
					self._source += '	declare_enum_value(L, -2, "%s", (int)%s);\n' % (name, value)
			self._source += '\n'

		types_to_register = [t for t in self._bound_types if isinstance(t, LuaClassTypeConverter)]

		if len(types_to_register) > 0:
			self._source += '	// register types\n'
			for t in types_to_register:
				self._source += '	register_%s(L);\n' % t.bound_name
			self._source += '\n'

		self._source += '	// register global functions\n'
		self._source += '	luaL_setfuncs(L, %s_global_functions, 0);\n' % self._name

		self._source += '	return 1;\n'
		self._source += '}\n'
