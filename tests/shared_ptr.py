import lib

from lib.stl import SharedPtrProxyFeature


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() = default;
	simple_struct(float k) : u(k), v(10 * int(k)) {}

	float u = 4.f;
	int v = 7;
};

std::shared_ptr<simple_struct> get_shared_ptr_to_simple_struct() { return std::make_shared<simple_struct>(); }

std::shared_ptr<simple_struct> get_empty_shared_ptr() { return {}; }
''', True, False)

	gen.add_include('memory', True)

	simple_struct_conv = gen.begin_class('simple_struct')
	gen.bind_members(simple_struct_conv, ['float u', 'int v'])
	gen.end_class(simple_struct_conv)

	shared_ptr_simple_struct_conv = gen.begin_class('std::shared_ptr<simple_struct>', bound_name='ssimple_struct', features={'proxy': SharedPtrProxyFeature(simple_struct_conv)})
	gen.bind_constructor(shared_ptr_simple_struct_conv, ['float k'], ['proxy'])
	gen.bind_members(shared_ptr_simple_struct_conv, ['float u', 'int v'], ['proxy'])
	gen.end_class(shared_ptr_simple_struct_conv)

	gen.bind_function('get_shared_ptr_to_simple_struct', 'std::shared_ptr<simple_struct>', [])

	gen.bind_function('get_empty_shared_ptr', 'std::shared_ptr<simple_struct>', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

sp = my_test.get_shared_ptr_to_simple_struct()

assert sp.u == 4.0
assert sp.v == 7

sp2 = my_test.ssimple_struct(9.0)

assert sp2.u == 9.0
assert sp2.v == 90

spn = my_test.get_empty_shared_ptr()

assert spn == None
'''

test_lua = '''\
my_test = require "my_test"

sp = my_test.get_shared_ptr_to_simple_struct()

assert(sp.u == 4.0)
assert(sp.v == 7)

sp2 = my_test.ssimple_struct(9.0)

assert(sp2.u == 9.0)
assert(sp2.v == 90)

spn = my_test.get_empty_shared_ptr()

assert(spn == nil)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	sp := GetSharedPtrToSimpleStruct()
	
	assert.Equal(t, sp.GetU(), float32(4.0), "should be the same.")
	assert.Equal(t, sp.GetV(), int32(7), "should be the same.")

	sp2 := NewSsimpleStruct(9.0)

	assert.Equal(t, sp2.GetU(), float32(9.0), "should be the same.")
	assert.Equal(t, sp2.GetV(), int32(90), "should be the same.")

	spn := GetEmptySharedPtr()

	assert.True(t, spn.IsNil(), "should be nil.")
}
'''

test_fsharp = '''\
    module MyTest

open NUnit.Framework

[<Test>]
let ``Test``() = 
    let sp = GetSharedPtrToSimpleStruct()
	
    Assert.AreEqual(sp.GetU(), 4.0, "should be the same.")
    Assert.AreEqual(sp.GetV(), 7, "should be the same.")

    let sp2 = NewSsimpleStruct(9.0)

    Assert.AreEqual(sp2.GetU(), 9.0, "should be the same.")
    Assert.AreEqual(sp2.GetV(), 90, "should be the same.")

    let spn = GetEmptySharedPtr()

    Assert.IsTrue(spn.IsNil(), "should be nil.")
'''
#In F#, you can call functions and assign their returned values to variables just like in Go.
#The test function calls the function "GetSharedPtrToSimpleStruct()" and assigns the returned value to the variable "sp". Then it uses the "Assert.AreEqual()" function to check if the "GetU()" and "GetV()" method called on object "sp" returns the expected values of 4.0 and 7 respectively.

#Then it calls the function "NewSsimpleStruct()" passing in the argument 9.0 and assigns the returned value to the variable "sp2". Then it uses the "Assert.AreEqual()" function to check if the "GetU()" and "GetV()" method called on object "sp2" returns the expected values of 9.0 and 90 respectively.

#Then it calls the function "GetEmptySharedPtr()" and assigns the returned value to the variable "spn". 