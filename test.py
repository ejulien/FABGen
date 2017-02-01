import lua
import python


def bind_math(gen):
	gen.begin_class('gs::Vector3')
	gen.bind_members('gs::Vector3', ['float x', 'float y', 'float z'])
	gen.bind_arithmetic_ops('gs::Vector3', ['+', '-', '*', '/', '+=', '-=', '*=', '/='], 'gs::Vector3', ['gs::Vector3 &'])
	gen.end_class('gs::Vector3')

def run_test(gen):
	gen.start('test')

	bind_math(gen)
	'''

	gen.bind_function_overloads('get', [('int', []), ('float', ['float']), ('int', ['float', 'int', 'int']), ('int', ['float', 'const char *', 'int']), ('void', ['float', 'int', 'float']), ('const char *', ['int', 'const char *']), ('int', ['int'])])

	gen.begin_class('base_class')
	gen.bind_constructor_overloads('base_class', [['float v0'], ['float v0', 'int v1'], ['float v0', 'float v1']])
	gen.end_class('base_class')

	base_class = gen.begin_class('base_class')
	gen.bind_constructor(base_class, ['float'])
	gen.bind_class_method(base_class, 'base_method', 'int', [])
	gen.bind_class_method(base_class, 'base_method_override', 'int', [])
	gen.end_class(base_class)

	derived_class = gen.begin_class('derived_class')
	gen.add_class_base(derived_class, 'base_class')
	gen.bind_constructor(derived_class, [])
	gen.bind_class_method(derived_class, 'derived_method', 'int', [])
	gen.bind_class_method(derived_class, 'base_method_override', 'int', [])
	gen.end_class(derived_class)
	'''

	gen.finalize()

	header, source = gen.get_output()

	print(header)
	print(source)


#run_test(lua.LuaGenerator())
run_test(python.PythonGenerator())
