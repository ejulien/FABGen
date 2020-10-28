import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct simple_struct {
	simple_struct() : v(7) {}
	int v;
};

static simple_struct return_instance;

simple_struct return_simple_struct_by_value() { return return_instance; }
simple_struct *return_simple_struct_by_pointer() { return &return_instance; }
simple_struct &return_simple_struct_by_ref() { return return_instance; }

static simple_struct take_instance;

void take_simple_struct_by_value(simple_struct v) { take_instance.v = -7; take_instance = v; }
void take_simple_struct_by_pointer(simple_struct *v) { take_instance.v = -7; take_instance = *v; }
void take_simple_struct_by_ref(simple_struct &v) { take_instance.v = -7; take_instance = v; }

bool test_simple_struct() {
	return take_instance.v == return_instance.v;
}
''', True, False)

	simple_struct = gen.begin_class('simple_struct')
	gen.end_class(simple_struct)

	gen.bind_function('return_simple_struct_by_value', 'simple_struct', [])
	gen.bind_function('return_simple_struct_by_pointer', 'simple_struct*', [])
	gen.bind_function('return_simple_struct_by_ref', 'simple_struct&', [])

	gen.bind_function('take_simple_struct_by_value', 'void', ['simple_struct s'])
	gen.bind_function('take_simple_struct_by_pointer', 'void', ['simple_struct *s'])
	gen.bind_function('take_simple_struct_by_ref', 'void', ['simple_struct &s'])

	gen.bind_function('test_simple_struct', 'bool', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

# take by value
s = my_test.return_simple_struct_by_value()
my_test.take_simple_struct_by_value(s)
assert my_test.test_simple_struct() == True

s = my_test.return_simple_struct_by_pointer()
my_test.take_simple_struct_by_value(s)
assert my_test.test_simple_struct() == True

s = my_test.return_simple_struct_by_ref()
my_test.take_simple_struct_by_value(s)
assert my_test.test_simple_struct() == True
'''


test_lua = '''\
my_test = require "my_test"

-- take by value
s = my_test.return_simple_struct_by_value()
my_test.take_simple_struct_by_value(s)
assert(my_test.test_simple_struct() == true)

s = my_test.return_simple_struct_by_pointer()
my_test.take_simple_struct_by_value(s)
assert(my_test.test_simple_struct() == true)

s = my_test.return_simple_struct_by_ref()
my_test.take_simple_struct_by_value(s)
assert(my_test.test_simple_struct() == true)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	// take by value
	s := ReturnSimpleStructByValue()
	TakeSimpleStructByValue(s)
	assert.True(t, TestSimpleStruct(), "should be true.")

	sp := ReturnSimpleStructByPointer()
	TakeSimpleStructByPointer(sp)
	assert.True(t, TestSimpleStruct(), "should be true.")

	sr := ReturnSimpleStructByRef()
	TakeSimpleStructByRef(sr)
	assert.True(t, TestSimpleStruct(), "should be true.")
}
'''