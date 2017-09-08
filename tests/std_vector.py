import lib.std
import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
#include <iostream>

int consume_pointer_to_int(const int *p) {
	std::cout << p[0] << std::endl;
	std::cout << p[1] << std::endl;
	return p[1];
}
''', True, False)

	int_ptr = gen.bind_ptr('int *', bound_name='IntPointer')

	gen.add_include('vector', is_system=True)

	std_vector_int = gen.begin_class('std::vector<int>', features={'sequence': lib.std.VectorSequenceFeature(gen.get_conv('int'))})
	gen.bind_constructor(std_vector_int, [])

	gen.bind_method(std_vector_int, 'size', 'int', [])
	gen.bind_method(std_vector_int, 'push_back', 'void', ['int v'])
	gen.bind_method(std_vector_int, 'at', 'int&', ['int pos'])

	gen.bind_method(std_vector_int, 'data', 'int*', [])

	gen.end_class(std_vector_int)

	gen.bind_function('consume_pointer_to_int', 'int', ['const int *p'])

	gen.add_cast(std_vector_int, int_ptr, lambda in_var, out_var: '%s = ((std::vector<int> *)%s)->data();\n' % (out_var, in_var))

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

v = my_test.vector_of_int()

assert v.size() == 0
assert len(v) == 0

v.push_back(5)
v.push_back(1)
v.push_back(9)

assert v.size() == 3
assert len(v) == 3

assert v.at(1) == 1
assert v.at(2) == 9
assert v.at(0) == 5

assert v[1] == 1
assert v[2] == 9
assert v[0] == 5

v[1] = 16

assert v[2] == 9
assert v[0] == 5
assert v[1] == 16

v[0] *= 4

assert v[0] == 20

assert my_test.consume_pointer_to_int(v.data()) == 16

# implicit cast to const int *
assert my_test.consume_pointer_to_int(v) == 16
'''

test_lua = '''\
my_test = require "my_test"

v = my_test.vector_of_int()

assert(v:size() == 0)
assert(#v == 0)

v:push_back(5)
v:push_back(1)
v:push_back(9)

assert(v:size() == 3)
assert(#v == 3)

assert(v:at(1) == 1)
assert(v:at(2) == 9)
assert(v:at(0) == 5)

assert(v[1] == 1)
assert(v[2] == 9)
assert(v[0] == 5)

v[1] = 16

assert(v[2] == 9)
assert(v[0] == 5)
assert(v[1] == 16)

v[0] = v[0] * 4

assert(v[0] == 20)

assert(my_test.consume_pointer_to_int(v:data()) == 16)

-- implicit cast to const int *
assert(my_test.consume_pointer_to_int(v) == 16)
'''
