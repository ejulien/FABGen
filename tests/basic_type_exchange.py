import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
// basic interoperability
int return_int() { return 8; }
float return_float() { return 8.f; }
const char *return_const_char_ptr() { return "const char * -> string"; }

static int static_int = 9;

int *return_int_by_pointer() { return &static_int; }
int &return_int_by_reference() { return static_int; }

// argument passing
int add_int_by_value(int a, int b) { return a + b; }
int add_int_by_pointer(int *a, int *b) { return *a + *b; }
int add_int_by_reference(int &a, int &b) { return a + b; }
\n''', True, False)

	gen.add_include('string', True)

	gen.bind_function('return_int', 'int', [])
	gen.bind_function('return_float', 'float', [])
	gen.bind_function('return_const_char_ptr', 'const char *', [])

	gen.bind_function('return_int_by_pointer', 'int*', [])
	gen.bind_function('return_int_by_reference', 'int&', [])

	gen.bind_function('add_int_by_value', 'int', ['int a', 'int b'])
	gen.bind_function('add_int_by_pointer', 'int', ['int *a', 'int *b'])
	gen.bind_function('add_int_by_reference', 'int', ['int &a', 'int &b'])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

assert my_test.return_int() == 8
assert my_test.return_float() == 8
assert my_test.return_const_char_ptr() == "const char * -> string"

assert my_test.return_int_by_pointer() == 9
assert my_test.return_int_by_reference() == 9

assert my_test.add_int_by_value(3, 4) == 7
assert my_test.add_int_by_pointer(3, 4) == 7
assert my_test.add_int_by_reference(3, 4) == 7
'''

test_lua = '''\
my_test = require "my_test"

assert(my_test.return_int() == 8)
assert(my_test.return_float() == 8)
assert(my_test.return_const_char_ptr() == "const char * -> string")

assert(my_test.return_int_by_pointer() == 9)
assert(my_test.return_int_by_reference() == 9)

assert(my_test.add_int_by_value(3, 4) == 7)
assert(my_test.add_int_by_pointer(3, 4) == 7)
assert(my_test.add_int_by_reference(3, 4) == 7)
'''

#This is a Go test file that tests various functions that return different types of values. The file imports the "testing" and "github.com/stretchr/testify/assert" packages. The file defines a single test function, "Test()", that uses the "testing" package to test various code logic, using the "assert" package to check for expected results.

#The test function calls several functions that return different types of values, like integers, floats, and strings and check the returned values against expected results using the assert.Equal function. The function also tests the behavior of functions that take input values by value, pointer, and reference and check the returned values against expected results using the assert.Equal function.

#The functions being tested are:

#ReturnInt: which returns an int
#ReturnFloat: which returns a float32
#ReturnConstCharPtr: which returns a string
#ReturnIntByPointer: which returns a pointer to an int
#ReturnIntByReference: which returns a reference to an int
#AddIntByValue: which takes two integers as input and returns the sum
#AddIntByPointer: which takes two pointers to integers as input and returns the sum
#AddIntByReference: which takes two references to integers as input and returns the sum
test_go = '''\
package mytest

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	assert.Equal(t, ReturnInt(), 8, "should be the same.")
	assert.Equal(t, ReturnFloat(), float32(8), "should be the same.")
	assert.Equal(t, ReturnConstCharPtr(), "const char * -> string", "should be the same.")

	assert.Equal(t, *ReturnIntByPointer(), 9, "should be the same.")
	assert.Equal(t, *ReturnIntByReference(), 9, "should be the same.")
	
	assert.Equal(t, AddIntByValue(3, 4), 7, "should be the same.")
	a := int32(3)
	b := int32(4)
	assert.Equal(t, AddIntByPointer(&a, &b), 7, "should be the same.")
	assert.Equal(t, AddIntByReference(&a, &b), 7, "should be the same.")
}
'''

test_fsharp = '''\
    module MyTest

open NUnit.Framework

[<Test>]
let ``Test``() = 
    Assert.AreEqual(ReturnInt(), 8, "should be the same.")
    Assert.AreEqual(ReturnFloat(), 8.0f, "should be the same.")
    Assert.AreEqual(ReturnConstCharPtr(), "const char * -> string", "should be the same.")

    Assert.AreEqual(ReturnIntByPointer(), 9, "should be the same.")
    Assert.AreEqual(ReturnIntByReference(), 9, "should be the same.")

    Assert.AreEqual(AddIntByValue(3, 4), 7, "should be the same.")
    let a = 3
    let b = 4
    Assert.AreEqual(AddIntByPointer(a, b), 7, "should be the same.")
    Assert.AreEqual(AddIntByReference(a, b), 7, "should be the same.")
'''
#In F#, you don't need to use pointers to pass values by reference, you can use the & operator. Also, you don't need to dereference pointers before using them.
#Also, you don't need to import any package to perform assertions, you can use the NUnit.Framework module that comes with the NUnit package.