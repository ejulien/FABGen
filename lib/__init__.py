# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

def bind_defaults(gen):
	if gen.get_language() == 'CPython':
		import lib.cpython.std
		import lib.cpython.stl

		lib.cpython.std.bind_std(gen)
		lib.cpython.stl.bind_stl(gen)
	elif gen.get_language() == 'Lua':
		import lib.lua.std
		import lib.lua.stl

		lib.lua.std.bind_std(gen)
		lib.lua.stl.bind_stl(gen)
	elif gen.get_language() == 'Go':
		import lib.go.std
		import lib.go.stl

		lib.go.std.bind_std(gen)
		lib.go.stl.bind_stl(gen)
