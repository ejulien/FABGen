import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	gen.insert_code('''
int *return_nullptr() { return nullptr; }
''')
	gen.bind_function('return_nullptr', 'int *', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

v = my_test.return_nullptr()
assert v is None
'''

test_lua = '''\
my_test = require "my_test"

v = my_test.return_nullptr()
assert(v == nil)
'''

test_go = '''\
package mytest

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {	
	v := ReturnNullptr()
	assert.Nil(t, v, "should be nil.")
}
'''

test_fsharp = '''\
    module MyTest

open NUnit.Framework

[<Test>]
let ``Test``() = 
    let v = ReturnNullptr()
    Assert.IsNull(v, "should be null.")
'''
#In F#, you can call functions and assign their returned values to variables just like in Go.
#The test function calls a function "ReturnNullptr()" and assigns the returned value to the variable "v". Then it uses the "Assert.IsNull()" function to check if the value of "v" is null, which means the pointer is pointing to nothing.

#This test case checks if the ReturnNullptr function is working correctly and returning a null pointer.