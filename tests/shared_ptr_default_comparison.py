# Although both proxy objects are different they resolve to the same underlying C++ shared_ptr and should test as equal.

import lib

from lib.stl import SharedPtrProxyFeature


def bind_test(gen):
	gen.start('my_test')
	gen.add_include('memory', True)

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
std::shared_ptr<int> obj0(new int(2)), obj1(new int(3)), obj2(obj0);

std::shared_ptr<int> &get_obj0() { return obj0; }
std::shared_ptr<int> &get_obj1() { return obj1; }
std::shared_ptr<int> &get_obj2() { return obj2; }
''', True, False)

	shared_ptr_int_conv = gen.begin_class('std::shared_ptr<int>', bound_name='sint', features={'proxy': SharedPtrProxyFeature(gen.get_conv('int'))})
	gen.end_class(shared_ptr_int_conv)

	gen.bind_function('get_obj0', 'std::shared_ptr<int> &', [])
	gen.bind_function('get_obj1', 'std::shared_ptr<int> &', [])
	gen.bind_function('get_obj2', 'std::shared_ptr<int> &', [])

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

d = my_test.get_obj2()

assert a == d
'''

test_lua = '''\
my_test = require "my_test"

a = my_test.get_obj0()
b = my_test.get_obj0()

assert(a == b)

c = my_test.get_obj1()

assert(a ~= c)
assert(b ~= c)

d = my_test.get_obj2()

assert(a == d)
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

	assert.True(t, a.Equal(b), "should be the equal.")

	c := GetObj1()

	assert.True(t, !a.Equal(c), "should be different.")
	assert.True(t, !b.Equal(c), "should be different.")

	d := GetObj2()

	assert.True(t, a.Equal(d), "should be the equal.")
}
'''