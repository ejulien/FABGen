import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	gen.insert_code('''
int *return_nullptr() { return nullptr; }
''')
	gen.bind_function('return_nullptr', 'int *', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

v = my_test.return_nullptr()
assert v is None
'''

test_lua = '''\
my_test = require "my_test"

v = my_test.return_nullptr()
assert(v == nil)
'''

test_go = '''\
package mytest

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {	
	v := ReturnNullptr()
	assert.Nil(t, v, "should be nil.")
}
'''