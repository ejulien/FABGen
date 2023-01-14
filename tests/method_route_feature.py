import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	gen.insert_code('''
struct Object { int a{11}; };

int ObjectGet(Object *o, int v) { return o->a + v; }
\n''')

	obj = gen.begin_class('Object')

	def route_function(args):
		return 'ObjectGet(%s);' % (', '.join(args))

	gen.bind_constructor(obj, [])
	gen.bind_method(obj, 'Get', 'int', ['int v'], {'route': route_function})
	gen.end_class(obj)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

o = my_test.Object()
assert o.Get(4) == 15
'''

test_lua = '''\
my_test = require "my_test"

o = my_test.Object()
assert(o:Get(4) == 15)
'''

test_go = """\
package mytest

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	o := NewObject()
	assert.Equal(t, o.Get(4), int32(15), "should be the same.")
}
"""

test_fsharp = '''\
    module MyTest

open NUnit.Framework

[<Test>]
let ``Test``() = 
    let o = new Object()
    Assert.AreEqual(o.Get 4, 15, "should be the same.")
'''
#In F#, you can use the "new" keyword to create an instance of an object and call its methods using the "." operator.
#The test function creates an instance of an object, "o", using the "new Object()" function. Then it calls a method on the object, "Get()", passing in an int32 argument of 4.
#It uses the "Assert.AreEqual()" function to compare the returned value of the "Get()" method with the expected value of 15 and check if they are the same.

#This test case checks if the "Get()" method of the object is working correctly and returning the expected results when passed a specific argument.





