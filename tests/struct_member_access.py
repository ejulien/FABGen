import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_all_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : a(7), b(17.5f), c(true), d(9), text_field("some content") {}
	int a;
	float b;
	bool c;
	const int d;
	const char *text_field;
};

static simple_struct return_instance;
simple_struct *return_simple_struct_by_pointer() { return &return_instance; }
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_members(simple_struct, ['const char *text_field', 'int a', 'float b', 'bool c', 'const int d'])
	gen.end_class(simple_struct)

	gen.bind_function('return_simple_struct_by_pointer', 'simple_struct*', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

s = my_test.return_simple_struct_by_pointer()

expect_eq(s.a, 7)
expect_eq(s.b, 17.5)
expect_eq(s.c, True)
expect_eq(s.d, 9)
expect_eq(s.text_field, "some content")

s.a = -2
s.b = -4.5
s.c = False

expect_eq(s.a, -2)
expect_eq(s.b, -4.5)
expect_eq(s.c, False)

s.a += 4
expect_eq(s.a, 2)

# write to const member
write_to_const_failed = False
try:
	s.d = 12
except Exception:
	write_to_const_failed = True
expect_eq(write_to_const_failed, True)

expect_eq(s.d, 9)
'''

test_lua = '''\
my_test = require "my_test"

s = my_test.return_simple_struct_by_pointer()

assert(s.a == 7)
assert(s.b == 17.5)
assert(s.c == true)
assert(s.d == 9)
assert(s.text_field == "some content")

s.a = -2
s.b = -4.5
s.c = false

assert(s.a == -2)
assert(s.b == -4.5)
assert(s.c == false)

s.a += 4
assert(s.a == 2)

-- FIXME
-- write to const member
--write_to_const_failed = False
--try:
--	s.d = 12
--except Exception:
--	write_to_const_failed = True
--expect_eq(write_to_const_failed, True)

--expect_eq(s.d, 9)
'''
