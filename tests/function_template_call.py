import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
template <typename T> T get() { return T(8); }
''', True, False)

	gen.bind_function('get<int>', 'int', [], bound_name='get_int')
	gen.bind_function('get<float>', 'float', [], bound_name='get_float')

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

assert my_test.get_int() == 8
assert my_test.get_float() == 8
'''

test_lua = '''\
my_test = require "my_test"

assert(my_test.get_int() == 8)
assert(my_test.get_float() == 8)
'''

test_go = """\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	assert.Equal(t, GetInt(), int32(8), "should be the same.")
	assert.Equal(t, GetFloat(), float32(8), "should be the same.")
}
"""