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