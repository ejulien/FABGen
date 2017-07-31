import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_all_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	static int i;
	static const char *s;
};

int simple_struct::i = 5;
const char *simple_struct::s = "some string";
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_static_member(simple_struct, 'int i')
	gen.bind_static_member(simple_struct, 'const char *s')
	gen.end_class(simple_struct)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

expect_eq(my_test.simple_struct.i, 5)
expect_eq(my_test.simple_struct.s, "some string")
'''
