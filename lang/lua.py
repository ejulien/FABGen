# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

import gen


#
class LuaTypeConverterCommon(gen.TypeConverter):
	def get_type_api(self, module_name):
		out = '// type API for %s\n' % self.ctype
		if self.c_storage_class:
			out += 'struct %s;\n' % self.c_storage_class
		out += 'bool %s(lua_State *L, int idx);\n' % self.check_func
		if self.c_storage_class:
			out += 'void %s(lua_State *L, int idx, void *obj, %s &storage);\n' % (self.to_c_func, self.c_storage_class)
		else:
			out += 'void %s(lua_State *L, int idx, void *obj);\n' % self.to_c_func
		out += 'int %s(lua_State *L, void *obj, OwnershipPolicy);\n' % self.from_c_func
		out += '\n'
		return out

	def to_c_call(self, in_var, out_var_p):
		out = ''
		if self.c_storage_class:
			c_storage_var = 'storage_%s' % out_var_p.replace('&', '_')
			out += '%s %s;\n' % (self.c_storage_class, c_storage_var)
			out += '%s(L, %s, (void *)%s, %s);\n' % (self.to_c_func, in_var, out_var_p, c_storage_var)
		else:
			out += '%s(L, %s, %s);\n' % (self.to_c_func, in_var, out_var_p)
		return out

	def from_c_call(self, out_var, expr, ownership):
		return "%s(L, (void *)%s, %s);\n" % (self.from_c_func, expr, ownership)

	def check_call(self, in_var):
		return "%s(L, %s)" % (self.check_func, in_var)


#
def build_index_map(name, values, filter, gen_output):
	out = 'static std::map<std::string, int (*)(lua_State *)> %s = {' % name
	if len(values) > 0:
		entries = [gen_output(v) for v in values if filter(v)]
		out += '\n' + ',\n'.join(entries) + '\n'
	out += '};\n\n'
	return out


