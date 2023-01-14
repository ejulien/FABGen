import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : a(3), b(11), c(1) {}
	unsigned int a:2;
	unsigned int b:4;
	unsigned int c:2;
};
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_constructor(simple_struct, [])
	gen.bind_members(simple_struct, ['int a:', 'int b:', 'int c:'])
	gen.end_class(simple_struct)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

s = my_test.simple_struct()

assert s.a == 3
assert s.b == 11
assert s.c == 1

s.a = 1
s.b = 7
s.c = 2

assert s.a == 1
assert s.b == 7
assert s.c == 2
'''

test_lua = '''\
my_test = require "my_test"

s = my_test.simple_struct()

assert(s.a, 3)
assert(s.b, 11)
assert(s.c, 1)

s.a = 1
s.b = 7
s.c = 2

assert(s.a, 1)
assert(s.b, 7)
assert(s.c, 2)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	s := NewSimpleStruct()

	assert.Equal(t, s.GetA(), int32(3), "should be the same.")
	assert.Equal(t, s.GetB(), int32(11), "should be the same.")
	assert.Equal(t, s.GetC(), int32(1), "should be the same.")

	s.SetA(1)
	s.SetB(7)
	s.SetC(2)

	assert.Equal(t, s.GetA(), int32(1), "should be the same.")
	assert.Equal(t, s.GetB(), int32(7), "should be the same.")
	assert.Equal(t, s.GetC(), int32(2), "should be the same.")
}
'''

test_fsharp = '''\
    open NUnit.Framework

[<Test>]
let ``test simple struct`` () =
    let s = SimpleStruct()

    // Check initial values
    Assert.AreEqual(s.A, 3)
    Assert.AreEqual(s.B, 11)
    Assert.AreEqual(s.C, 1)

    // Update values
    s.A <- 1
    s.B <- 7
    s.C <- 2

    // Check updated values
    Assert.AreEqual(s.A, 1)
    Assert.AreEqual(s.B, 7)
    Assert.AreEqual(s.C, 2)
'''
#It's important to note that in F# properties are usually defined as member variables and accessed directly, so you don't need to define getter/setter methods like in Go.
#Also, the test function is marked with the [<Test>] attribute to indicate that it is a test function, and the Assert.AreEqual() function from the NUnit.Framework library is used to check that the values match the expected values.

#Please note that this is just an example, and you'll need to adjust the code to match the design of the actual struct you're testing.
