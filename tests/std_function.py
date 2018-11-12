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

static std::function<int(int)> int_int_function;

void SetIntIntFunction(std::function<int(int)> f) { int_int_function = f; }
int InvokeIntIntFunction(int v) { return int_int_function(v); }
''', True, False)

	lib.stl.bind_function_T(gen, 'std::function<void()>', 'VoidCb')
	gen.bind_function('SetSimpleVoidFunction', 'void', ['std::function<void()> f'])
	gen.bind_function('InvokeSimpleVoidFunction', 'void', [])

	lib.stl.bind_function_T(gen, 'std::function<int(int)>', 'IntCbTakingInt')
	gen.bind_function('SetIntIntFunction', 'void', ['std::function<int(int)> f'])
	gen.bind_function('InvokeIntIntFunction', 'int', ['int v'])

	gen.finalize()

	return gen.get_output()


test_python = '''\
import my_test

def simple_void_function():
    print("void function called!")

my_test.SetSimpleVoidFunction(simple_void_function)
my_test.InvokeSimpleVoidFunction()

def int_int_function(v):
    return v * 3

my_test.SetIntIntFunction(int_int_function)
r = my_test.InvokeIntIntFunction(5)

assert r == 15
'''

test_lua = '''\
my_test = require "my_test"

function simple_void_function()
    print('void function called!')
end

my_test.SetSimpleVoidFunction(simple_void_function)
my_test.InvokeSimpleVoidFunction()

function int_int_function(v)
    return v * 3
end

my_test.SetIntIntFunction(int_int_function)
r = my_test.InvokeIntIntFunction(5)

assert(r == 15)
'''
