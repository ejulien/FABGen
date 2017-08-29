import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_binding_code('''\
int get_int() {
	throw 0;
	return 8;
}
''')
	gen.bind_function('get_int', 'int', [], {'exception': 'native exception raised'})

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

exception_raised = False

try:
	my_test.get_int()  # will raise a native exception
except:
	exception_raised = True

assert exception_raised == True
'''

test_lua = '''\
my_test = require "my_test"
'''
