import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
int get_int() { return 8; }

int get() { return 0; }
int get(int v) { return v / 2; }
int get(int v, int k) { return v * k; }
int get(int v, int k, int b) { return v * k + b; }

static int global_int = 0;

void set_global_int() { global_int = 8; }
int get_global_int() { return global_int; }

int get_global_int_multiplied(int k = 5) { return 3 * k; }
''', True, False)

	gen.bind_function('get_int', 'int', [])
	gen.bind_function_overloads('get', [
		('int', [], []),
		('int', ['int v'], []),
		('int', ['int v', 'int k'], []),
		('int', ['int v', 'int k', 'int b'], [])
	])

	gen.bind_function('set_global_int', 'void', [])
	gen.bind_function('get_global_int', 'int', [])

	gen.bind_function('get_global_int_multiplied', 'int', ['?int k'])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

assert my_test.get_int() == 8

assert my_test.get_global_int() == 0
my_test.set_global_int()
assert my_test.get_global_int() == 8

# overload
assert my_test.get() == 0
assert my_test.get(2) == 1
assert my_test.get(4, 3) == 12
assert my_test.get(4, 3, 2) == 14

# optional argument
assert my_test.get_global_int_multiplied() == 15
assert my_test.get_global_int_multiplied(2) == 6
'''

test_lua = '''\
my_test = require "my_test"

assert(my_test.get_int() == 8)

assert(my_test.get_global_int() == 0)
my_test.set_global_int()
assert(my_test.get_global_int() == 8)

-- overload
assert(my_test.get() == 0)
assert(my_test.get(2) == 1)
assert(my_test.get(4, 3) == 12)
assert(my_test.get(4, 3, 2) == 14)

-- optional argument
assert(my_test.get_global_int_multiplied() == 15)
assert(my_test.get_global_int_multiplied(2) == 6)
'''

test_go = '''\
package harfang

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	assert.Equal(t, GetInt(), 8, "should be the same.")

	assert.Equal(t, GetGlobalInt(), 0, "should be the same.")

	SetGlobalInt()
	assert.Equal(t, GetGlobalInt(), 8, "should be the same.")

	// overload
	assert.Equal(t, Get0(), 0, "should be the same.")
	assert.Equal(t, Get1(2), 1, "should be the same.")
	assert.Equal(t, Get2(4, 3), 12, "should be the same.")
	assert.Equal(t, Get3(4, 3, 2), 14, "should be the same.")

	// optional argument
	assert.Equal(t, GetGlobalIntMultiplied0(), 15, "should be the same.")
	assert.Equal(t, GetGlobalIntMultiplied1(2), 6, "should be the same.")
}
'''