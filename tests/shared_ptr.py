def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	float u = 4.f;
	int v = 7;
};
''', True, False)

	gen.begin_class('simple_struct')
	gen.bind_members('simple_struct', ['float u', 'int v'])
	gen.end_class('simple_struct')

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

#expect_eq(my_test.test_simple_struct(), True)

# ...
'''
