import lua
import python


def bind_globals(gen):
	gen.bind_function_overloads('gs::core::LoadPlugins', [('bool', []), ('bool', ['const char *path'])])
	gen.bind_function('gs::core::UnloadPlugins', 'void', [])


def bind_render(gen):
	gen.begin_class('gs::RenderWindow')
	gen.end_class('gs::RenderWindow')


def bind_plus(gen):

	# Plus
	gen.add_include('plus/plus.h')

	gen.begin_class('gs::Plus', noncopyable=True)

	gen.bind_constructor('gs::Plus', [])

	gen.bind_method_overloads('gs::Plus', 'RenderInit', [
		('bool', ['int width', 'int height']),
		('bool', ['int width', 'int height', 'const char *core_path'])
	])
	gen.bind_method('gs::Plus', 'RenderUninit', 'void', [])

	gen.bind_method('gs::Plus', 'NewRenderWindow', 'gs::RenderWindow', ['int width', 'int height'])
	gen.bind_method('gs::Plus', 'FreeRenderWindow', 'void', ['gs::RenderWindow &window'])

	gen.bind_method('gs::Plus', 'GetRenderWindow', 'gs::RenderWindow', [])
	gen.bind_method_overloads('gs::Plus', 'SetRenderWindow', [
		('void', ['gs::RenderWindow &window']),
		('void', [])
	])

	gen.bind_method('gs::Plus', 'UpdateRenderWindow', 'void', ['const gs::RenderWindow &window'])

	gen.end_class('gs::Plus')


def bind_math(gen):
	gen.add_include("foundation/color.h")
	gen.add_include("foundation/vector3.h")
	gen.add_include("foundation/vector3_api.h")
	gen.add_include("foundation/vector4.h")
	gen.add_include("foundation/matrix3.h")
	gen.add_include("foundation/matrix4.h")
	gen.add_include("foundation/matrix44.h")

	gen.decl_class('gs::Color')
	gen.decl_class('gs::Vector3')
	gen.decl_class('gs::Vector4')
	gen.decl_class('gs::Matrix3')
	gen.decl_class('gs::Matrix4')
	gen.decl_class('gs::Matrix44')

	gen.begin_class('gs::Color')
	gen.end_class('gs::Color')

	gen.begin_class('gs::Vector4')
	gen.end_class('gs::Vector4')

	gen.begin_class('gs::Matrix3')
	gen.end_class('gs::Matrix3')

	gen.begin_class('gs::Matrix4')
	gen.end_class('gs::Matrix4')

	gen.begin_class('gs::Matrix44')
	gen.end_class('gs::Matrix44')

	# Vector3
	gen.begin_class('gs::Vector3')

	gen.bind_members('gs::Vector3', ['float x', 'float y', 'float z'])

	gen.bind_constructor_overloads('gs::Vector3', [[], ['float x', 'float y', 'float z']])

	gen.bind_function('gs::Vector3FromVector4', 'gs::Vector3', ['const gs::Vector4 &v'])

	gen.bind_arithmetic_ops_overloads('gs::Vector3', ['+', '-', '/'], [('gs::Vector3', ['gs::Vector3 &v']), ('gs::Vector3', ['float k'])])
	gen.bind_arithmetic_ops_overloads('gs::Vector3', ['*'], [('gs::Vector3', ['gs::Vector3 &v']), ('gs::Vector3', ['float k']), ('gs::Vector3', ['gs::Matrix3 m']), ('gs::Vector3', ['gs::Matrix4 m'])])

	gen.bind_inplace_arithmetic_ops_overloads('gs::Vector3', ['+=', '-=', '*=', '/='], [['gs::Vector3 &v'], ['float k']])

	gen.bind_function('gs::Dot', 'float', ['const gs::Vector3 &u', 'const gs::Vector3 &v'])
	gen.bind_function('gs::Cross', 'gs::Vector3', ['const gs::Vector3 &u', 'const gs::Vector3 &v'])

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

	gen.bind_function('gs::Reflect', 'gs::Vector3', ['const gs::Vector3 &v', 'const gs::Vector3 &normal'])
	gen.bind_function_overloads('gs::Refract', [('gs::Vector3', ['const gs::Vector3 &v', 'const gs::Vector3 &normal']), ('gs::Vector3', ['const gs::Vector3 &v', 'const gs::Vector3 &normal', 'float index_of_refraction_in', 'float index_of_refraction_out'])])

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


def bind_gs(gen):
	gen.start('gs')

	gen.add_include('engine/engine.h')
	gen.add_include('engine/engine_plugins.h')

	gen.add_custom_init_code('''
	gs::core::Init();
''')

	bind_globals(gen)
	bind_render(gen)
	bind_plus(gen)
	bind_math(gen)

	gen.finalize()

	return gen.get_output()


hdr, src = bind_gs(python.PythonGenerator())

with open('d:/gs-fabgen-test/bind_gs.h', mode='w', encoding='utf-8') as f:
	f.write(hdr)
with open('d:/gs-fabgen-test/bind_gs.cpp', mode='w', encoding='utf-8') as f:
	f.write(src)

print("DONE")
