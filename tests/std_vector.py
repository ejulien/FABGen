import lib.std


def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
#include <iostream>

void consume_pointer_to_int(const int *p) {
	std::cout << p[0] << std::endl;
	std::cout << p[1] << std::endl;
}
''', True, False)

	int_ptr = gen.bind_ptr('int *', bound_name='PointerToIntData')

	gen.add_include('vector', is_system=True)

	std_vector_int = gen.begin_class('std::vector<int>', features={'sequence': lib.std.VectorSequenceFeature(gen.get_conv('int'))})
	gen.bind_constructor(std_vector_int, [])

	gen.bind_method(std_vector_int, 'size', 'int', [])
	gen.bind_method(std_vector_int, 'push_back', 'void', ['int v'])
	gen.bind_method(std_vector_int, 'at', 'int&', ['int pos'])

	gen.bind_method(std_vector_int, 'data', 'int*', [])

	gen.end_class(std_vector_int)

	gen.bind_function('consume_pointer_to_int', 'void', ['const int *p'])

	gen.add_cast(std_vector_int, int_ptr, lambda in_var, out_var: '%s = ((std::vector<int> *)%s)->data();\n' % (out_var, in_var))

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

v = my_test.vector_of_int()

expect_eq(v.size(), 0)
expect_eq(len(v), 0)

v.push_back(5)
v.push_back(1)
v.push_back(9)

expect_eq(v.size(), 3)
expect_eq(len(v), 3)

expect_eq(v.at(1), 1)
expect_eq(v.at(2), 9)
expect_eq(v.at(0), 5)

expect_eq(v[1], 1)
expect_eq(v[2], 9)
expect_eq(v[0], 5)

v[1] = 16

expect_eq(v[2], 9)
expect_eq(v[0], 5)
expect_eq(v[1], 16)

v[0] *= 4

expect_eq(v[0], 20)

my_test.consume_pointer_to_int(v.data())

# implicit cast to const int *
my_test.consume_pointer_to_int(v)
'''
