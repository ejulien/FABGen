import lib.std
import lib.stl
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
	int_conv = gen.get_conv('int')

	gen.add_include('vector', is_system=True)

	if gen.get_language() == 'CPython':
		gen.bind_type(lib.cpython.stl.PySequenceToStdVectorConverter('PySequenceOfInt', int_conv))
	elif gen.get_language() == 'Lua':
		gen.bind_type(lib.lua.stl.LuaTableToStdVectorConverter('LuaTableOfInt', int_conv))

	std_vector_int = gen.begin_class('std::vector<int>', features={'sequence': lib.std.VectorSequenceFeature(int_conv)})

	if gen.get_language() == 'CPython':
		gen.bind_constructor(std_vector_int, ['?PySequenceOfInt sequence'])
	elif gen.get_language() == 'Lua':
		gen.bind_constructor(std_vector_int, ['?LuaTableOfInt sequence'])

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

# construct from PySequence
w = my_test.vector_of_int([5, 2, 8])

assert w[0] == 5
assert w[1] == 2
assert w[2] == 8
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

assert(v[2] == 1)
assert(v[3] == 9)
assert(v[1] == 5)

v[2] = 16

assert(v[3] == 9)
assert(v[1] == 5)
assert(v[2] == 16)

v[1] = v[1] * 4

assert(v[1] == 20)

assert(my_test.consume_pointer_to_int(v:data()) == 16)

-- implicit cast to const int *
assert(my_test.consume_pointer_to_int(v) == 16)

-- construct from table of int
w = my_test.vector_of_int({5, 2, 8})

assert(w[1] == 5)
assert(w[2] == 2)
assert(w[3] == 8)
'''
