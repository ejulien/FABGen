import bind


def install(namespace = 'BindLua'):
	bind.reset_generator()
	bind.set_namespace(namespace)

	# templates for basic type exchange
	def check_proto(funcname, type, info):
		return 'bool %s(lua_State *L, int idx)' % funcname

	def to_c_proto(funcname, type, info):
		return 'void %s(lua_State *L, int idx, %s *obj)' % (funcname, type)

	def from_c_proto(funcname, type, info):
		return 'int %s(lua_State *L, %s *obj, OwnershipPolicy own_policy)' % (funcname, type)

	bind.set_proto_templates(check_proto, to_c_proto, from_c_proto)

	# templates for function calls
	def arg_to_c(i, to_c, out_var_ptr):
		return '%s(L, %d, %s);' % (to_c, i, out_var_ptr)

	def rval_from_c(i, count, var, func, own_policy):
		src = 'int rval_count = 0;\n' if i == 0 else ''
		src += 'rval_count += %s(L, %s, %s);\n' % (func, var, own_policy)
		if i == count - 1:
			src += 'return rval_count'
		return src

	def void_rval_from_c():
		return 'return 0;'

	bind.set_call_templates(arg_to_c, rval_from_c, void_rval_from_c)

	# templates for class type exchange
	bind.insert_source_code('''
// wrap a C object
template<typename NATIVE_OBJECT_WRAPPER_T> int _wrap_obj(lua_State *L, void *obj, const char *type_tag)
{
	auto p = lua_newuserdata(L, sizeof(NATIVE_OBJECT_WRAPPER_T));
	if (!p)
		return 0;

	new (p) NATIVE_OBJECT_WRAPPER_T(obj, type_tag);
	return 1;
}
''')

	def class_check(type, info):
		return '''
	auto p = lua_touserdata(L, idx);
	if (!p)
		return false;

	auto w = reinterpret_cast<NativeObjectWrapper *>(p);
	return w->IsNativeObjectWrapper() && w->GetTypeTag() == %s;
''' % info['type_tag']

	def class_to_c(type, info):
		return '''
	auto p = lua_touserdata(L, idx);
	auto w = reinterpret_cast<NativeObjectWrapper *>(p);
	*val = reinterpret_cast<%s>(w->GetObj());
''' % type

	def class_from_c(type, info):
		return '''
	switch (own_policy) {
		default:
		case NonOwning:
			return _wrap_obj<NativeObjectPtrWrapper<%s>>(L, obj, %s);
		case ByValue:
			return _wrap_obj<NativeObjectValueWrapper<%s>>(L, obj, %s);
		case ByAddress:
			return _wrap_obj<NativeObjectUniquePtrWrapper<%s>>(L, obj, %s);
	}
	return 0;
''' % (type, info['type_tag'], type, info['type_tag'], type, info['type_tag'])

	bind.set_class_templates(class_check, class_to_c, class_from_c)

	# bind basic types
	bind.bind_type('int',
		"return lua_isnumber(L, idx) ? true : false;",
		"*val = lua_tonumber(L, idx);",
		"lua_pushinteger(L, *val); return 1;"
	)

	bind.bind_type('float',
		"return lua_isnumber(L, idx) ? true : false;",
		"*val = float(lua_tonumber(L, idx));",
		"lua_pushnumber(L, *val); return 1;"
	)

	bind.bind_type('std::string',
		"return lua_isstring(L, idx) ? true : false;",
		"*val = lua_tostring(L, idx);",
		"lua_pushstring(L, val->c_str()); return 1;"
	)

	bind.bind_type('const char *',
		"return lua_isstring(L, idx) ? true : false;",
		"*val = lua_tostring(L, idx);",
		"lua_pushstring(L, *val); return 1;"
	)
