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
		gen.bind_type(lib.cpython.stl.PySequenceToStdVectorConverter('PySequenceOfInt_ptr', int_ptr))
	elif gen.get_language() == 'Lua':
		gen.bind_type(lib.lua.stl.LuaTableToStdVectorConverter('LuaTableOfInt', int_conv))
		gen.bind_type(lib.lua.stl.LuaTableToStdVectorConverter('LuaTableOfInt_ptr', int_ptr))
	elif gen.get_language() == 'Go':
		gen.bind_type(lib.go.stl.GoSliceToStdVectorConverter('GoSliceOfInt', int_conv))
		gen.bind_type(lib.go.stl.GoSliceToStdVectorConverter('GoSliceOfInt_ptr', int_ptr))

	std_vector_int = gen.begin_class('std::vector<int>', features={'sequence': lib.std.VectorSequenceFeature(int_conv)})

	if gen.get_language() == 'CPython':
		gen.bind_constructor(std_vector_int, ['?PySequenceOfInt sequence'])
	elif gen.get_language() == 'Lua':
		gen.bind_constructor(std_vector_int, ['?LuaTableOfInt sequence'])
	elif gen.get_language() == 'Go':
		gen.bind_constructor(std_vector_int, ['?GoSliceOfInt sequence'])

	gen.bind_method(std_vector_int, 'size', 'int', [])
	gen.bind_method(std_vector_int, 'push_back', 'void', ['int v'])
	gen.bind_method(std_vector_int, 'at', 'int&', ['int pos'])

	gen.bind_method(std_vector_int, 'data', 'int*', [])

	gen.end_class(std_vector_int)

	gen.bind_function('consume_pointer_to_int', 'int', ['const int *p'])

	gen.add_cast(std_vector_int, int_ptr, lambda in_var, out_var: '%s = ((std::vector<int> *)%s)->data();\n' % (out_var, in_var))

	std_vector_int_ptr = gen.begin_class('std::vector<int*>', features={'sequence': lib.std.VectorSequenceFeature(int_ptr)})

	if gen.get_language() == 'CPython':
		gen.bind_constructor(std_vector_int_ptr, ['?PySequenceOfInt_ptr sequence'])
	elif gen.get_language() == 'Lua':
		gen.bind_constructor(std_vector_int_ptr, ['?LuaTableOfInt_ptr sequence'])
	elif gen.get_language() == 'Go':
		gen.bind_constructor(std_vector_int_ptr, ['?GoSliceOfInt_ptr sequence'])

	gen.bind_method(std_vector_int_ptr, 'size', 'int', [])
	gen.bind_method(std_vector_int_ptr, 'push_back', 'void', ['int* v'])
	gen.bind_method(std_vector_int_ptr, 'at', 'int*&', ['int pos'])

	gen.bind_method(std_vector_int_ptr, 'data', 'int**', [])

	gen.end_class(std_vector_int_ptr)

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

v_ptr = my_test.vector_of_int_ptr()
v_ptr.push_back(0)
v_ptr.push_back(v.data())

assert v_ptr.size() == 2
assert len(v_ptr) == 2

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

v_ptr = my_test.vector_of_int_ptr()

v_ptr:push_back(0)
v_ptr:push_back(v:data())

assert(v_ptr:size() == 2)
assert(#v_ptr == 2)

'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	v := NewVectorOfInt()

	assert.Equal(t, v.Size(), int32(0), "should be the same.")
	assert.Equal(t, v.Len(), int32(0), "should be the same.")

	v.PushBack(5)
	v.PushBack(1)
	v.PushBack(9)

	assert.Equal(t, v.Size(), int32(3), "should be the same.")
	assert.Equal(t, v.Len(), int32(3), "should be the same.")

	assert.Equal(t, *v.At(1), int32(1), "should be the same.")
	assert.Equal(t, *v.At(2), int32(9), "should be the same.")
	assert.Equal(t, *v.At(0), int32(5), "should be the same.")

	assert.Equal(t, v.Get(1), int32(1), "should be the same.")
	assert.Equal(t, v.Get(2), int32(9), "should be the same.")
	assert.Equal(t, v.Get(0), int32(5), "should be the same.")

	v.Set(1, 16)

	assert.Equal(t, v.Get(2), int32(9), "should be the same.")
	assert.Equal(t, v.Get(0), int32(5), " should be the same.")
	assert.Equal(t, v.Get(1), int32(16), "should be the same.")

	v.Set(0, v.Get(0)*4)

	assert.Equal(t, v.Get(0), int32(20), "should be the same.")

	assert.Equal(t, ConsumePointerToInt(v.Data()), int32(16), "should be the same.")

	// implicit cast to const int *
	//	assert.Equal(t, ConsumePointerToInt(v), int32(16), "should be the same.")

	// // construct from GoSlice
	w := NewVectorOfIntWithSequence([]int32{5, 2, 8})

	assert.Equal(t, w.Get(0), int32(5), "should be the same.")
	assert.Equal(t, w.Get(1), int32(2), "should be the same.")
	assert.Equal(t, w.Get(2), int32(8), "should be the same.")

	vPtr := NewVectorOfIntPtr()
	vPtr.PushBack(nil)
	vPtr.PushBack(v.Data())

	assert.Equal(t, vPtr.Size(), int32(2), "should be the same.")
	assert.Equal(t, vPtr.Len(), int32(2), "should be the same.")
}
'''