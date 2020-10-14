import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : a(1) {}

	int set_a(int v) { return a = v; }

	bool set_a(int v0, int v1) {
		a = v0 + v1;
		return true;
	}

	int get_a() { return a; }

	static int get_static_int() { return 4; }

	int a;
};
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.bind_constructor(simple_struct, [])
	gen.bind_method_overloads(simple_struct, 'set_a', [
		('int', ['int v'], []),
		('bool', ['int v0', 'int v1'], [])
	])
	gen.bind_method(simple_struct, 'get_a', 'int', [])
	gen.bind_static_method(simple_struct, 'get_static_int', 'int', [])
	gen.end_class(simple_struct)

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
	s := NewSimpleStruct()

	assert.Equal(t, s.GetA(), int32(1), "should be the same.")
	assert.True(t, s.SetA1(8, 2), "should be the same.")

	assert.Equal(t, s.GetA(), int32(10), "should be the same.")

	assert.Equal(t, s.SetA0(9), int32(9), "should be the same.")
	assert.Equal(t, s.GetA(), int32(9), "should be the same.")

	assert.Equal(t, s.GetStaticInt(), int32(4), "should be the same.")
}
'''