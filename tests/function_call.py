import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
int get_int() { return 8; }

int get() { return 0; }
int get(int v) { return v / 2; }
int get(int v, int k) { return v * k; }
int get(int v, int k, int b) { return v * k + b; }

static int global_int = 0;

void set_global_int() { global_int = 8; }
int get_global_int() { return global_int; }

int get_global_int_multiplied(int k = 5) { return 3 * k; }

void get_modify_arg_in_out(int &v, int k=5) { v = 3 * k + v; }
''', True, False)

	gen.bind_function('get_int', 'int', [])
	gen.bind_function_overloads('get', [
		('int', [], []),
		('int', ['int v'], []),
		('int', ['int v', 'int k'], []),
		('int', ['int v', 'int k', 'int b'], [])
	])

	gen.bind_function('set_global_int', 'void', [])
	gen.bind_function('get_global_int', 'int', [])

	gen.bind_function('get_global_int_multiplied', 'int', ['?int k'])

	gen.bind_function('get_modify_arg_in_out', 'void', ['int &v', '?int k'], {'arg_in_out': ['v']})

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

assert my_test.get_int() == 8

assert my_test.get_global_int() == 0
my_test.set_global_int()
assert my_test.get_global_int() == 8

# overload
assert my_test.get() == 0
assert my_test.get(2) == 1
assert my_test.get(4, 3) == 12
assert my_test.get(4, 3, 2) == 14

# optional argument
assert my_test.get_global_int_multiplied() == 15
assert my_test.get_global_int_multiplied(2) == 6
'''

test_lua = '''\
my_test = require "my_test"

assert(my_test.get_int() == 8)

assert(my_test.get_global_int() == 0)
my_test.set_global_int()
assert(my_test.get_global_int() == 8)

-- overload
assert(my_test.get() == 0)
assert(my_test.get(2) == 1)
assert(my_test.get(4, 3) == 12)
assert(my_test.get(4, 3, 2) == 14)

-- optional argument
assert(my_test.get_global_int_multiplied() == 15)
assert(my_test.get_global_int_multiplied(2) == 6)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	assert.Equal(t, GetInt(), int32(8), "should be the same.")

	assert.Equal(t, GetGlobalInt(), int32(0), "should be the same.")

	SetGlobalInt()
	assert.Equal(t, GetGlobalInt(), int32(8), "should be the same.")

	// overload
	assert.Equal(t, Get(), int32(0), "should be the same.")
	assert.Equal(t, GetWithV(2), int32(1), "should be the same.")
	assert.Equal(t, GetWithVK(4, 3), int32(12), "should be the same.")
	assert.Equal(t, GetWithVKB(4, 3, 2), int32(14), "should be the same.")

	// optional argument
	assert.Equal(t, GetGlobalIntMultiplied(), int32(15), "should be the same.")
	assert.Equal(t, GetGlobalIntMultipliedWithK(2), int32(6), "should be the same.")

	// argument in out
	v := int32(2)
	GetModifyArgInOut(&v)
	assert.Equal(t, v, int32(17), "should be the same.")

	v = int32(2)
	GetModifyArgInOutWithK(&v, 4)
	assert.Equal(t, v, int32(14), "should be the same.")
}
'''

test_fsharp = '''\
    module MyTest

open NUnit.Framework

[<Test>]
let ``Test``() = 
    Assert.AreEqual(GetInt(), 8, "should be the same.")

    let mutable globalInt = 0
    Assert.AreEqual(GetGlobalInt globalInt, 0, "should be the same.")

    SetGlobalInt globalInt
    Assert.AreEqual(GetGlobalInt globalInt, 8, "should be the same.")

    // overload
    Assert.AreEqual(Get(), 0, "should be the same.")
    Assert.AreEqual(GetWithV 2, 1, "should be the same.")
    Assert.AreEqual(GetWithVK 4 3, 12, "should be the same.")
    Assert.AreEqual(GetWithVKB 4 3 2, 14, "should be the same.")

    // optional argument
    Assert.AreEqual(GetGlobalIntMultiplied globalInt, 15, "should be the same.")
    Assert.AreEqual(GetGlobalIntMultipliedWithK globalInt 2, 6, "should be the same.")

    // argument in out
    let mutable v = 2
    GetModifyArgInOut v
    Assert.AreEqual(v, 17, "should be the same.")

    v <- 2
    GetModifyArgInOutWithK v 4
    Assert.AreEqual(v, 14, "should be the same.")
'''
#In F#, functions are called using the same syntax as in Go, with the difference that parameters are separated by spaces. Also, you don't need to import any package to perform assertions, you can use the NUnit.Framework module that comes with the NUnit package.
#The code is calling several functions that have different types of parameters and checks the returned values against expected results using the Assert.AreEqual function.

#The functions being tested are:

#GetInt: which returns an int32
#GetGlobalInt: which returns the value of a global int32 variable
#SetGlobalInt: which sets the value of the global int32 variable
#Get