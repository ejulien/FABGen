def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct(int _v) : v(_v) {}

	simple_struct operator-(const simple_struct &b) { return simple_struct(v - b.v); }
	simple_struct operator+(const simple_struct &b) { return simple_struct(v + b.v); }
	simple_struct operator/(const simple_struct &b) { return simple_struct(v / b.v); }
	simple_struct operator*(const simple_struct &b) { return simple_struct(v * b.v); }

	int v;
};
''', True, False)

	gen.begin_class('simple_struct')
	gen.bind_constructor('simple_struct', 'int')
	gen.bind_operator('simple_struct', '-', 'simple_struct', ['simple_struct b'])
	gen.bind_operator('simple_struct', '+', 'simple_struct', ['simple_struct b'])
	gen.bind_operator('simple_struct', '/', 'simple_struct', ['simple_struct b'])
	gen.bind_operator('simple_struct', '*', 'simple_struct', ['simple_struct b'])
	gen.bind_member('simple_struct', 'int v')
	gen.end_class('simple_struct')

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

a, b = my_test.simple_struct(4), my_test.simple_struct(8)

s = a + b
expect_eq(s.v, 12)
'''
