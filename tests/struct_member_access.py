import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : a(7), b(17.5f), c(true), d(9), text_field("some content") {}
	int a;
	float b;
	bool c;
	const int d;
	const char *text_field;
};

static simple_struct return_instance;
simple_struct *return_simple_struct_by_pointer() { return &return_instance; }
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_members(simple_struct, ['const char *text_field', 'int a', 'float b', 'bool c', 'const int d'])
	gen.end_class(simple_struct)

	gen.bind_function('return_simple_struct_by_pointer', 'simple_struct*', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

s = my_test.return_simple_struct_by_pointer()

assert s.a == 7
assert s.b == 17.5
assert s.c == True
assert s.d == 9
assert s.text_field == "some content"

s.a = -2
s.b = -4.5
s.c = False

assert s.a == -2
assert s.b == -4.5
assert s.c == False

s.a += 4
assert s.a == 2

# write to const member
write_to_const_failed = False
try:
	s.d = 12
except Exception:
	write_to_const_failed = True
assert write_to_const_failed == True

assert s.d == 9
'''

test_lua = '''\
my_test = require "my_test"

s = my_test.return_simple_struct_by_pointer()

assert(s.a == 7)
assert(s.b == 17.5)
assert(s.c == true)
assert(s.d == 9)
assert(s.text_field == "some content")

s.a = -2
s.b = -4.5
s.c = false

assert(s.a == -2)
assert(s.b == -4.5)
assert(s.c == false)

s.a = s.a + 4
assert(s.a == 2)

-- FIXME
-- write to const member
--write_to_const_failed = False
--try:
--	s.d = 12
--except Exception:
--	write_to_const_failed = True
--expect_eq(write_to_const_failed, True)

--expect_eq(s.d, 9)
'''

test_go = """\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	s := ReturnSimpleStructByPointer()

	assert.Equal(t, s.GetA(), int32(7), "should be the same.")
	assert.Equal(t, s.GetB(), float32(17.5), "should be the same.")
	assert.Equal(t, s.GetC(), true, "should be the same.")
	assert.Equal(t, s.GetD(), int32(9), "should be the same.")
	assert.Equal(t, s.GetTextField(), "some content", "should be the same.")

	s.SetA(-2)
	s.SetB(-4.5)
	s.SetC(false)

	assert.Equal(t, s.GetA(), int32(-2), "should be the same.")
	assert.Equal(t, s.GetB(), float32(-4.5), "should be the same.")
	assert.Equal(t, s.GetC(), false, "should be the same.")

	s.SetA(s.GetA() + 4)
	assert.Equal(t, s.GetA(), int32(2), "should be the same.")

	// # write to const member
	//  can't set d because it's a const
	// check if it didn't bind it
	_, writeToConstFailed := interface{}(s).(interface{ SetD() })
	assert.Equal(t, writeToConstFailed, false, "should be the same.")

	assert.Equal(t, s.GetD(), int32(9), "should be the same.")
}
"""
#In short, this test verifies that the struct has the correct initial values, can be modified, and that the constant members of the struct can't be modified.

test_fsharp = '''\
    open NUnit.Framework

[<Test>]
let ``test struct properties and methods`` () =
    let s = ReturnSimpleStructByPointer()

    Assert.AreEqual(s.A, 7)
    Assert.AreEqual(s.B, 17.5)
    Assert.AreEqual(s.C, true)
    Assert.AreEqual(s.D, 9)
    Assert.AreEqual(s.TextField, "some content")

    s.A <- -2
    s.B <- -4.5
    s.C <- false

    Assert.AreEqual(s.A, -2)
    Assert.AreEqual(s.B, -4.5)
    Assert.AreEqual(s.C, false)

    s.A <- s.A + 4
    Assert.AreEqual(s.A, 2)

    // check if it didn't bind it
    Assert.IsFalse(s.D.IsMutable)
'''
#The test function creates a variable s and assigns the result of calling ReturnSimpleStructByPointer() to it, which creates a new instance of a struct and returns its reference. Then it asserts that the values of the properties s.A, `s