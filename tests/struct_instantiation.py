def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct(int v) : v_(v) {}
	int get() { return v_; }
	int v_;
};
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_class_constructor(simple_struct, ['int v_'])
	gen.bind_class_member(simple_struct, 'int v_')
	gen.bind_class_method(simple_struct, 'get', 'int', [])
	gen.end_class(simple_struct)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

s = my_test.simple_struct()
expect_eq(s.get(), 8)
'''
