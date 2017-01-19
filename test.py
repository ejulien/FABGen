import lua
import python


def run_test(gen):
	gen.start('test')

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_member(simple_struct, 'int a')
	gen.bind_method(simple_struct, 'set_a', 'bool', ['int v0', 'int v1'])
	gen.end_class(simple_struct)

	gen.finalize()

	header, source = gen.get_output()

	print(header)
	print(source)


#run_test(lua.LuaGenerator())
run_test(python.PythonGenerator())
