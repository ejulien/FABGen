import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
int v{2};

struct simple_struct {
	int v{4};
};

simple_struct s;

namespace ns {
	int v{14};
}
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_member(simple_struct, 'int v')
	gen.end_class(simple_struct)

	gen.bind_variables(['int v', 'simple_struct s'])
	gen.bind_variable('int ns::v', bound_name='w')

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

assert my_test.v == 2
my_test.v = 5
assert my_test.v == 5

assert my_test.s.v == 4
my_test.s.v = 9
assert my_test.s.v == 9

assert my_test.w == 14
'''

test_lua = '''\
my_test = require "my_test"

assert(my_test.v == 2)
my_test.v = 5
assert(my_test.v == 5)

assert(my_test.s.v == 4)
my_test.s.v = 9
assert(my_test.s.v == 9)

assert(my_test.w == 14)
'''
