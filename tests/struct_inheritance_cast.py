import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct base_class {
};

struct derived_class : base_class {
	int u{7};
};

static derived_class __b;

static base_class &GetBaseClass() {  return __b; }

''', True, False)

	base_conv =	gen.begin_class('base_class')
	gen.bind_constructor(base_conv, [])
	gen.end_class(base_conv)

	derived_conv = gen.begin_class('derived_class')
	gen.add_base(derived_conv, base_conv)
	gen.bind_constructor(derived_conv, [])
	gen.bind_members(derived_conv, ['int u'])
	gen.end_class(derived_conv)

	gen.bind_function('GetBaseClass', 'base_class &', [])

	gen.finalize()

	return gen.get_output()


test_python = '''\
import my_test

a = my_test.GetBaseClass()
b = my_test.Cast_base_class_To_derived_class(a)
assert b.u == 7
'''

test_lua = '''\
my_test = require "my_test"

a = my_test.GetBaseClass()
b = my_test.Cast_base_class_To_derived_class(a)
assert(b.u == 7)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	a := GetBaseClass()
	b := CastBaseClassToDerivedClass(a)
	assert.Equal(t, b.GetU(), int32(7), "should be the same.")
}
'''

test_fsharp = '''\
    open NUnit.Framework

[<Test>]
let ``test class casting`` () =
    let a = GetBaseClass()
    let b = CastBaseClassToDerivedClass(a)
    Assert.AreEqual(b.U, 7)
'''
#The test function creates a variable a and assigns the result of calling GetBaseClass() to it. Then it creates a variable b and assigns the result of calling CastBaseClassToDerivedClass(a) to it. CastBaseClassToDerivedClass(a) takes a variable of a base class and casts it to a derived class. After that, it uses the Assert.AreEqual() function to check that the value of the property b.U is equal to 7.

#It's important to note that in F#, class casting is done by using the :> operator and it's not a function.