import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
// basic interoperability
int return_int() { return 8; }
float return_float() { return 8.f; }
const char *return_const_char_ptr() { return "const char * -> string"; }

static int static_int = 9;

int *return_int_by_pointer() { return &static_int; }
int &return_int_by_reference() { return static_int; }

// argument passing
int add_int_by_value(int a, int b) { return a + b; }
int add_int_by_pointer(int *a, int *b) { return *a + *b; }
int add_int_by_reference(int &a, int &b) { return a + b; }
\n''', True, False)

	gen.add_include('string', True)

	gen.bind_function('return_int', 'int', [])
	gen.bind_function('return_float', 'float', [])
	gen.bind_function('return_const_char_ptr', 'const char *', [])

	gen.bind_function('return_int_by_pointer', 'int*', [])
	gen.bind_function('return_int_by_reference', 'int&', [])

	gen.bind_function('add_int_by_value', 'int', ['int a', 'int b'])
	gen.bind_function('add_int_by_pointer', 'int', ['int *a', 'int *b'])
	gen.bind_function('add_int_by_reference', 'int', ['int &a', 'int &b'])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

expect_eq(my_test.return_int(), 8)
expect_eq(my_test.return_float(), 8)
expect_eq(my_test.return_const_char_ptr(), "const char * -> string")

expect_eq(my_test.return_int_by_pointer(), 9)
expect_eq(my_test.return_int_by_reference(), 9)

expect_eq(my_test.add_int_by_value(3, 4), 7)
expect_eq(my_test.add_int_by_pointer(3, 4), 7)
expect_eq(my_test.add_int_by_reference(3, 4), 7)
'''

test_lua = '''\
my_test = require "my_test"

assert(my_test.return_int() == 8)
assert(my_test.return_float() == 8)
assert(my_test.return_const_char_ptr() == "const char * -> string")

assert(my_test.return_int_by_pointer() == 9)
assert(my_test.return_int_by_reference() == 9)

assert(my_test.add_int_by_value(3, 4) == 7)
assert(my_test.add_int_by_pointer(3, 4) == 7)
assert(my_test.add_int_by_reference(3, 4) == 7)
'''