#
class LuaClassTypeConverter(LuaTypeConverterCommon):
	def is_type_class(self):
		return True

	def get_type_glue(self, gen, module_name):
		out = ''

		# sequence feature support
		has_sequence = 'sequence' in self._features

		if has_sequence:
			out += '// sequence protocol for %s\n' % self.bound_name
			seq = self._features['sequence']

			# get_size
			out += 'static int __len_%s(lua_State *L) {\n' % self.bound_name
			out += gen._prepare_to_c_self(self, '_self')
			out += '	lua_Integer size;\n'
			out += seq.get_size('_self', 'size')
			out += '	lua_pushinteger(L, size);\n'
			out += '	return 1;\n'
			out += '}\n\n'

			# get_item
			out += 'static int seq__index_%s(lua_State *L) {\n' % self.bound_name
			out += '	int rval_count = 0;\n'
			out += gen._prepare_to_c_self(self, '_self')
			out += gen.prepare_to_c_var(0, gen.get_conv('int'), 'idx', 'getter')
			out += gen.decl_var(seq.wrapped_conv.ctype, 'rval')
			out += '	bool error = false;\n'
			out += seq.get_item('_self', 'idx-1', 'rval', 'error')  # Lua index starts at 1
			out += '''	if (error)
		return luaL_error(L, "invalid lookup");
'''
			out += gen.prepare_from_c_var({'conv': seq.wrapped_conv, 'ctype': seq.wrapped_conv.ctype, 'var': 'rval', 'is_arg_in_out': False, 'ownership': None})
			out += gen.commit_from_c_vars(['rval'])
			out += '	return rval_count;\n'
			out += '}\n\n'

			# set_item
			out += 'static int seq__newindex_%s(lua_State *L) {\n' % self.bound_name
			out += '	if (!%s)\n' % seq.wrapped_conv.check_call('-1')
			out += '		return luaL_error(L, "invalid type in assignation, expected %s");\n' % seq.wrapped_conv.ctype
			out += gen._prepare_to_c_self(self, '_self')
			out += gen.prepare_to_c_var(0, gen.get_conv('int'), 'idx', 'setter')
			out += gen.prepare_to_c_var(1, seq.wrapped_conv, 'cval', 'setter')
			out += '	bool error = false;\n'
			out += seq.set_item('_self', 'idx-1', 'cval', 'error')  # Lua index starts at 1
			out += '''	if (error)
		return luaL_error(L, "invalid assignation");
'''
			out += '	return 0;\n'
			out += '}\n\n'

		# type metatable maps
		gen.add_include('map', True)
		gen.add_include('string', True)

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

		# type default comparison operator
		out += '''\
static int __default_Lua_eq_%s(lua_State *L) {
	wrapped_Object *w1 = cast_to_wrapped_Object_safe(L, -2);
	wrapped_Object *w2 = cast_to_wrapped_Object_safe(L, -1);

	lua_pop(L, 2);

	if (!w1 || !w2 || w1->type_tag != w2->type_tag) {
		lua_pushboolean(L, 0);
		return 1;
	}
''' % self.bound_name

		if self._supports_deep_compare:
			out += '''
	if (!(*(%s *)w1->obj == *(%s *)w2->obj)) {
		lua_pushboolean(L, 0);
		return 1;
	}
''' % (self.ctype, self.ctype)
		else:
			out += '''
	if (!(w1->obj == w2->obj)) {
		lua_pushboolean(L, 0);
		return 1;
	}
'''

		out += '''
	lua_pushboolean(L, 1);
	return 1;
}
'''

		# Visual Code debugger userdata inspection
		debug_members = self.get_all_members()  # + self.get_all_static_members()
		has___debugger_extand = len(debug_members) > 0

		if has___debugger_extand:
			out += '\
static int __debugger_extand_%s_class(lua_State *L) {\n' % self.bound_name
			out += gen._prepare_to_c_self(self, 'obj', 'getter', self._features)

			out += '\n	lua_newtable(L);\n'

			out += '\n	// dict\n'
			for i, member in enumerate(debug_members):
				out += '	lua_pushstring(L, "%s");\n' % member['name']
				out += '	lua_seti(L, -2, %d);\n' % (i + 1)

			out += '\n	// values\n'
			for i, member in enumerate(debug_members):
				if member['is_bitfield']:
					out += '	lua_pushinteger(L, obj->%s);\n' % (member['name'])
				else:
					conv = gen.select_ctype_conv(member['ctype'])
					if isinstance(conv, LuaClassTypeConverter):
						continue  # FIXME I cannot get this to work with the Lua debugger API...
					out += '	' + conv.from_c_call(-1, '&obj->%s' % member['name'], 'NonOwning')
				out += '	lua_setfield(L, -2, "%s");\n' % member['name']

			out += '''\
	return 1;
}\n\n'''

		# type instance metatable
		comp_op_to_metaevent = {'<': '__lt', '<=': '__le', '==': '__eq' }
		arit_op_to_metaevent = {'+': '__add', '-': '__sub', '*': '__mul', '/': '__div' }

		out += 'static const luaL_Reg %s_instance_meta[] = {\n' % self.bound_name
		out += '	{"__gc", wrapped_Object_gc},\n'
		out += '	{"__index", __index_%s_instance},\n' % self.bound_name
		out += '	{"__newindex", __newindex_%s_instance},\n' % self.bound_name

		if has___debugger_extand:
			out += '	{"__debugger_extand", __debugger_extand_%s_class},\n' % self.bound_name  # support for Visual Code Lua Debugger userdata inspection

		has_eq_op = False
		for i, ops in enumerate(self.comparison_ops):
			if ops['op'] == '==':
				has_eq_op = True
			if ops['op'] in comp_op_to_metaevent:
				out += '	{"%s", %s},\n' % (comp_op_to_metaevent[ops['op']], ops['proxy_name'])

		if not has_eq_op:
			out += '	{"__eq", __default_Lua_eq_%s},\n' % self.bound_name

		for i, ops in enumerate(self.arithmetic_ops):
			if ops['op'] in arit_op_to_metaevent:
				out += '	{"%s", %s},\n' % (arit_op_to_metaevent[ops['op']], ops['proxy_name'])

		if has_sequence:
			out += '	{"__len", __len_%s},\n' % self.bound_name

		out += '	{NULL, NULL}};\n\n'

		# type registration
		out += 'static void register_%s(lua_State *L) {\n' % self.bound_name
		if self._inline:
			out += '	assert(sizeof(%s) <= 16);\n\n' % self.ctype
		out += '''\
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
}\n\n''' % (self.bound_name, self.bound_name, self.bound_name, self.bound_name)

		# delete delegates
		out += 'static void delete_%s(void *o) { delete (%s *)o; }\n\n' % (self.bound_name, self.ctype)

		# check
		out += '''bool %s(lua_State *L, int idx) {
	wrapped_Object *w = cast_to_wrapped_Object_safe(L, idx);
	if (!w)
		return false;
	return _type_tag_can_cast(w->type_tag, %s);
}\n''' % (self.check_func, self.type_tag)

		# to C
		out += '''void %s(lua_State *L, int idx, void *obj) {
	wrapped_Object *w = cast_to_wrapped_Object_unsafe(L, idx);
	*(void **)obj = _type_tag_cast(w->obj, w->type_tag, %s);
}\n''' % (self.to_c_func, self.type_tag)

		# from C
		is_inline = False

		if self._non_copyable:
			if self._moveable:
				copy_code = 'obj = new %s(std::move(*(%s *)obj));' % (self.ctype, self.ctype)
			else:
				copy_code = 'return luaL_error(L, "type %s is non-copyable and non-moveable");' % self.bound_name
		else:
			if self._inline:
				is_inline = True
				copy_code = 'obj = new((void *)w->inline_obj) %s(*(%s *)obj);' % (self.ctype, self.ctype)
			else:
				copy_code = 'obj = new %s(*(%s *)obj);' % (self.ctype, self.ctype)

		if is_inline:
			delete_code = 'w->on_delete = &delete_inline_%s;' % self.bound_name
		else:
			delete_code = 'w->on_delete = &delete_%s;' % self.bound_name

		if is_inline:
			out += '''
static void delete_inline_%s(void *o) {
	using T = %s;
	((T*)o)->~T();
}\n\n''' % (self.bound_name, self.ctype)

		out += '''int %s(lua_State *L, void *obj, OwnershipPolicy own) {
	wrapped_Object *w = (wrapped_Object *)lua_newuserdata(L, sizeof(wrapped_Object));
	if (own == Copy)
		%s
	init_wrapped_Object(w, %s, obj);
	if (own != NonOwning)
		%s
	luaL_setmetatable(L, "%s");
	return 1;
}
\n''' % (self.from_c_func, copy_code, self.type_tag, delete_code, self.bound_name)

		return out

	def finalize_type(self):
		out = ''
		return out


