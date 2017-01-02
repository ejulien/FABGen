import bind


def install(namespace = 'BindLua'):
	bind.reset_generator()
	bind.set_namespace(namespace)

	# templates for basic type exchange
	def check(funcname, type, info):
		return 'bool %s(lua_State *L, int idx)' % funcname

	def to_c(funcname, type, info):
		return 'void %s(lua_State *L, int idx, %s *val)' % (funcname, type)

	def from_c(funcname, type, info):
		return 'int %s(lua_State *L, %s *val)' % (funcname, type)

	bind.set_type_templates(check, to_c, from_c)

	# templates for function calls
	def arg_to_c(i, count, var, func):
		return '%s(L, %d, %s);' % (func, i, var)

	def rval_from_c(i, count, var, func):
		src = 'int rval_count = 0;\n' if i == 0 else ''
		src += 'rval_count += %s(L, %s);\n' % (func, var)
		if i == count - 1:
			src += 'return rval_count'
		return src

	def void_rval_from_c():
		return 'return 0;'

	bind.set_call_templates(arg_to_c, rval_from_c, void_rval_from_c)

	# templates for object type exchange
	bind.insert_source_code('''
// wrap a C object
template<typename NATIVE_OBJECT_WRAPPER_T> int _wrap_obj(lua_State *L, void *obj, const char *type)
{
	auto p = lua_newuserdata(L, sizeof(NATIVE_OBJECT_WRAPPER_T));
	if (!p)
		return 0;

	new (p) NATIVE_OBJECT_WRAPPER_T(obj, type);
	return 1;
}
	''')




#	bind.set_obj_templates(check_obj, obj_to_c, obj_from_c)




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
