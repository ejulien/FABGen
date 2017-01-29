def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
struct base_class {
	int base_method() { return 4; }
	int base_method_override() { return 4; }
};

struct derived_class : base_class {
	int derived_method() { return 8; }
	int base_method_override() { return 8; }
};
''', True, False)

	gen.begin_class('base_class')
	gen.bind_constructor('base_class', [])
	gen.bind_method('base_class', 'base_method', 'int', [])
	gen.bind_method('base_class', 'base_method_override', 'int', [])
	gen.end_class('base_class')

	gen.begin_class('derived_class')
	gen.add_class_base('derived_class', 'base_class')
	gen.bind_constructor('derived_class', [])
	gen.bind_method('derived_class', 'derived_method', 'int', [])
	gen.bind_method('derived_class', 'base_method_override', 'int', [])
	gen.end_class('derived_class')

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
'''
