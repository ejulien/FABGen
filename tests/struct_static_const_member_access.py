import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	int v{3};
	static int i;
	static const char *s;
};

int simple_struct::i = 5;
const char *simple_struct::s = "some string";
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_constructor(simple_struct, [])
	gen.bind_member(simple_struct, 'int v')
	gen.bind_static_member(simple_struct, 'int i')
	gen.bind_static_member(simple_struct, 'const char *s')
	gen.end_class(simple_struct)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

v = my_test.simple_struct()
assert v.v == 3

assert my_test.simple_struct.i == 5
assert my_test.simple_struct.s == "some string"
'''

test_lua = '''\
my_test = require "my_test"

v = my_test.simple_struct()
assert(v.v == 3)

assert(my_test.simple_struct.i == 5)
assert(my_test.simple_struct.s == "some string")
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	v := NewSimpleStruct()
	assert.Equal(t, v.GetV(), int32(3), "should be the same.")

	assert.Equal(t, SimpleStructGetI(), int32(5), "should be the same.")
	assert.Equal(t, SimpleStructGetS(), "some string", "should be the same.")
}
'''