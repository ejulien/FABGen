import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_all_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct nested_struct {
	int v{8};
};

struct enclosing_struct {
	nested_struct n;
};
''', True, False)

	nested_struct = gen.begin_class('nested_struct')
	gen.bind_constructor(nested_struct, [])
	gen.bind_member(nested_struct, 'int v')
	gen.end_class(nested_struct)

	enclosing_struct = gen.begin_class('enclosing_struct')
	gen.bind_constructor(enclosing_struct, [])
	gen.bind_member(enclosing_struct, 'nested_struct n')
	gen.end_class(enclosing_struct)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

#
n = my_test.nested_struct()
expect_eq(n.v, 8)
n.v -= 4
expect_eq(n.v, 4)

#
e = my_test.enclosing_struct()
expect_eq(e.n.v, 8)
e.n.v = 12
expect_eq(e.n.v, 12)
e.n.v *= 4
expect_eq(e.n.v, 48)
e.n.v //= 2
expect_eq(e.n.v, 24)
'''
