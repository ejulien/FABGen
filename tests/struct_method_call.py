import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : a(1) {}
	simple_struct(int v) : a(v) {}

	int set_a(int v) { return a = v; }

	bool set_a(int v0, int v1) {
		a = v0 + v1;
		return true;
	}

	int get_a() { return a; }

	static int get_static_int() { return 4; }

	int a;
};

void get_modify_arg_out(simple_struct &v, simple_struct k=simple_struct()) { v.a = 3 * k.a + v.a; }

struct simple_struct2 {
	simple_struct2() : a(1) {}
	simple_struct2(int v) : a(v) {}
	simple_struct2(simple_struct v) : a(v.a) {}
	int a;
};
void get_modify_arg_out2(simple_struct2 &v, simple_struct k=simple_struct()) { v.a = 3 * k.a + v.a; }

''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_constructor_overloads(simple_struct, [
		([], {"bound_name": "SimplestConstructor"}),
		(['int v'], [])
	])
	gen.bind_method_overloads(simple_struct, 'set_a', [
		('int', ['int v'], []),
		('bool', ['int v0', 'int v1'], [])
	])
	gen.bind_method(simple_struct, 'get_a', 'int', [])
	gen.bind_static_method(simple_struct, 'get_static_int', 'int', [])
	gen.end_class(simple_struct)
	
	gen.bind_function('get_modify_arg_out', 'void', ['simple_struct &v', '?simple_struct k'], {'arg_out': ['v']})
	
	simple_struct2 = gen.begin_class('simple_struct2')
	gen.bind_constructor_overloads(simple_struct2, [
		([], []),
		(['int v'], []),
		(['simple_struct v'], {"bound_name": "WithOtherStruct"})
	])
	gen.bind_members(simple_struct2, ['int a'])
	gen.end_class(simple_struct2)

	gen.bind_function('get_modify_arg_out2', 'void', ['simple_struct2 &v', '?simple_struct k'], {'arg_out': ['v']})

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

s = my_test.simple_struct()

assert s.get_a() == 1
assert s.set_a(8, 2) == True

assert s.get_a() == 10

assert s.set_a(9) == 9
assert s.get_a() == 9

assert s.get_static_int() == 4
'''

test_lua = '''\
my_test = require "my_test"

s = my_test.simple_struct()

assert(s:get_a() == 1)
assert(s:set_a(8, 2) == true)

assert(s:get_a() == 10)

assert(s:set_a(9) == 9)
assert(s:get_a() == 9)

assert(s.get_static_int() == 4)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	s := NewSimpleStructSimplestConstructor()

	assert.Equal(t, s.GetA(), int32(1), "should be the same.")
	assert.True(t, s.SetAWithV0V1(8, 2), "should be the same.")

	assert.Equal(t, s.GetA(), int32(10), "should be the same.")

	assert.Equal(t, s.SetA(9), int32(9), "should be the same.")
	assert.Equal(t, s.GetA(), int32(9), "should be the same.")

	assert.Equal(t, s.GetStaticInt(), int32(4), "should be the same.")

	sOut := GetModifyArgOut()
	assert.Equal(t, sOut.GetA(), int32(4), "should be the same.")

	sOut = GetModifyArgOutWithK(NewSimpleStructWithV(5))
	assert.Equal(t, sOut.GetA(), int32(16), "should be the same.")

	s2 := NewSimpleStruct2WithOtherStruct(sOut)
	assert.Equal(t, s2.GetA(), int32(16), "should be the same.")

	sOut2 := GetModifyArgOut2()
	assert.Equal(t, sOut2.GetA(), int32(4), "should be the same.")

	sOut2 = GetModifyArgOut2WithK(s)
	assert.Equal(t, sOut2.GetA(), int32(28), "should be the same.")
}
'''

test_fsharp = '''\
    open NUnit.Framework

[<Test>]
let ``test struct properties and methods`` () =
    let s = NewSimpleStructSimplestConstructor()

    Assert.AreEqual(s.A, 1)
    Assert.IsTrue(s.SetAWithV0V1(8, 2))

    Assert.AreEqual(s.A, 10)

    Assert.AreEqual(s.SetA(9), 9)
    Assert.AreEqual(s.A, 9)

    Assert.AreEqual(s.StaticInt, 4)

    let sOut = GetModifyArgOut()
    Assert.AreEqual(sOut.A, 4)

    let sOut = GetModifyArgOutWithK(NewSimpleStructWithV(5))
    Assert.AreEqual(sOut.A, 16)

    let s2 = NewSimpleStruct2WithOtherStruct(sOut)
    Assert.AreEqual(s2.A, 16)

    let sOut2 = GetModifyArgOut2()
    Assert.AreEqual(sOut2.A, 4)

    let sOut2 = GetModifyArgOut2WithK(s)
    Assert.AreEqual(sOut2.A, 28)
'''
#The test function creates a variable s and assigns the result of calling NewSimpleStructSimplestConstructor() to it, which creates a new instance of a struct with default values. Then it asserts that the value of the property s.A match the expected value 1 using the Assert.AreEqual() function.

#It then calls the method s.SetAWithV0V1(8, 2) on the struct s to change the value of its property A and asserts that the returned value is true using the Assert.IsTrue() function. It asserts that the new value of the property s.A match the expected value 10 using the Assert.AreEqual() function.

#It then calls the method s.SetA(9) on the struct s to change the value of its property A and asserts that the returned value is 9 using the Assert.AreEqual() function. It asserts that the new value of the property s.A match the expected value 9 using the Assert.AreEqual() function.