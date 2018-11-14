import lib.std
import lib.stl
import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.insert_code('''\
#include <functional>

static std::function<void()> simple_void_function;

void SetSimpleVoidFunction(std::function<void()> f) { simple_void_function = f; }
void InvokeSimpleVoidFunction() {  simple_void_function(); }

static std::function<int(int, int &, int *)> compute_function;

void SetComputeFunction(std::function<int(int, int &, int *)> f) { compute_function = f; }
int InvokeComputeFunction(int v, int m, int c) { return compute_function(v, m, &c); }
''', True, False)

	lib.stl.bind_function_T(gen, 'std::function<void()>', 'VoidCb')
	gen.bind_function('SetSimpleVoidFunction', 'void', ['std::function<void()> f'])
	gen.bind_function('InvokeSimpleVoidFunction', 'void', [])

	lib.stl.bind_function_T(gen, 'std::function<int(int, int &, int *)>')
	gen.bind_function('SetComputeFunction', 'void', ['std::function<int(int, int &, int *)> f'])
	gen.bind_function('InvokeComputeFunction', 'int', ['int v', 'int m', 'int c'])

	gen.finalize()

	return gen.get_output()


test_python = '''\
import my_test

def simple_void_function():
	print("void function called!")

my_test.SetSimpleVoidFunction(simple_void_function)
my_test.InvokeSimpleVoidFunction()

def compute_function(v, m, c):
	return v * m + c

my_test.SetComputeFunction(compute_function)
r = my_test.InvokeComputeFunction(5, 3, 4)

assert r == 19
'''

test_lua = '''\
my_test = require "my_test"

function simple_void_function()
	print('void function called!')
end

my_test.SetSimpleVoidFunction(simple_void_function)
my_test.InvokeSimpleVoidFunction()

function compute_function(v, m, c)
	return v * m + c
end

my_test.SetComputeFunction(compute_function)
r = my_test.InvokeComputeFunction(5, 3, 4)

assert(r == 19)
'''
