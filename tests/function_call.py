def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
int get_int() { return 8; }

int get() { return 0; }
int get(int v) { return v / 2; }
int get(int v, int k) { return v * k; }
int get(int v, int k, int b) { return v * k + b; }
''', True, False)

	gen.bind_function('get_int', 'int', [])
	gen.bind_function_overloads('get', [('int', []), ('int', ['int v']), ('int', ['int v', 'int k']), ('int', ['int v', 'int k', 'int b'])])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

expect_eq(my_test.get_int(), 8)

# overload
expect_eq(my_test.get(), 0)
expect_eq(my_test.get(2), 1)
expect_eq(my_test.get(4, 3), 12)
expect_eq(my_test.get(4, 3, 2), 14)
'''