#
class LuaPtrTypeConverter(LuaTypeConverterCommon):
	def get_type_glue(self, gen, module_name):
		out = '''bool %s(lua_State *L, int idx) {
	if (lua_isinteger(L, idx))
		return true;
	if (wrapped_Object *w = cast_to_wrapped_Object_safe(L, idx))
		return _type_tag_can_cast(w->type_tag, %s);
	return false;
}\n''' % (self.check_func, self.type_tag)

		out += '''void %s(lua_State *L, int idx, void *obj) {
	if (lua_isinteger(L, idx)) {
		*((%s*)obj) = (%s)lua_tointeger(L, idx);
	} else if (wrapped_Object *w = cast_to_wrapped_Object_unsafe(L, idx)) {
		*(void **)obj = _type_tag_cast(w->obj, w->type_tag, %s);
	}
}\n''' % (self.to_c_func, self.ctype, self.ctype, self.type_tag)

		out += 'int %s(lua_State *L, void *obj, OwnershipPolicy) { lua_pushinteger(L, (lua_Integer)*((%s*)obj)); return 1; }\n' % (self.from_c_func, self.ctype)
		return out


#
class LuaExternTypeConverter(LuaTypeConverterCommon):
	def __init__(self, type, to_c_storage_type, bound_name, module):
		super().__init__(type, to_c_storage_type, bound_name)
		self.module = module

	def get_type_api(self, module_name):
		return ''

	def to_c_call(self, in_var, out_var_p):
		out = ''
		if self.c_storage_class:
			c_storage_var = 'storage_%s' % out_var_p.replace('&', '_')
			out += '%s %s;\n' % (self.c_storage_class, c_storage_var)
			out += '(*%s)(L, %s, (void *)%s, %s);\n' % (self.to_c_func, in_var, out_var_p, c_storage_var)
		else:
			out += '(*%s)(L, %s, %s);\n' % (self.to_c_func, in_var, out_var_p)
		return out

	def from_c_call(self, out_var, expr, ownership):
		return "(*%s)(L, (void *)%s, %s);\n" % (self.from_c_func, expr, ownership)

	def check_call(self, in_var):
		return "(*%s)(L, %s)" % (self.check_func, in_var)

	def get_type_glue(self, gen, module_name):
		out = '// extern type API for %s\n' % self.ctype
		if self.c_storage_class:
			out += 'struct %s;\n' % self.c_storage_class
		out += 'bool (*%s)(lua_State *L, int idx) = nullptr;\n' % self.check_func
		if self.c_storage_class:
			out += 'void (*%s)(lua_State *L, int idx, void *obj, %s &storage) = nullptr;\n' % (self.to_c_func, self.c_storage_class)
		else:
			out += 'void (*%s)(lua_State *L, int idx, void *obj) = nullptr;\n' % self.to_c_func
		out += 'int (*%s)(lua_State *L, void *obj, OwnershipPolicy) = nullptr;\n' % self.from_c_func
		out += '\n'
		return out


