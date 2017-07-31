import lib.cpython.std
import lib.cpython.stl
import lang.cpython


def bind_all_defaults(gen):
	if gen.get_language() == 'CPython':
		lib.cpython.std.bind_std(gen)
		lib.cpython.stl.bind_stl(gen)
