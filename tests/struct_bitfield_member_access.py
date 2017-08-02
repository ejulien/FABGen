import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_all_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : a(3), b(11), c(1) {}
	unsigned int a:2;
	unsigned int b:4;
	unsigned int c:2;
};
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_constructor(simple_struct, [])
	gen.bind_members(simple_struct, ['int a:', 'int b:', 'int c:'])
	gen.end_class(simple_struct)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

s = my_test.simple_struct()

expect_eq(s.a, 3)
expect_eq(s.b, 11)
expect_eq(s.c, 1)

s.a = 1
s.b = 7
s.c = 2

expect_eq(s.a, 1)
expect_eq(s.b, 7)
expect_eq(s.c, 2)
'''

test_lua = '''\
my_test = require "my_test"

s = my_test.simple_struct()

assert(s.a, 3)
assert(s.b, 11)
assert(s.c, 1)

s.a = 1
s.b = 7
s.c = 2

assert(s.a, 1)
assert(s.b, 7)
assert(s.c, 2)
'''
