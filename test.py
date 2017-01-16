import lua
import python


def run_test(gen):
	gen.start('test')

	gen.bind_class('simple_struct')

	gen.bind_function('return_simple_struct_by_value', 'simple_struct', [])
	gen.bind_function('return_simple_struct_by_pointer', 'simple_struct*', [])
	gen.bind_function('return_simple_struct_by_ref', 'simple_struct&', [])

	gen.bind_function('take_simple_struct_by_value', 'void', ['simple_struct'])
	gen.bind_function('take_simple_struct_by_pointer', 'void', ['simple_struct*'])
	gen.bind_function('take_simple_struct_by_ref', 'void', ['simple_struct&'])

	gen.bind_function('test_simple_struct', 'bool', [])

	gen.finalize()

	header, source = gen.get_output()

	print(header)
	print(source)


#run_test(lua.LuaGenerator())
run_test(python.PythonGenerator())
