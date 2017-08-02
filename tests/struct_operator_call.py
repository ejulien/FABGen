import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

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

	bool operator==(int k) const { return k == v; }
	bool operator==(const simple_struct &b) const { return b.v == v; }
	bool operator!=(int k) const { return k != v; }
	bool operator!=(const simple_struct &b) const { return b.v != v; }

	int v;
};
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_constructor(simple_struct, ['int v'])
	gen.bind_arithmetic_ops_overloads(simple_struct, ['-', '+', '/', '*'], [
		('simple_struct', ['simple_struct b'], []),
		('simple_struct', ['int k'], [])
	])
	gen.bind_inplace_arithmetic_ops_overloads(simple_struct, ['-=', '+=', '/=', '*='], [
		(['simple_struct b'], []),
		(['int k'], [])
	])
	gen.bind_comparison_ops_overloads(simple_struct, ['==', '!='], [
		(['simple_struct b'], []),
		(['int k'], [])
	])
	gen.bind_member(simple_struct, 'int v')
	gen.end_class(simple_struct)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq, expect_neq

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

c = a * 2
expect_eq(c, b)
expect_neq(a, b)
'''

test_lua = '''\
my_test = require "my_test"

a, b = my_test.simple_struct(4), my_test.simple_struct(8)

s = a + b
assert(s.v == 12)
s = s + b
assert(s.v == 20)
s = s + 4
assert(s.v == 24)

s = s / 4
assert(s.v == 6)
s = s / 3
assert(s.v == 2)
s = s + a
assert(s.v == 6)

s = s * a
assert(s.v == 24)
s = s * 2
assert(s.v == 48)

s = s - b
assert(s.v == 40)
s = s - 32
assert(s.v == 8)

c = a * 2
assert(c == b)
assert(a ~= b)
'''