#
class LuaGenerator(gen.FABGen):
	default_ptr_converter = LuaPtrTypeConverter
	default_class_converter = LuaClassTypeConverter
	default_extern_converter = LuaExternTypeConverter

	def __init__(self):
		super().__init__()
		self.check_self_type_in_ops = True

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

		self._header += 'struct lua_State;\n\n'

		self._source += '''\
typedef struct {
	uint32_t magic_u32; // wrapped_Object marker
	uint32_t type_tag; // wrapped pointer type tag

	void *obj;
	char inline_obj[16]; // storage for inline objects

	void (*on_delete)(void *);
} wrapped_Object;

static void init_wrapped_Object(wrapped_Object *o, uint32_t type_tag, void *obj) {
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

		self._source += '''
// helper class to store a reference to an Lua value on the stack
class LuaValueRef {
public:
	LuaValueRef(lua_State *_L, int idx) : L(_L) {
		lua_pushvalue(L, idx);
		ref = luaL_ref(L, LUA_REGISTRYINDEX);
	}
	~LuaValueRef() {
		if (ref != LUA_NOREF)
			luaL_unref(L, LUA_REGISTRYINDEX, ref);
	}

	void Push() const { lua_rawgeti(L, LUA_REGISTRYINDEX, ref); }

private:
	lua_State *L{nullptr};
	int ref{LUA_NOREF};
};
\n'''

		self._source += self.get_binding_api_declaration()
		self._header += self.get_binding_api_declaration()

	#
	def set_error(self, type, reason):
		return 'return luaL_error(L, "%s");\n' % reason

	#
	def get_self(self, ctx):
		return '1'  # always first arg

	def get_var(self, i, ctx):
		i += 1  # Lua stack starts at 1
		if ctx in ['getter', 'setter', 'method', 'arithmetic_op', 'comparison_op']:
			i += 1  # account for self in those methods
		if ctx == 'rbind_rval':
			i = -1  # return value for a reverse binding call
		return str(i)

	#
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

	def rval_from_nullptr(self, out_var):
		return 'lua_pushnil(L);\n++rval_count;\n'

	def rval_from_c_ptr(self, conv, out_var, expr, ownership):
		return 'rval_count += ' + conv.from_c_call(out_var, expr, ownership)

	def commit_from_c_vars(self, rvals, ctx='default'):
		return ''  #'return rval_count;\n'

	def rval_assign_arg_in_out(self, out_var, arg_in_out):
		out = 'lua_pushvalue(L, %s);\n' % arg_in_out
		out += 'rval_count += 1;\n'
		return out

	# reverse binding support
	def _get_rbind_call_custom_args(self):
		return 'lua_State *L, int idx'

	def _prepare_rbind_call(self, rval, args):
		return '''\
