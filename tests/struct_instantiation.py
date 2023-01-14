import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : v_(-8) {}
	simple_struct(int v) : v_(v) {}
	int v_;
};
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_constructor_overloads(simple_struct, [
		([], []),
		(['int v_'], [])
	])
	gen.bind_member(simple_struct, 'int v_')
	gen.end_class(simple_struct)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

s = my_test.simple_struct()
t = my_test.simple_struct(4)

assert s.v_ == -8
assert t.v_ == 4
'''

test_lua = '''\
my_test = require "my_test"

s = my_test.simple_struct()
t = my_test.simple_struct(4)

assert(s.v_ == -8)
assert(t.v_ == 4)
'''

test_go = """\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	s := NewSimpleStruct()
	u := NewSimpleStructWithV(int32(4))

	assert.Equal(t, s.GetV(), int32(-8), "should be the same.")
	assert.Equal(t, u.GetV(), int32(4), "should be the same.")
}
"""

test_fsharp = '''\
    open NUnit.Framework

[<Test>]
let ``test struct creation`` () =
    let s = new SimpleStruct()
    let u = new SimpleStruct(4)

    Assert.AreEqual(s.V, -8)
    Assert.AreEqual(u.V, 4)
'''
#The test function creates a variable s and assigns the result of calling the constructor of SimpleStruct with no arguments to it, which creates a new instance of a struct with default values. Then it creates a variable u and assigns the result of calling the constructor of SimpleStruct with the argument 4 which creates a new instance of the same struct with a custom value for the property V. After that, it uses the Assert.AreEqual() function to check that the value of the property s.V match the expected value -8 and the value of the property u.V match the expected value 4.

#This test is checking if the constructor new SimpleStruct() creates a struct with the default value, and if the constructor new SimpleStruct(4) creates a struct with the custom value.