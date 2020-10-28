import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
struct SomeStruct {};
\n''', True, False)

	def get_repr(var_self, var_repr):
		return '%s = "repr!";\n' % var_repr

	some_struct = gen.begin_class('SomeStruct', features={'repr': get_repr})
	gen.bind_constructor(some_struct, [])
	gen.end_class(some_struct)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

o = my_test.SomeStruct()

assert repr(o) == "repr!"
'''

test_lua = '''\
my_test = require "my_test"

'''

test_go = '''\
package mytest

'''
