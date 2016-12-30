import bind


def arg_to_c(i, count, var, func):
	return '%s(L, %d, %s);' % (func, i, var)


def rval_from_c(i, count, var, func):
	src = 'int rval_count = 0;\n' if i == 0 else ''
	src += 'rval_count += %s(L, %s);\n' % (func, var)
	if i == count - 1:
		src += 'return rval_count'
	return src


def install(namespace = 'BindLua'):
	bind.reset_generator()
	bind.set_namespace(namespace)

	#
	bind.set_templates({
		'check': "bool $name(lua_State *L, int idx)",
		'to_c': "void $name(lua_State *L, int idx, $type *val)",
		'from_c': "int $name(lua_State *L, $type *val)",

		'arg_to_c': arg_to_c,
		'rval_from_c': rval_from_c,
		'void_rval_from_c': 'return 0;'
	})

	#
	bind.register_type('int', {
		'check': "return lua_isnumber(L, idx) ? true : false;",
		'to_c': "*val = lua_tonumber(L, idx);",
		'from_c': "lua_pushinteger(L, *val); return 1;"
	})

	bind.register_type('float', {
		'check': "return lua_isnumber(L, idx) ? true : false;",
		'to_c': "*val = float(lua_tonumber(L, idx));",
		'from_c': "lua_pushnumber(L, *val); return 1;"
	})

	bind.register_type('std::string', {
		'check': "return lua_isstring(L, idx) ? true : false;",
		'to_c': "*val = lua_tostring(L, idx);",
		'from_c': "lua_pushstring(L, val->c_str()); return 1;"
	})

	bind.register_type('const char *', {
		'check': "return lua_isstring(L, idx) ? true : false;",
		'to_c': "*val = lua_tostring(L, idx);",
		'from_c': "lua_pushstring(L, *val); return 1;"
	})
