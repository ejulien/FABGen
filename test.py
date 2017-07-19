import lua
import python

from lib.std import StdSharedPtrProxyProtocol


def bind_globals(gen):
	gen.bind_function_overloads('gs::core::LoadPlugins', [('bool', [], []), ('bool', ['const char *path'], [])])
	gen.bind_function('gs::core::UnloadPlugins', 'void', [])


def bind_render(gen):
	window_conv = gen.begin_class('gs::RenderWindow')
	gen.end_class(window_conv)


def bind_plus(gen):

	# Plus
	gen.add_include('plus/plus.h')

	plus_conv = gen.begin_class('gs::Plus', noncopyable=True)

	gen.bind_constructor(plus_conv, [])

	gen.bind_method_overloads(plus_conv, 'RenderInit', [
		('bool', ['int width', 'int height'], []),
		('bool', ['int width', 'int height', 'const char *core_path'], [])
	])
	gen.bind_method(plus_conv, 'RenderUninit', 'void', [])

	gen.bind_method(plus_conv, 'NewRenderWindow', 'gs::RenderWindow', ['int width', 'int height'])
	gen.bind_method(plus_conv, 'FreeRenderWindow', 'void', ['gs::RenderWindow &window'])

	gen.bind_method(plus_conv, 'GetRenderWindow', 'gs::RenderWindow', [])
	gen.bind_method_overloads(plus_conv, 'SetRenderWindow', [
		('void', ['gs::RenderWindow &window'], []),
		('void', [], [])
	])

	gen.bind_method(plus_conv, 'UpdateRenderWindow', 'void', ['const gs::RenderWindow &window'])

	gen.end_class(plus_conv)


def bind_filesystem(gen):
	gen.add_include("foundation/io_cfile.h")

	cfile_conv = gen.begin_class('gs::io::CFile', bound_name='CFile_hide_me')  # TODO do not expose this type in the module
	gen.end_class(cfile_conv)

	std_file_driver_conv = gen.begin_class('std::shared_ptr<gs::io::CFile>', bound_name='StdFileDriver', proxy_protocol=StdSharedPtrProxyProtocol(cfile_conv))
	gen.bind_constructor_overloads(std_file_driver_conv, [
		([], ['proxy']),
		(['const std::string &root_path'], ['proxy']),
		(['const std::string &root_path', 'bool sandbox'], ['proxy'])
		])
	gen.bind_method_overloads(std_file_driver_conv, 'SetRootPath', [('void', ['const std::string &path'], ['proxy']), ('void', ['const std::string &path', 'bool sandbox'], ['proxy'])])
	gen.end_class(std_file_driver_conv)


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

	color_conv = gen.begin_class('gs::Color')
	gen.end_class(color_conv)

	vector4_conv = gen.begin_class('gs::Vector4')
	gen.end_class(vector4_conv)

	matrix3_conv = gen.begin_class('gs::Matrix3')
	gen.end_class(matrix3_conv)

	matrix4_conv = gen.begin_class('gs::Matrix4')
	gen.end_class(matrix4_conv)

	matrix44_conv = gen.begin_class('gs::Matrix44')
	gen.end_class(matrix44_conv)

	# Vector3
	vector3_conv = gen.begin_class('gs::Vector3')

	gen.bind_members(vector3_conv, ['float x', 'float y', 'float z'])

	gen.bind_constructor_overloads(vector3_conv, [
		([], []),
		(['float x', 'float y', 'float z'], [])
		])

	gen.bind_function('gs::Vector3FromVector4', 'gs::Vector3', ['const gs::Vector4 &v'])

	gen.bind_arithmetic_ops_overloads(vector3_conv, ['+', '-', '/'], [('gs::Vector3', ['gs::Vector3 &v'], []), ('gs::Vector3', ['float k'], [])])
	gen.bind_arithmetic_ops_overloads(vector3_conv, ['*'], [('gs::Vector3', ['gs::Vector3 &v'], []), ('gs::Vector3', ['float k'], []), ('gs::Vector3', ['gs::Matrix3 m'], []), ('gs::Vector3', ['gs::Matrix4 m'], [])])

	gen.bind_inplace_arithmetic_ops_overloads(vector3_conv, ['+=', '-=', '*=', '/='], [('gs::Vector3 &v', []), ('float k', [])])

	gen.bind_function('gs::Dot', 'float', ['const gs::Vector3 &u', 'const gs::Vector3 &v'])
	gen.bind_function('gs::Cross', 'gs::Vector3', ['const gs::Vector3 &u', 'const gs::Vector3 &v'])

	gen.bind_method(vector3_conv, 'Reverse', 'void', [])
	gen.bind_method(vector3_conv, 'Inverse', 'void', [])
	gen.bind_method(vector3_conv, 'Normalize', 'void', [])
	gen.bind_method(vector3_conv, 'Normalized', 'gs::Vector3', [])
	gen.bind_method_overloads(vector3_conv, 'Clamped', [('gs::Vector3', ['float min', 'float max'], []), ('gs::Vector3', ['const gs::Vector3 &min', 'const gs::Vector3 &max'], [])])
	gen.bind_method(vector3_conv, 'ClampedMagnitude', 'gs::Vector3', ['float min', 'float max'])
	gen.bind_method(vector3_conv, 'Reversed', 'gs::Vector3', [])
	gen.bind_method(vector3_conv, 'Inversed', 'gs::Vector3', [])
	gen.bind_method(vector3_conv, 'Abs', 'gs::Vector3', [])
	gen.bind_method(vector3_conv, 'Sign', 'gs::Vector3', [])
	gen.bind_method(vector3_conv, 'Maximum', 'gs::Vector3', ['const gs::Vector3 &left', 'const gs::Vector3 &right'])
	gen.bind_method(vector3_conv, 'Minimum', 'gs::Vector3', ['const gs::Vector3 &left', 'const gs::Vector3 &right'])

	gen.bind_function('gs::Reflect', 'gs::Vector3', ['const gs::Vector3 &v', 'const gs::Vector3 &normal'])
	gen.bind_function_overloads('gs::Refract', [
		('gs::Vector3', ['const gs::Vector3 &v', 'const gs::Vector3 &normal'], []),
		('gs::Vector3', ['const gs::Vector3 &v', 'const gs::Vector3 &normal', 'float index_of_refraction_in', 'float index_of_refraction_out'], [])
		])

	gen.bind_method(vector3_conv, 'Len2', 'float', [])
	gen.bind_method(vector3_conv, 'Len', 'float', [])
	gen.bind_method(vector3_conv, 'Floor', 'gs::Vector3', [])
	gen.bind_method(vector3_conv, 'Ceil', 'gs::Vector3', [])

	gen.end_class(vector3_conv)


def bind_gs(gen):
	gen.start('gs')

	gen.add_include('engine/engine.h')
	gen.add_include('engine/engine_plugins.h')

	gen.add_custom_init_code('''
	gs::core::Init();
''')

	bind_globals(gen)
	bind_filesystem(gen)
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
