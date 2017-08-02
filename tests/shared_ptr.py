import lib

from lib.stl import SharedPtrProxyFeature


def bind_test(gen):
	gen.start('my_test')

	lib.bind_all_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() = default;
	simple_struct(float k) : u(k), v(10 * int(k)) {}

	float u = 4.f;
	int v = 7;
};

std::shared_ptr<simple_struct> get_shared_ptr_to_simple_struct() { return std::make_shared<simple_struct>(); }
''', True, False)

	gen.add_include('memory', True)

	simple_struct_conv = gen.begin_class('simple_struct')
	gen.bind_members(simple_struct_conv, ['float u', 'int v'])
	gen.end_class(simple_struct_conv)

	shared_ptr_simple_struct_conv = gen.begin_class('std::shared_ptr<simple_struct>', bound_name='ssimple_struct', features={'proxy': SharedPtrProxyFeature(simple_struct_conv)})
	gen.bind_constructor(shared_ptr_simple_struct_conv, ['float k'], ['proxy'])
	gen.bind_members(shared_ptr_simple_struct_conv, ['float u', 'int v'], ['proxy'])
	gen.end_class(shared_ptr_simple_struct_conv)

	gen.bind_function('get_shared_ptr_to_simple_struct', 'std::shared_ptr<simple_struct>', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

sp = my_test.get_shared_ptr_to_simple_struct()

expect_eq(sp.u, 4.0)
expect_eq(sp.v, 7)

sp2 = my_test.ssimple_struct(9.0)

expect_eq(sp2.u, 9.0)
expect_eq(sp2.v, 90)
'''

test_lua = '''\
my_test = require "my_test"

sp = my_test.get_shared_ptr_to_simple_struct()

assert(sp.u == 4.0)
assert(sp.v == 7)

sp2 = my_test.ssimple_struct(9.0)

assert(sp2.u == 9.0)
assert(sp2.v == 90)
'''
