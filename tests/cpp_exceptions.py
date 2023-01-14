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

#This is a Python code snippet that imports a module named "my_test" and runs a test to check whether a native exception is raised when the function "get_int" is called.

#The code initializes a variable "exception_raised" to False. Then it uses a try-except block to call the function "get_int" from the imported "my_test" module. If the function raises an exception, the code inside the except block will be executed and the "exception_raised" variable will be set to True.

#Finally, it asserts that the "exception_raised" variable is equal to True, meaning that the exception was raised as expected. This verifies that the function "get_int" raises an exception as it should.
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

exception_raised = false

if pcall(my_test.get_int) then
	assert(false) -- should not succeed, as an exception is thrown from C++
end
'''

test_go = '''\
package mytest
'''

test_fsharp = '''\
    let exceptionRaised = ref false

try
    myTest.getInt() // will raise an exception
    ()
with
    | _ -> exceptionRaised := true

Assert.IsTrue(!exceptionRaised)
'''
#In F#, you can use the "try-with" block to catch exceptions. The try block contains the code that may raise an exception, in this case the call to the "getInt()" function from the "myTest" module. If an exception is raised, the code inside the "with" block will be executed, and the exceptionRaised variable will be set to true.

#Finally, it asserts that the exceptionRaised variable is true, meaning that the exception was raised as expected. This verifies that the function "getInt()" raises an exception as it should.

#Note that in F#, you can use a reference cell to hold the value of a variable. This allows you to change the value of the variable inside the try-with block and use it outside the block.