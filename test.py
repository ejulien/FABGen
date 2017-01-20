import lua
import python


def run_test(gen):
	gen.start('test')

	base_class = gen.begin_class('base_class')
	gen.bind_class_constructor(base_class, ['int v0', 'int v1'])
	gen.end_class(base_class)

	'''
	base_class = gen.begin_class('base_class')
	gen.bind_class_method(base_class, 'base_method', 'int', [])
	gen.bind_class_method(base_class, 'base_method_override', 'int', [])
	gen.end_class(base_class)

	derived_class = gen.begin_class('derived_class')
	gen.add_class_base(derived_class, 'base_class')
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
