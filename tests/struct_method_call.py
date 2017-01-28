def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : a(1) {}

	int set_a(int v) { return a = v; }

	bool set_a(int v0, int v1) {
		a = v0 + v1;
		return true;
	}

	int get_a() { return a; }

	int a;
};
''', True, False)

	gen.begin_class('simple_struct')
	gen.bind_constructor('simple_struct', [])
	gen.bind_method_overloads('simple_struct', 'set_a', [('int', ['int v']), ('bool', ['int v0', 'int v1'])])
	gen.bind_method('simple_struct', 'get_a', 'int', [])
	gen.end_class('simple_struct')

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

s = my_test.simple_struct()

expect_eq(s.get_a(), 1)
expect_eq(s.set_a(8, 2), True)

expect_eq(s.get_a(), 10)

expect_eq(s.set_a(9), 9)
expect_eq(s.get_a(), 9)
'''
