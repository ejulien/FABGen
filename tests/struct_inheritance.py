import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct base_class {
	int base_method() { return 4; }
	int base_method_override() { return 4; }
	virtual int virtual_method() { return 6; }
	int u{6};
	static int v;
	int override{4};
	static int static_override;
};

int base_class::v{7};
int base_class::static_override{1};

struct derived_class : base_class {
	int derived_method() { return 8; }
	int base_method_override() { return 8; }
	int virtual_method() override { return 9; }
	int override{12};
	static int static_override;
};

int derived_class::static_override{42};

int read_virtual_method_through_base_class(base_class &o) {
	return o.virtual_method();
}
''', True, False)

	base_conv =	gen.begin_class('base_class')
	gen.bind_constructor(base_conv, [])
	gen.bind_method(base_conv, 'base_method', 'int', [])
	gen.bind_method(base_conv, 'base_method_override', 'int', [])
	gen.bind_method(base_conv, 'virtual_method', 'int', [])
	gen.bind_members(base_conv, ['int u', 'int override'])
	gen.bind_static_members(base_conv, ['int v', 'int static_override'])
	gen.end_class(base_conv)

	derived_conv = gen.begin_class('derived_class')
	gen.add_base(derived_conv, base_conv)
	gen.bind_constructor(derived_conv, [])
	gen.bind_method(derived_conv, 'derived_method', 'int', [])
	gen.bind_method(derived_conv, 'base_method_override', 'int', [])
	gen.bind_members(derived_conv, ['int override'])
	gen.bind_static_members(derived_conv, ['int static_override'])
	gen.end_class(derived_conv)

	gen.bind_function('read_virtual_method_through_base_class', 'int', ['base_class &o'])

	gen.finalize()

	return gen.get_output()


test_python = '''\
import my_test

base = my_test.base_class()
assert base.base_method() == 4
assert base.base_method_override() == 4

derived = my_test.derived_class()
assert derived.base_method() == 4  # can still access base class
assert derived.derived_method() == 8  # can access its own methods
assert derived.base_method_override() == 8  # properly overshadows redeclared base methods

# argument casting through inheritance tree
assert my_test.read_virtual_method_through_base_class(base) == 6
assert my_test.read_virtual_method_through_base_class(derived) == 9

# member access through inheritance tree
assert base.u == 6
assert derived.u == 6  # can access base class member
assert base.v == 7
assert derived.v == 7  # can access base class static member

assert base.override == 4
assert base.static_override == 1
assert derived.override == 12  # member overshadowing
assert derived.static_override == 42  # static member overshadowing

assert my_test.base_class.v == 7
assert my_test.derived_class.v == 7
assert my_test.base_class.static_override == 1
assert my_test.derived_class.static_override == 42
'''

test_lua = '''\
my_test = require "my_test"

base = my_test.base_class()
assert(base:base_method() == 4)
assert(base:base_method_override() == 4)

derived = my_test.derived_class()
assert(derived:base_method() == 4)  -- can still access base class
assert(derived:derived_method() == 8)  -- can access its own methods
assert(derived:base_method_override() == 8)  -- properly overshadows redeclared base methods

-- argument casting through inheritance tree
assert(my_test.read_virtual_method_through_base_class(base) == 6)
assert(my_test.read_virtual_method_through_base_class(derived) == 9)

-- member access through inheritance tree
assert(base.u == 6)
assert(derived.u == 6)  -- can access base class member
assert(base.v == 7)
assert(derived.v == 7)  -- can access base class static member

assert(base.override == 4)
assert(base.static_override == 1)
assert(derived.override == 12)  -- member overshadowing
assert(derived.static_override == 42)  -- static member overshadowing

assert(my_test.base_class.v == 7)
assert(my_test.derived_class.v == 7)
assert(my_test.base_class.static_override == 1)
assert(my_test.derived_class.static_override == 42)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	base := NewBaseClass()
	assert.Equal(t, base.BaseMethod(), int32(4), "should be the same.")
	assert.Equal(t, base.BaseMethodOverride(), int32(4), "should be the same.")

	derived := NewDerivedClass()
	assert.Equal(t, derived.BaseMethod(), int32(4), "should be the same.")         // can still access base class
	assert.Equal(t, derived.DerivedMethod(), int32(8), "should be the same.")      // can access its own methods
	assert.Equal(t, derived.BaseMethodOverride(), int32(8), "should be the same.") // properly overshadows redeclared base methods

	// argument casting through inheritance tree
	assert.Equal(t, ReadVirtualMethodThroughBaseClass(base), int32(6), "should be the same.")
	assert.Equal(t, ReadVirtualMethodThroughBaseClass(CastDerivedClassToBaseClass(derived)), int32(9), "should be the same.")

	// member access through inheritance tree
	assert.Equal(t, base.GetU(), int32(6), "should be the same.")
	assert.Equal(t, derived.GetU(), int32(6), "should be the same.") // can access base class member
	assert.Equal(t, base.GetV(), int32(7), "should be the same.")
	assert.Equal(t, derived.GetV(), int32(7), "should be the same.") // can access base class static member

	assert.Equal(t, base.GetOverride(), int32(4), "should be the same.")
	assert.Equal(t, base.GetStaticOverride(), int32(1), "should be the same.")
	assert.Equal(t, derived.GetOverride(), int32(12), "should be the same.")       // member overshadowing
	assert.Equal(t, derived.GetStaticOverride(), int32(42), "should be the same.") // static member overshadowing

	assert.Equal(t, BaseClassGetV(), int32(7), "should be the same.")
	assert.Equal(t, DerivedClassGetV(), int32(7), "should be the same.")
	assert.Equal(t, BaseClassGetStaticOverride(), int32(1), "should be the same.")
	assert.Equal(t, DerivedClassGetStaticOverride(), int32(42), "should be the same.")
}
'''