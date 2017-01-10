import lua
import python


def run_test(gen):
	gen.start('test', 'binding')

	gen.bind_function('add_basic_types', 'int', ['int a', 'int'])
	gen.bind_function('set_name_from_const_char_ptr', 'void', ['const char *'])
	gen.bind_function('get_name_as_const_char_ptr', 'const char *', ['void'])

	gen.bind_function('add_basic_types_by_ref', 'int', ['int &', 'int &'])
	gen.bind_function('add_basic_types_by_ptr', 'int', ['int *', 'int *'])

	gen.bind_function('return_basic_type_by_ptr', 'int *', [])

	gen.bind_function('ns::simple_call', 'void', [])

	gen.decl_function_template('add3', ['T0', 'T1'], 'T0', ['T0', 'int', 'T1'])
	gen.bind_function_template('add3', 'add3_float_float', ['float', 'float'])
	gen.bind_function_template('add3', 'add3_float_string', ['float', 'std::string *'])

	# gen.bind_class('simple_struct')
	#
	# gen.bind_function('return_simple_struct_by_value', 'simple_struct', [])
	# gen.bind_function('return_simple_struct_by_pointer', 'simple_struct*', [])
	# gen.bind_function('return_simple_struct_by_ref', 'simple_struct&', [])
	#
	# gen.bind_function('take_simple_struct_by_value', 'void', ['simple_struct'])
	# gen.bind_function('take_simple_struct_by_pointer', 'void', ['simple_struct*'])
	# gen.bind_function('take_simple_struct_by_ref', 'void', ['simple_struct&'])

	gen.finalize()

	header, source = gen.get_output()

	print(header)
	print(source)


#run_test(lua.LuaGenerator())
run_test(python.PythonGenerator())
