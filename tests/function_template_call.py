import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
template <typename T> T get() { return T(8); }
''', True, False)

	gen.bind_function('get<int>', 'int', [], bound_name='get_int')
	gen.bind_function('get<float>', 'float', [], bound_name='get_float')

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

assert my_test.get_int() == 8
assert my_test.get_float() == 8
'''

test_lua = '''\
my_test = require "my_test"

assert(my_test.get_int() == 8)
assert(my_test.get_float() == 8)
'''

test_go = """\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	assert.Equal(t, GetInt(), int32(8), "should be the same.")
	assert.Equal(t, GetFloat(), float32(8), "should be the same.")
}
"""

test_fsharp= '''\
    module MyTest

open NUnit.Framework

[<Test>]
let ``Test``() = 
    Assert.AreEqual(GetInt(), 8, "should be the same.")
    Assert.AreEqual(GetFloat(), 8.0, "should be the same.")
'''
#n F#, functions are called using the same syntax as in Go, with the difference that parameters are separated by spaces. Also, you don't need to import any package to perform assertions, you can use the NUnit.Framework module that comes with the NUnit package.

#The test function calls two functions:

#GetInt: which returns an int32 value
#GetFloat: which returns a float32 value
#It uses the "Assert.AreEqual()" function to compare the returned values with the expected values, 8 and 8.0 respectively, and check if they are the same.

#This test case checks if the GetInt and GetFloat functions are working correctly and returning the expected results.