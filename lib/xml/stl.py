# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

import lang.xml


def bind_function_T(gen, type, bound_name=None):
	fn = gen.begin_class(type, bound_name=bound_name)
	gen.end_class(fn)

	# TODO call into gen to declare a callback type so we can document it

	return fn
