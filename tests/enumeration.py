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