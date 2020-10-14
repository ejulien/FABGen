# this test is incomplete and only ensures the output module builds

import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	gen.bind_extern_type('SomeExternType')
	gen.bind_extern_type('nspace::SomeOtherExternType', 'BoundAsThis')  # mostly for documentation purpose (so that extern types display the proper bound name)
	gen.bind_extern_type('nspace::YetAnotherExternType', 'WithThisBoundName', 'TheModule')  # mostly for documentation purpose (so that extern types display the proper bound name)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test
'''

test_lua = '''\
my_test = require "my_test"
'''

test_go = '''\
package mytest
'''