int rval_count = 0;

if (idx != -1) {
	lua_pushvalue(L, idx);
	if (idx < 0)
		--idx;
	lua_remove(L, idx);
}

'''

	def _rbind_call(self, rval, args, success_var):
		if rval == 'void':
			return '%s = lua_pcall(L, rval_count, 0, 0) == LUA_OK;\n' % success_var
		return '%s = lua_pcall(L, rval_count, 1, 0) == LUA_OK;\n' % success_var

	def _clean_rbind_call(self, rval, args):
		if rval == 'void':
			return ''
		return 'lua_pop(L, 1);\n'

	#
	def get_binding_api_declaration(self):
		type_info_name = gen.apply_api_prefix('type_info')

		out = '''\
struct %s {
	uint32_t type_tag;
	const char *c_type;
	const char *bound_name;

	bool (*check)(lua_State *L, int index);
	void (*to_c)(lua_State *L, int index, void *out);
	int (*from_c)(lua_State *L, void *obj, OwnershipPolicy policy);
};\n
''' % type_info_name

		out += '// return a type info from its type tag\n'
		out += '%s *%s(uint32_t type_tag);\n' % (type_info_name, gen.apply_api_prefix('get_bound_type_info'))

		out += '// return a type info from its type name\n'
		out += '%s *%s(const char *type);\n' % (type_info_name, gen.apply_api_prefix('get_c_type_info'))

		out += '// returns the typetag of a userdata object on the stack, nullptr if not a Fabgen object\n'
		out += 'uint32_t %s(lua_State *L, int idx);\n\n' % gen.apply_api_prefix('get_wrapped_object_type_tag')

		return out

	def output_binding_api(self):
		type_info_name = gen.apply_api_prefix('type_info')

		self._source += '// Note: Types using a storage class for conversion are not listed here.\n'
		self._source += 'static std::map<uint32_t, %s> __type_tag_infos;\n\n' % type_info_name

		self._source += 'static void __initialize_type_tag_infos() {\n'
		for type in self._bound_types:
			if not type.c_storage_class:
				self._source += '	__type_tag_infos[%s] = {%s, "%s", "%s", %s, %s, %s};\n' % (type.type_tag, type.type_tag, str(type.ctype), type.bound_name, type.check_func, type.to_c_func, type.from_c_func)
		self._source += '};\n\n'

		self._source += '''\
%s *%s(uint32_t type_tag) {
	auto i = __type_tag_infos.find(type_tag);
	return i == __type_tag_infos.end() ? nullptr : &i->second;
}\n\n''' % (type_info_name, gen.apply_api_prefix('get_bound_type_info'))

		self._source += 'static std::map<std::string, %s> __type_infos;\n\n' % type_info_name

		self._source += 'static void __initialize_type_infos() {\n'
		for type in self._bound_types:
			if not type.c_storage_class:
				self._source += '	__type_infos["%s"] = {%s, "%s", "%s", %s, %s, %s};\n' % (str(type.ctype), type.type_tag, str(type.ctype), type.bound_name, type.check_func, type.to_c_func, type.from_c_func)
		self._source += '};\n\n'

		self._source += '''
%s *%s(const char *type) {
	auto i = __type_infos.find(type);
	return i == __type_infos.end() ? nullptr : &i->second;
}\n\n''' % (type_info_name, gen.apply_api_prefix('get_c_type_info'))

		self._source += '''\
uint32_t %s(lua_State *L, int idx) {
	auto o = cast_to_wrapped_Object_safe(L, idx);
	return o ? o->type_tag : 0;
}\n\n''' % gen.apply_api_prefix('get_wrapped_object_type_tag')

	def output_module_free(self):
		self._source += 'static int __gc_%s(lua_State *L) {\n' % self._name
		self._source += '	// custom free code\n'
		self._source += self._custom_free_code
		self._source += '   return 0;\n'
		self._source += '}\n\n'

	def finalize(self):
		super().finalize()

		self.output_binding_api()

		# output module functions table
		self._source += 'static const luaL_Reg %s_global_functions[] = {\n' % self._name
		for f in self._bound_functions:
			self._source += '	{"%s", %s},\n' % (f['bound_name'], f['proxy_name'])
		self._source += '	{NULL, NULL}};\n\n'

		# registration function
		self._source += '''\
