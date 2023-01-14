import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
int v{2};

struct simple_struct {
	int v{4};
};

simple_struct s;

namespace ns {
	int v{14};
	float u{7.f};
}
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_member(simple_struct, 'int v')
	gen.end_class(simple_struct)

	gen.bind_variables(['int v', 'simple_struct s'])
	gen.bind_variable('int ns::v', bound_name='w')

	gen.bind_variable('float ns::u')

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

assert my_test.v == 2
my_test.v = 5
assert my_test.v == 5

assert my_test.s.v == 4
my_test.s.v = 9
assert my_test.s.v == 9

assert my_test.w == 14

assert my_test.u == 7
'''

test_lua = '''\
my_test = require "my_test"

assert(my_test.v == 2)
my_test.v = 5
assert(my_test.v == 5)

assert(my_test.s.v == 4)
my_test.s.v = 9
assert(my_test.s.v == 9)

assert(my_test.w == 14)

assert(my_test.u == 7)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	assert.Equal(t, GetV(), int32(2), "should be the same.")
	SetV(int32(5))
	assert.Equal(t, GetV(), int32(5), "should be the same.")

	assert.Equal(t, GetS().GetV(), int32(4), "should be the same.")
	GetS().SetV(int32(9))
	assert.Equal(t, GetS().GetV(), int32(9), "should be the same.")

	assert.Equal(t, GetW(), int32(14), "should be the same.")

	assert.Equal(t, GetU(), float32(7), "should be the same.")
}
'''

test_fsharp = '''\
   open Xunit

[<Fact>]
let ``Test`` () =
    Assert.Equal(GetV(), 2, "should be the same.")
    SetV(5)
    Assert.Equal(GetV(), 5, "should be the same.")

    Assert.Equal(GetS().GetV(), 4, "should be the same.")
    GetS().SetV(9)
    Assert.Equal(GetS().GetV(), 9, "should be the same.")

    Assert.Equal(GetW(), 14, "should be the same.")

    Assert.Equal(GetU(), 7.0f, "should be the same.")

    '''
#In this version of the test, the open Xunit statement imports the necessary XUnit libraries. The test is decorated with [<Fact>] attribute, this means this function will be considered as a test function. The test function named "Test" uses the "Assert.Equal" method to make several equality assertions between the output of various functions (GetV(), SetV(), GetS().GetV(), GetS().SetV(), GetW(), and GetU()) and expected values (2, 5, 4, 9, 14, and 7.0f). If any of these assertions fail, the test will fail and the corresponding message "should be the same." will be printed.



    
    