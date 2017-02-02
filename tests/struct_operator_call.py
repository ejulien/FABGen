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

	simple_struct operator+(int k) { return simple_struct(v + k); }
	simple_struct operator/(int k) { return simple_struct(v / k); }
	simple_struct operator*(int k) { return simple_struct(v * k); }
	simple_struct operator-(int k) { return simple_struct(v - k); }

	void operator-=(const simple_struct &b) { v -= b.v; }
	void operator+=(const simple_struct &b) { v += b.v; }
	void operator/=(const simple_struct &b) { v /= b.v; }
	void operator*=(const simple_struct &b) { v *= b.v; }

	void operator-=(int k) { v -= k; }
	void operator+=(int k) { v += k; }
	void operator/=(int k) { v /= k; }
	void operator*=(int k) { v *= k; }

	int v;
};
''', True, False)

	gen.begin_class('simple_struct')
	gen.bind_constructor('simple_struct', 'int')
	gen.bind_arithmetic_ops_overloads('simple_struct', ['-', '+', '/', '*'], [('simple_struct', ['simple_struct b']), ('simple_struct', ['int k'])])
	gen.bind_inplace_arithmetic_ops_overloads('simple_struct', ['-=', '+=', '/=', '*='], [['simple_struct b'], ['int k']])
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
s += b
expect_eq(s.v, 20)
s += 4
expect_eq(s.v, 24)

s = s / 4
expect_eq(s.v, 6)
s /= 3
expect_eq(s.v, 2)
s += a
expect_eq(s.v, 6)

s = s * a
expect_eq(s.v, 24)
s *= 2
expect_eq(s.v, 48)

s = s - b
expect_eq(s.v, 40)
s -= 32
expect_eq(s.v, 8)
'''
