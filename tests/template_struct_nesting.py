import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
template <typename T> struct enclosing_template {
	struct nested_struct {
		int v{9};
	};

	nested_struct n;
};

template <typename T> auto &GetNestedStruct(enclosing_template<T> &s) { return s.n; }
''', True, False)

	nested_struct = gen.begin_class('enclosing_template<int>::nested_struct', bound_name='nested_struct_int')
	gen.bind_constructor(nested_struct, [])
	gen.bind_member(nested_struct, 'int v')
	gen.end_class(nested_struct)

	enclosing_struct = gen.begin_class('enclosing_template<int>', bound_name='enclosing_template_int')
	gen.bind_constructor(enclosing_struct, [])
	gen.bind_member(enclosing_struct, 'enclosing_template<int>::nested_struct n')
	gen.end_class(enclosing_struct)

	gen.bind_function('GetNestedStruct<int>', 'enclosing_template<int>::nested_struct &', ['enclosing_template<int> &s'], bound_name='GetNestedStructInt')

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

#
s = my_test.enclosing_template_int()
n = my_test.GetNestedStructInt(s)
assert n.v == 9
'''

test_lua = '''\
my_test = require "my_test"

--
s = my_test.enclosing_template_int()
n = my_test.GetNestedStructInt(s)
assert(n.v == 9)
'''

test_go = """\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	s := NewEnclosingTemplateInt()
	n := GetNestedStructInt(s)
	assert.Equal(t, n.GetV(), int32(9), "should be the same.")
}
"""