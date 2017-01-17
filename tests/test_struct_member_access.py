def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : a(7), b(17.5f), c(true) {}
	int a;
	float b;
	bool c;
};

static simple_struct return_instance;
simple_struct *return_simple_struct_by_pointer() { return &return_instance; }
''', True, False)

	gen.bind_class('simple_struct', ['int a', 'float b', 'bool c'], [])
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
'''
