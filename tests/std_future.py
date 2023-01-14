import lib.std
import lib.stl
import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
#include <future>
#include <thread>
#include <chrono>

static std::future<int> f;

void SetBarrierValue(std::promise<int> barrier) {
	std::this_thread::sleep_for(std::chrono::seconds(3));
    barrier.set_value(8);
}

std::thread work_thread;
 
std::future<int> GetFutureValue() {
    std::promise<int> barrier;
    std::future<int> future = barrier.get_future();
	work_thread = std::thread(SetBarrierValue, std::move(barrier));
	return std::move(future);
}
''', True, False)

	lib.stl.bind_future_T(gen, 'int', 'FutureInt')
	gen.bind_function('GetFutureValue', 'std::future<int>', [])

	gen.add_custom_free_code('work_thread.join();\n')
	gen.finalize()

	return gen.get_output()


test_python = '''\
import my_test

future = my_test.GetFutureValue()
assert future.valid() == True

future.wait()
assert future.get() == 8
'''

test_lua = '''\
my_test = require "my_test"

future = my_test.GetFutureValue()
assert(future:valid() == true)

future:wait()
assert(future:get() == 8)
'''

test_go = """\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	future := GetFutureValue()
	assert.True(t, future.Valid(), "should be the same.")

	future.Wait()
	assert.Equal(t, future.Get(), int32(8), "should be the same.")
}
"""

test_fsharp = '''\
    open MyTest

let future = getFutureValue()

if future.IsValid then
    future.Wait()
    let result = future.Get()
    printfn "Result: %d" result
    assert result = 8
else
    printfn "Invalid Future"
'''
#In this example, it calls the F# function "getFutureValue" which returns a future object.
#It then asserts that the "IsValid" function of the future object returns true. This verifies that the future object points to a valid future value.

#Then it calls the "Wait" function on the future object which will wait until the future value is ready.

#Once the future value is ready it assigns the result to the variable "result" and asserts that the result is equal to 8, which is the expected value.

#This test is checking if the future value is returned correctly and if the future object is valid before getting the value from it and if Wait function is working correctly.