#if WIN32
 #define _DLL_EXPORT_ __declspec(dllexport)
#else
 #define _DLL_EXPORT_
#endif
\n'''

		self._source += '''static void declare_enum_value(lua_State *L, int idx, const char *name, int value) {
	lua_pushinteger(L, value);
	lua_setfield(L, idx, name);
}\n\n'''

		# variable lookup map
		self._source += build_index_map('__index_%s_var_map' % self._name, self._bound_variables, lambda v: True, lambda v: '	{"%s", %s}' % (v['bound_name'], v['getter']))
		self._source += build_index_map('__newindex_%s_var_map' % self._name, self._bound_variables, lambda v: v['setter'], lambda v: '	{"%s", %s}' % (v['bound_name'], v['setter']))

		self._source += '''\
static int __index_%s_var(lua_State *L) {
	if (lua_isstring(L, -1)) {
		std::string key = lua_tostring(L, -1);
		lua_pop(L, 1);

		auto i = __index_%s_var_map.find(key); // variable lookup
		if (i != __index_%s_var_map.end())
			return i->second(L);
	}
	return 0; // lookup failed
}\n\n''' % (self._name, self._name, self._name)

		self._source += '''\
static int __newindex_%s_var(lua_State *L) {
	if (lua_isstring(L, -2)) {
		std::string key = lua_tostring(L, -2);
		lua_remove(L, -2);

		auto i = __newindex_%s_var_map.find(key);
		if (i != __newindex_%s_var_map.end())
			return i->second(L);
	}
	return 0; // lookup failed
}\n\n''' % (self._name, self._name, self._name)

		self.output_module_free()

		self._source += '''\
static const luaL_Reg %s_module_meta[] = {
	{"__gc", __gc_%s},
	{"__index", __index_%s_var},
	{"__newindex", __newindex_%s_var},
	{NULL, NULL}
};\n\n''' % (self._name, self._name, self._name, self._name)

		#
		if self.embedded:  # pragma: no cover
			create_module_func = gen.apply_api_prefix('create_%s' % self._name)
			bind_module_func = gen.apply_api_prefix('bind_%s' % self._name)

			self._header += '// create the module object and push it onto the stack\n'
			self._header += 'int %s(lua_State *L);\n' % create_module_func
			self._header += '// create the module object and register it into the interpreter global table\n'
			self._header += 'bool %s(lua_State *L, const char *symbol);\n\n' % bind_module_func

			self._source += 'int %s(lua_State *L) {\n' % create_module_func
		else:
			self._source += 'extern "C" _DLL_EXPORT_ int luaopen_%s(lua_State *L) {\n' % self._name

		self._source += '	// initialize type info structures\n'
		self._source += '	__initialize_type_tag_infos();\n'
		self._source += '	__initialize_type_infos();\n'
		self._source += '\n'

		self._source += '	// custom initialization code\n'
		self._source += self._custom_init_code
		self._source += '\n'

		# create the module table
		self._source += '	// new module table\n'
		self._source += '	lua_newtable(L);\n'
		self._source += '\n'

		# enums
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
		self._source += '\n'

		# module metatable
		self._source += '	// setup module metatable\n'
		self._source += '	lua_newtable(L);\n'
		self._source += '	luaL_setfuncs(L, %s_module_meta, 0);\n' % self._name
		self._source += '	lua_setmetatable(L, -2);\n'

		self._source += '	return 1;\n'
		self._source += '}\n\n'

		#
		if self.embedded:  # pragma: no cover
			self._source += '''\
bool %s(lua_State *L, const char *symbol) {
	if (%s(L) != 1)
		return false;
	lua_setglobal(L, symbol);
	return true;
}\n
''' % (bind_module_func, create_module_func)
