import lua
import python


def bind_math(gen):
	gen.decl_class('gs::Color')
	gen.decl_class('gs::Vector3')
	gen.decl_class('gs::Vector4')
	gen.decl_class('gs::Matrix3')
	gen.decl_class('gs::Matrix4')
	gen.decl_class('gs::Matrix44')

	# tVector2 TODO class template support

	# Vector3
	gen.begin_class('gs::Vector3')

	gen.bind_members('gs::Vector3', ['float x', 'float y', 'float z', 'const gs::Vector3 v'])

	gen.bind_constructor_overloads('gs::Vector3', [['float x', 'float y', 'float z'], ['const gs::Vector4 &v'], ['const gs::Color &c']])

	gen.bind_arithmetic_ops_overloads('gs::Vector3', ['+', '-', '/'], [('gs::Vector3', ['gs::Vector3 &']), ('gs::Vector3', ['float'])])
	gen.bind_arithmetic_ops_overloads('gs::Vector3', ['*'], [('gs::Vector3', ['gs::Vector3 &']), ('gs::Vector3', ['float']), ('gs::Vector3', ['gs::Matrix3']), ('gs::Vector3', ['gs::Matrix4'])])

	gen.bind_inplace_arithmetic_ops_overloads('gs::Vector3', ['+=', '-=', '*=', '/='], [['gs::Vector3 &'], ['float']])



#	gen.bind_method('gs::Vector3', 'Set', 'void', ['float x=0', 'float y=0', 'float z=0'])

	gen.bind_method('gs::Vector3', 'Set', 'void', ['const gs::Vector3 &v'])

	gen.bind_method('gs::Vector3', 'Dot', 'float', ['const gs::Vector3 &v'])
	gen.bind_method('gs::Vector3', 'Cross', 'gs::Vector3', ['const gs::Vector3 &v'])

	gen.bind_method('gs::Vector3', 'Reverse', 'void', [])
	gen.bind_method('gs::Vector3', 'Inverse', 'void', [])

	gen.bind_method('gs::Vector3', 'Normalize', 'void', [])
	gen.bind_method('gs::Vector3', 'Normalized', 'gs::Vector3', [])

	gen.bind_method_overloads('gs::Vector3', 'Clamped', [('gs::Vector3', ['float min', 'float max']), ('gs::Vector3', ['const gs::Vector3 &min', 'const gs::Vector3 &max'])])
	gen.bind_method('gs::Vector3', 'ClampedMagnitude', 'gs::Vector3', ['float min', 'float max'])

	gen.bind_method('gs::Vector3', 'Reversed', 'gs::Vector3', [])
	gen.bind_method('gs::Vector3', 'Inversed', 'gs::Vector3', [])

	gen.bind_method('gs::Vector3', 'Abs', 'gs::Vector3', [])
	gen.bind_method('gs::Vector3', 'Sign', 'gs::Vector3', [])

	gen.bind_method('gs::Vector3', 'Maximum', 'gs::Vector3', ['const gs::Vector3 &left', 'const gs::Vector3 &right'])
	gen.bind_method('gs::Vector3', 'Minimum', 'gs::Vector3', ['const gs::Vector3 &left', 'const gs::Vector3 &right'])

	gen.bind_method('gs::Vector3', 'Reflected', 'gs::Vector3', ['const gs::Vector3 &n'])
#	gen.bind_method('gs::Vector3', 'Refracted', 'gs::Vector3', ['const gs::Vector3 &n', 'float index_of_refraction_in=1', 'float index_of_refraction_out=1'])

	gen.bind_method('gs::Vector3', 'Len2', 'float', [])
	gen.bind_method('gs::Vector3', 'Len', 'float', [])

	gen.bind_method('gs::Vector3', 'Floor', 'gs::Vector3', [])
	gen.bind_method('gs::Vector3', 'Ceil', 'gs::Vector3', [])

# TODO
	# static Vector3 Random(float min = -1.f, float max = 1.f);
	# static Vector3 Random(const Vector3 &min, const Vector3 &max);
	#
	# static float Dist2(const Vector3 &a, const Vector3 &b);
	# static float Dist(const Vector3 &a, const Vector3 &b);

	gen.end_class('gs::Vector3')


def run_test(gen):
	gen.start('test')
	bind_math(gen)
	gen.finalize()

	header, source = gen.get_output()
	print(header, source)


#run_test(lua.LuaGenerator())
run_test(python.PythonGenerator())




# from pybindgen import *
# import sys
#
# mod = Module('test')
# vec = mod.add_class('gs::Vector3')
# vec.add_instance_attribute('x', 'float')
# vec.add_instance_attribute('y', 'float')
# vec.add_instance_attribute('z', 'float')
# vec.add_instance_attribute('v', 'gs::Vector3', True)
# vec.add_constructor([])
# vec.add_constructor([param('float', 'x'), param('float', 'y'), param('float', 'z')])
# vec.add_inplace_numeric_operator('+=')
# vec.add_inplace_numeric_operator('+=', param('float', 'v'))
# mod.generate(sys.stdout)
