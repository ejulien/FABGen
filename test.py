import lua
import python


def run_test(gen):
	gen.start("gs")

	gen.bind_function('add', 'int', ['int a', 'int'])
	gen.bind_function('set_name', 'void', ['const char *'])
	gen.bind_function('get_name', 'const char *', ['void'])

	gen.bind_function('add_by_ref', 'int', ['int &', 'int &'])
	gen.bind_function('add_by_ptr', 'int', ['int *', 'int *'])

	#lua.bind_class('simple_struct', None, None, None)

	header, source = gen.get_output()

	print(header)
	print(source)


#run_test(lua.LuaGenerator())
run_test(python.PythonGenerator())
