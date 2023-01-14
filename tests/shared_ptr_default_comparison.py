# Although both proxy objects are different they resolve to the same underlying C++ shared_ptr and should test as equal.

import lib

from lib.stl import SharedPtrProxyFeature


def bind_test(gen):
	gen.start('my_test')
	gen.add_include('memory', True)

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
std::shared_ptr<int> obj0(new int(2)), obj1(new int(3)), obj2(obj0);

std::shared_ptr<int> &get_obj0() { return obj0; }
std::shared_ptr<int> &get_obj1() { return obj1; }
std::shared_ptr<int> &get_obj2() { return obj2; }
''', True, False)

	shared_ptr_int_conv = gen.begin_class('std::shared_ptr<int>', bound_name='sint', features={'proxy': SharedPtrProxyFeature(gen.get_conv('int'))})
	gen.end_class(shared_ptr_int_conv)

	gen.bind_function('get_obj0', 'std::shared_ptr<int> &', [])
	gen.bind_function('get_obj1', 'std::shared_ptr<int> &', [])
	gen.bind_function('get_obj2', 'std::shared_ptr<int> &', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

a = my_test.get_obj0()
b = my_test.get_obj0()

assert a == b

c = my_test.get_obj1()

assert a != c
assert b != c

d = my_test.get_obj2()

assert a == d
'''

test_lua = '''\
my_test = require "my_test"

a = my_test.get_obj0()
b = my_test.get_obj0()

assert(a == b)

c = my_test.get_obj1()

assert(a ~= c)
assert(b ~= c)

d = my_test.get_obj2()

assert(a == d)
'''

test_go = '''\
package mytest

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {	
	a := GetObj0()
	b := GetObj0()

	assert.True(t, a.Equal(b), "should be the equal.")

	c := GetObj1()

	assert.True(t, !a.Equal(c), "should be different.")
	assert.True(t, !b.Equal(c), "should be different.")

	d := GetObj2()

	assert.True(t, a.Equal(d), "should be the equal.")
}
'''

test_fsharp = '''\
    module MyTest

open NUnit.Framework

[<Test>]
let ``Test``() = 
    let a = GetObj0()
    let b = GetObj0()

    Assert.IsTrue(a.Equal(b), "should be the equal.")

    let c = GetObj1()

    Assert.IsFalse(a.Equal(c), "should be different.")
    Assert.IsFalse(b.Equal(c), "should be different.")

    let d = GetObj2()

    Assert.IsTrue(a.Equal(d), "should be the equal.")
'''
#In F#, you can call functions and assign their returned values to variables just like in Go.
#The test function calls the function "GetObj0()" twice and assigns the returned values to the variables "a" and "b". Then it uses the "Assert.IsTrue()" function to check if the "Equal()" method called on object "a" and passed object "b" returns true, indicating that the two objects are equal.

#Then it calls the "GetObj1()" function and assigns the returned value to the variable "c". Then it uses the "Assert.IsFalse()" function to check if the "Equal()" method called on objects "a" and "b" with object "c" passed as argument returns false, indicating that the two objects are different.

#Then it calls the "GetObj2()" function and assigns the returned value to the variable "d". Then it uses the "Assert.IsTrue()" function to check if the "Equal()" method called on object "a" with object "