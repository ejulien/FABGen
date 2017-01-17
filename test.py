import lua
import python


def run_test(gen):
	gen.start('test')
	gen.bind_class('simple_struct', ['int a', 'float b', 'bool c'])
	gen.finalize()

	header, source = gen.get_output()

	print(header)
	print(source)


#run_test(lua.LuaGenerator())
run_test(python.PythonGenerator())
