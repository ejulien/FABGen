def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
template <typename T> T get() { return 8; }
''', True, False)

	gen.decl_function_template('get', ['T'], 'T', [])
	gen.bind_function_template('get', 'get_int', ['int'])
	gen.bind_function_template('get', 'get_float', ['float'])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

expect_eq(my_test.get_int(), 8)
expect_eq(my_test.get_float(), 8)
'''
