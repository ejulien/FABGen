import lua
import python


def run_test(gen):
	gen.start("gs")

#	gen.bind_function('add_basic_types', 'int', ['int a', 'int'])
#	gen.bind_function('set_name_from_const_char_ptr', 'void', ['const char *'])
#	gen.bind_function('get_name_as_const_char_ptr', 'const char *', ['void'])

	gen.bind_function('add_basic_types_by_ref', 'int', ['int &', 'int &'])
	gen.bind_function('add_basic_types_by_ptr', 'int', ['int *', 'int *'])

	gen.bind_function('return_basic_type_by_ptr', 'int *', [])

	gen.bind_function('ns::simple_call', 'void', [])

	#lua.bind_class('simple_struct', None, None, None)

	header, source = gen.get_output()

	print(header)
	print(source)


run_test(lua.LuaGenerator())
#run_test(python.PythonGenerator())
