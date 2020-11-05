import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	gen.insert_code('''
struct A { int v{2}; };
void modify_in_out_struct(A *a) { a->v = 3; }
''')
	A = gen.begin_class('A')
	gen.bind_constructor(A, [])
	gen.bind_member(A, 'int v')
	gen.end_class(A)
	gen.bind_function('modify_in_out_struct', 'void', ['A *a'], {'arg_in_out': ['a']})

	gen.insert_code('void out_values_function_call(int &a, int d, int *b, float k) { a = 8 * d; *b = 14 * k; }\n\n')
	gen.bind_function('out_values_function_call', 'void', ['int &a', 'int d', 'int *b', 'float k'], {'arg_out': ['a', 'b']})

	gen.insert_code('int out_values_function_call_rval(int &a, int d, int *b, float k = 1) { a = 8 * d; *b = 14 * d; return d*k; }\n\n')
	gen.bind_function_overloads('out_values_function_call_rval', [
		('int', ['int &a', 'int d', 'int *b'], {'arg_out': ['a', 'b']}),
		('int', ['int &a', 'int d', 'int *b', 'float k'], {'arg_out': ['a', 'b']})
	])

	gen.insert_code('bool in_out_value(int *in_out) { *in_out = *in_out * 4; return true; }')
	gen.bind_function('in_out_value', 'bool', ['int *in_out'], {'arg_in_out': ['in_out']})

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

a = my_test.A()
a = my_test.modify_in_out_struct(a)
assert a.v == 3

a, b = my_test.out_values_function_call(2, 3)
assert a == 16
assert b == 42

r, a, b = my_test.out_values_function_call_rval(2)
assert r == 2
assert a == 16
assert b == 28

r, a, b = my_test.out_values_function_call_rval(2, 2)
assert r == 4
assert a == 16
assert b == 28

r, v = my_test.in_out_value(5)
assert r == True
assert v == 20
'''

test_lua = '''\
my_test = require "my_test"

a = my_test.A()
a = my_test.modify_in_out_struct(a)
assert(a.v == 3)

a, b = my_test.out_values_function_call(2, 3)
assert(a == 16)
assert(b == 42)

r, a, b = my_test.out_values_function_call_rval(2)
assert(r == 2)
assert(a == 16)
assert(b == 28)

r, a, b = my_test.out_values_function_call_rval(2, 2)
assert(r == 4)
assert(a == 16)
assert(b == 28)

r, v = my_test.in_out_value(5)
assert(r == true)
assert(v == 20)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	a := NewA()
	defer a.Free()
	ModifyInOutStruct(a)
	assert.Equal(t, a.GetV(), int32(3), "should be the same.")

	c, b := OutValuesFunctionCall(2, 3)
	assert.Equal(t, *c, int32(16), "should be the same.")
	assert.Equal(t, *b, int32(42), "should be the same.")

	r, c, b := OutValuesFunctionCallRval(2)
	assert.Equal(t, r, int32(2), "should be the same.")
	assert.Equal(t, *c, int32(16), "should be the same.")
	assert.Equal(t, *b, int32(28), "should be the same.")

	r, c, b = OutValuesFunctionCallRvalWithK(2, 2)
	assert.Equal(t, r, int32(4), "should be the same.")
	assert.Equal(t, *c, int32(16), "should be the same.")
	assert.Equal(t, *b, int32(28), "should be the same.")

	w := int32(5)
	rb := InOutValue(&w)
	assert.True(t, rb, "should be the same.")
	assert.Equal(t, w, int32(20), "should be the same.")
}
'''