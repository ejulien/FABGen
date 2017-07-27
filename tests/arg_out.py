def bind_test(gen):
	gen.start('my_test')

	gen.insert_code('void out_values_function_call(int &a, int d, int *b, float k) { a = 8 * d; *b = 14 * k; }\n\n')
	gen.bind_function('out_values_function_call', 'void', ['int &a', 'int d', 'int *b', 'float k'], {'arg_out': ['a', 'b']})

	gen.insert_code('int out_values_function_call_rval(int &a, int d, int *b, float k = 1) { a = 8 * d; *b = 14 * d; return d*k; }\n\n')
	gen.bind_function_overloads('out_values_function_call_rval', [
		('int', ['int &a', 'int d', 'int *b'], {'arg_out': ['a', 'b']}),
		('int', ['int &a', 'int d', 'int *b', 'float k'], {'arg_out': ['a', 'b']})
	])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

a, b = my_test.out_values_function_call(2, 3)
expect_eq(a, 16)
expect_eq(b, 42)

r, a, b = my_test.out_values_function_call_rval(2)
expect_eq(r, 2)
expect_eq(a, 16)
expect_eq(b, 28)

r, a, b = my_test.out_values_function_call_rval(2, 2)
expect_eq(r, 4)
expect_eq(a, 16)
expect_eq(b, 28)
'''
