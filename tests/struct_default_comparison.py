# Although both proxy objects are different they resolve to the same underlying C++ object and should test as equal.

import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {};

simple_struct obj0, obj1;

simple_struct &get_obj0() { return obj0; }
simple_struct &get_obj1() { return obj1; }
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.end_class(simple_struct)

	gen.bind_function('get_obj0', 'simple_struct &', [])
	gen.bind_function('get_obj1', 'simple_struct &', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

a = my_test.get_obj0()
b = my_test.get_obj0()

assert a == b

c = my_test.get_obj1()

assert a != c
assert b != c
'''

test_lua = '''\
my_test = require "my_test"

a = my_test.get_obj0()
b = my_test.get_obj0()

assert(a == b)

c = my_test.get_obj1()

assert(a ~= c)
assert(b ~= c)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	a := GetObj0()
	b := GetObj0()

	assert.Equal(t, a, b, "should be the same.")

	c := GetObj1()

	assert.NotEqual(t, a, c, "should not be the same.")
	assert.NotEqual(t, b, c, "should not be the same.")
}
'''