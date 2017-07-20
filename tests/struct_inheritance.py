def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
struct base_class {
	int base_method() { return 4; }
	int base_method_override() { return 4; }
	virtual int virtual_method() { return 6; }
};

struct derived_class : base_class {
	int derived_method() { return 8; }
	int base_method_override() { return 8; }
	int virtual_method() override { return 9; }
};

int read_virtual_method_through_base_class(base_class &o) {
	return o.virtual_method();
}
''', True, False)

	base_conv =	gen.begin_class('base_class')
	gen.bind_constructor(base_conv, [])
	gen.bind_method(base_conv, 'base_method', 'int', [])
	gen.bind_method(base_conv, 'base_method_override', 'int', [])
	gen.end_class(base_conv)

	derived_conv = gen.begin_class('derived_class')
	gen.add_class_base(derived_conv, base_conv)
	gen.bind_constructor(derived_conv, [])
	gen.bind_method(derived_conv, 'derived_method', 'int', [])
	gen.bind_method(derived_conv, 'base_method_override', 'int', [])
	gen.end_class(derived_conv)

	gen.bind_function('read_virtual_method_through_base_class', 'int', ['base_class &o'])

	gen.finalize()

	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

base = my_test.base_class()
expect_eq(base.base_method(), 4)
expect_eq(base.base_method_override(), 4)

derived = my_test.derived_class()
expect_eq(derived.base_method(), 4)  # can still access base class
expect_eq(derived.derived_method(), 8)  # can access its own methods
expect_eq(derived.base_method_override(), 8)  # properly overshadows redeclared base methods

# argument casting through inheritance tree
expect_eq(my_test.read_virtual_method_through_base_class(base), 6)
expect_eq(my_test.read_virtual_method_through_base_class(derived), 9)
'''
