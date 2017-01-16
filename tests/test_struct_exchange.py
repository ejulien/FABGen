def bind_test(gen):
	gen.start('my_test')

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

bool test_simple_struct()
{
	return take_instance.v == return_instance.v;
}
''', True, False)

	gen.bind_class('simple_struct')

	gen.bind_function('return_simple_struct_by_value', 'simple_struct', [])
	gen.bind_function('return_simple_struct_by_pointer', 'simple_struct*', [])
	gen.bind_function('return_simple_struct_by_ref', 'simple_struct&', [])

	gen.bind_function('take_simple_struct_by_value', 'void', ['simple_struct'])
	gen.bind_function('take_simple_struct_by_pointer', 'void', ['simple_struct*'])
	gen.bind_function('take_simple_struct_by_ref', 'void', ['simple_struct&'])

	gen.bind_function('test_simple_struct', 'bool', [])

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

# take by value
s = my_test.return_simple_struct_by_value()
my_test.take_simple_struct_by_value(s)
expect_eq(my_test.test_simple_struct(), True)

s = my_test.return_simple_struct_by_pointer()
my_test.take_simple_struct_by_value(s)
expect_eq(my_test.test_simple_struct(), True)

s = my_test.return_simple_struct_by_ref()
my_test.take_simple_struct_by_value(s)
expect_eq(my_test.test_simple_struct(), True)

# ...
'''
