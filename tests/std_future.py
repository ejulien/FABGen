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
