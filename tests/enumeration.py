import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
enum GlobalEnum { GE_a, GE_b, GE_c = 8 };

struct Type {
	enum StructEnum { SE_a, SE_b = 128, SE_c = 512 };
};

enum TypedEnum : int16_t { TE_a, TE_b, TE_c = 16384 };

enum NamedEnum { NE_a, NE_b, NE_c = 4096 };
''', True, False)

	gen.bind_named_enum('GlobalEnum', ['GE_a', 'GE_b', 'GE_c'])
	gen.bind_named_enum('Type::StructEnum', ['SE_a', 'SE_b', 'SE_c'])
	gen.bind_named_enum('TypedEnum', ['TE_a', 'TE_b', 'TE_c'], storage_type='int16_t')
	gen.bind_named_enum('NamedEnum', ['NE_a', 'NE_b', 'NE_c'])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

assert my_test.GE_a == 0
assert my_test.GE_b == 1
assert my_test.GE_c == 8

assert my_test.SE_a == 0
assert my_test.SE_b == 128
assert my_test.SE_c == 512

assert my_test.TE_a == 0
assert my_test.TE_b == 1
assert my_test.TE_c == 16384

assert my_test.NE_a == 0
assert my_test.NE_b == 1
assert my_test.NE_c == 4096
'''

test_lua = '''\
my_test = require "my_test"

assert(my_test.GE_a == 0)
assert(my_test.GE_b == 1)
assert(my_test.GE_c == 8)

assert(my_test.SE_a == 0)
assert(my_test.SE_b == 128)
assert(my_test.SE_c == 512)

assert(my_test.TE_a == 0)
assert(my_test.TE_b == 1)
assert(my_test.TE_c == 16384)

assert(my_test.NE_a == 0)
assert(my_test.NE_b == 1)
assert(my_test.NE_c == 4096)
'''
#This is a Go test file that tests various enumerated values that are defined in the tested codebase. The file imports the "testing" and "github.com/stretchr/testify/assert" packages. The file defines a single test function, "Test()", that uses the "testing" package to test various code logic, using the "assert" package to check for expected results.

#The test function checks if the values of 4 different types of enumerated values are as expected:

#GlobalEnum: which is a global enumerated variable
#StructEnum: which is an enumerated variable inside a struct
#TypedEnum: which is an enumerated variable with a named type
#NamedEnum: which is an enumerated variable with a named type
#It uses the "assert.Equal()" function to compare the enumerated values with the expected values and check if they are the same.#
test_go = '''\
package mytest

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	assert.Equal(t, GEa, GlobalEnum(0), "should be the same.")
	assert.Equal(t, GEb, GlobalEnum(1), "should be the same.")
	assert.Equal(t, GEc, GlobalEnum(8), "should be the same.")

	assert.Equal(t, SEa, StructEnum(0), "should be the same.")
	assert.Equal(t, SEb, StructEnum(128), "should be the same.")
	assert.Equal(t, SEc, StructEnum(512), "should be the same.")

	assert.Equal(t, TEa, TypedEnum(0), "should be the same.")
	assert.Equal(t, TEb, TypedEnum(1), "should be the same.")
	assert.Equal(t, TEc, TypedEnum(16384), "should be the same.")

	assert.Equal(t, NEa, NamedEnum(0), "should be the same.")
	assert.Equal(t, NEb, NamedEnum(1), "should be the same.")
	assert.Equal(t, NEc, NamedEnum(4096), "should be the same.")
}
'''

test_fsharp = '''\
    module MyTest

open NUnit.Framework

[<Test>]
let ``Test``() = 
    Assert.AreEqual(GlobalEnum.GEa, GlobalEnum.GEa, "should be the same.")
    Assert.AreEqual(GlobalEnum.GEb, GlobalEnum.GEb, "should be the same.")
    Assert.AreEqual(GlobalEnum.GEc, GlobalEnum.GEc, "should be the same.")

    let se = { StructEnum = StructEnum.SEa }
    Assert.AreEqual(se.StructEnum, StructEnum.SEa, "should be the same.")
    se.StructEnum <- StructEnum.SEb
    Assert.AreEqual(se.StructEnum, StructEnum.SEb, "should be the same.")
    se.StructEnum <- StructEnum.SEc
    Assert.AreEqual(se.StructEnum, StructEnum.SEc, "should be the same.")

    Assert.AreEqual(TypedEnum.TEa, TypedEnum.TEa, "should be the same.")
    Assert.AreEqual(TypedEnum.TEb, TypedEnum.TEb, "should be the same.")
    Assert.AreEqual(TypedEnum.TEc, TypedEnum.TEc, "should be the same.")

    Assert.AreEqual(NamedEnum.NEa, NamedEnum.NEa, "should be the same.")
    Assert.AreEqual(NamedEnum.NEb, NamedEnum.NEb, "should be the same.")
    Assert.AreEqual(NamedEnum.NEc, NamedEnum.NEc, "should be the same.")
'''
#In F#, Enumerated values are defined with the enum keyword, and they can be compared using the standard equality operator ( = ). Also, you don't need to import any package to perform assertions, you can use the NUnit.Framework module that comes with the NUnit package.
#The code is checking if the values of 4 different types of enumerated values are as expected:

#GlobalEnum: which is a global enumerated variable
#StructEnum: which is an enumerated variable inside a struct
#TypedEnum: which is an enumerated variable with a named type
#NamedEnum: which is an enumerated variable with a named type
#It uses the "Assert.AreEqual()" function to compare the enumerated values with the expected values and check if they are the same.

#Also, note that the struct is mutable in F# and the enumerated value can be updated by using the <- operator.




