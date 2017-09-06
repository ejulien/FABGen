import argparse

import lang.lua
import lang.cpython

import lib.std
import lib.stl
import lib


def check_rval_lambda(gen, msg):
	return lambda rvals, ctx: 'if (!%s) {\n%s}\n' % (rvals[0], gen.proxy_call_error(msg, ctx))


def route_lambda(name):
	return lambda args: '%s(%s);' % (name, ', '.join(args))


def bind_std_vector(gen, T_conv):
	if gen.get_language() == 'CPython':
		PySequence_T_type = 'PySequenceOf%s' % T_conv.bound_name.title()
		gen.bind_type(lib.cpython.stl.PySequenceToStdVectorConverter(PySequence_T_type, T_conv))

	conv = gen.begin_class('std::vector<%s>' % T_conv.ctype, bound_name='%sList' % T_conv.bound_name.title(), features={'sequence': lib.std.VectorSequenceFeature(T_conv)})
	if gen.get_language() == 'CPython':
		gen.bind_constructor(conv, ['%s sequence' % PySequence_T_type])

	gen.bind_method(conv, 'push_back', 'void', ['%s v' % T_conv.ctype])
	gen.bind_method(conv, 'size', 'size_t', [])
	gen.bind_method(conv, 'at', repr(T_conv.ctype), ['int idx'])

	gen.end_class(conv)
	return conv


def bind_log(gen):
	gen.add_include('foundation/log.h')

	gen.bind_named_enum('gs::LogLevel::mask_type', ['Message', 'Warning', 'Error', 'Debug', 'All'], storage_type='gs::uint', prefix='Log', bound_name='LogLevel', namespace='gs::LogLevel')

	gen.bind_function('gs::SetLogLevel', 'void', ['gs::LogLevel::mask_type mask'])
	gen.bind_function('gs::SetLogIsDetailed', 'void', ['bool is_detailed'])

	gen.bind_function('gs::FlushLog', 'void', [])


def bind_binary_blob(gen):
	gen.add_include('foundation/binary_blob.h')

	binary_blob = gen.begin_class('gs::BinaryBlob', bound_name='BinaryData')

	gen.bind_constructor_overloads(binary_blob, [
		([], []),
		(['const gs::BinaryBlob &data'], [])
	])

	gen.bind_method(binary_blob, 'GetDataSize', 'size_t', [])

	gen.bind_method(binary_blob, 'GetCursor', 'size_t', [])
	gen.bind_method(binary_blob, 'SetCursor', 'void', ['size_t position'])

	gen.bind_method(binary_blob, 'GetCursorPtr', 'const char *', [])
	gen.bind_method(binary_blob, 'GetDataSizeAtCursor', 'size_t', [])

	gen.bind_method(binary_blob, 'Reset', 'void', [])

	gen.bind_method(binary_blob, 'Commit', 'void', ['size_t size'])
	gen.bind_method(binary_blob, 'Grow', 'void', ['size_t size'])
	gen.bind_method(binary_blob, 'Skip', 'void', ['size_t size'])

	def bind_write(type, alias):
		# unit write
		gen.bind_method(binary_blob, 'Write<%s>' % type, 'void', ['const %s &v' % type], bound_name='Write%s' % alias)

		# batch write
		gen.insert_binding_code('''
static void _BinaryData_Write%ss(gs::BinaryBlob *blob, const std::vector<%s> &vs) {
	for (auto &v : vs)
		blob->Write<%s>(v);
}
''' % (alias, type, type))

		features = {'route': lambda args: '_BinaryData_Write%ss(%s);' % (alias, ', '.join(args))}

		protos = []
		protos += [('void', ['const std::vector<%s> &vs' % type], features)]
		if gen.get_language() == 'CPython':
			protos += [('void', ['PySequenceOf%s seq' % gen.get_conv(type).bound_name.title()], features)]

		gen.bind_method_overloads(binary_blob, 'Write%ss' % alias, protos)

	bind_write('int8_t', 'Int8')
	bind_write('int16_t', 'Int16')
	bind_write('int32_t', 'Int32')
	bind_write('int64_t', 'Int64')
	bind_write('uint8_t', 'UInt8')
	bind_write('uint16_t', 'UInt16')
	bind_write('uint32_t', 'UInt32')
	bind_write('uint64_t', 'UInt64')
	bind_write('float', 'Float')
	bind_write('double', 'Double')

	def bind_write_at(type, alias):
		gen.bind_method(binary_blob, 'WriteAt<%s>' % type, 'void', ['const %s &v' % type, 'size_t position'], bound_name='Write%sAt' % alias)

	bind_write_at('int8_t', 'Int8')
	bind_write_at('int16_t', 'Int16')
	bind_write_at('int32_t', 'Int32')
	bind_write_at('int64_t', 'Int64')
	bind_write_at('uint8_t', 'UInt8')
	bind_write_at('uint16_t', 'UInt16')
	bind_write_at('uint32_t', 'UInt32')
	bind_write_at('uint64_t', 'UInt64')
	bind_write_at('float', 'Float')
	bind_write_at('double', 'Double')

	# TODO Read<T> requires tuple return value

	gen.bind_method(binary_blob, 'Free', 'void', [])

	gen.end_class(binary_blob)

	# implicit cast to various base types
	gen.add_cast(binary_blob, gen.get_conv('float *'), lambda in_var, out_var: '%s = ((gs::BinaryBlob *)%s)->GetData();\n' % (out_var, in_var))
	gen.add_cast(binary_blob, gen.get_conv('void *'), lambda in_var, out_var: '%s = ((gs::BinaryBlob *)%s)->GetData();\n' % (out_var, in_var))

	#
	gen.bind_function('BinaryBlobBlur3d', 'void', ['gs::BinaryBlob &data', 'uint32_t width', 'uint32_t height', 'uint32_t depth'])


def bind_task_system(gen):
	gen.add_include('foundation/task.h')

	gen.typedef('gs::task_affinity', 'char')
	gen.typedef('gs::task_priority', 'char')


def bind_time(gen):
	gen.add_include('foundation/time.h')

	gen.typedef('gs::time_ns', 'int64_t')

	gen.bind_function('gs::time_to_sec_f', 'float', ['gs::time_ns t'])
	gen.bind_function('gs::time_to_ms_f', 'float', ['gs::time_ns t'])
	gen.bind_function('gs::time_to_us_f', 'float', ['gs::time_ns t'])

	gen.bind_function('gs::time_to_day', 'int64_t', ['gs::time_ns t'])
	gen.bind_function('gs::time_to_hour', 'int64_t', ['gs::time_ns t'])
	gen.bind_function('gs::time_to_min', 'int64_t', ['gs::time_ns t'])
	gen.bind_function('gs::time_to_sec', 'int64_t', ['gs::time_ns t'])
	gen.bind_function('gs::time_to_ms', 'int64_t', ['gs::time_ns t'])
	gen.bind_function('gs::time_to_us', 'int64_t', ['gs::time_ns t'])
	gen.bind_function('gs::time_to_ns', 'int64_t', ['gs::time_ns t'])

	gen.bind_function('gs::time_from_sec_f', 'gs::time_ns', ['float sec'])
	gen.bind_function('gs::time_from_ms_f', 'gs::time_ns', ['float ms'])
	gen.bind_function('gs::time_from_us_f', 'gs::time_ns', ['float us'])

	gen.bind_function('gs::time_from_day', 'gs::time_ns', ['int64_t day'])
	gen.bind_function('gs::time_from_hour', 'gs::time_ns', ['int64_t hour'])
	gen.bind_function('gs::time_from_min', 'gs::time_ns', ['int64_t min'])
	gen.bind_function('gs::time_from_sec', 'gs::time_ns', ['int64_t sec'])
	gen.bind_function('gs::time_from_ms', 'gs::time_ns', ['int64_t ms'])
	gen.bind_function('gs::time_from_us', 'gs::time_ns', ['int64_t us'])
	gen.bind_function('gs::time_from_ns', 'gs::time_ns', ['int64_t ns'])

	gen.bind_function('gs::time_now', 'gs::time_ns', [])

	gen.bind_function('gs::time_to_string', 'std::string', ['gs::time_ns t'])

	lib.stl.bind_future_T(gen, 'gs::time_ns', 'FutureTime')


def bind_input(gen):
	gen.add_include('platform/input_system.h')

	gen.bind_named_enum('gs::InputDevice::Type', [
		'TypeAny', 'TypeKeyboard', 'TypeMouse', 'TypePad', 'TypeTouch', 'TypeHMD', 'TypeController'
	], bound_name='InputType', prefix='Input')

	gen.bind_named_enum('gs::InputDevice::KeyCode', [
		'KeyLShift', 'KeyRShift', 'KeyLCtrl', 'KeyRCtrl', 'KeyLAlt', 'KeyRAlt', 'KeyLWin', 'KeyRWin',
		'KeyTab', 'KeyCapsLock', 'KeySpace', 'KeyBackspace', 'KeyInsert', 'KeySuppr', 'KeyHome', 'KeyEnd', 'KeyPageUp', 'KeyPageDown',
		'KeyUp', 'KeyDown', 'KeyLeft', 'KeyRight',
		'KeyEscape',
		'KeyF1', 'KeyF2', 'KeyF3', 'KeyF4', 'KeyF5', 'KeyF6', 'KeyF7', 'KeyF8', 'KeyF9', 'KeyF10', 'KeyF11', 'KeyF12',
		'KeyPrintScreen', 'KeyScrollLock', 'KeyPause', 'KeyNumLock', 'KeyReturn',
		'KeyNumpad0', 'KeyNumpad1', 'KeyNumpad2', 'KeyNumpad3', 'KeyNumpad4', 'KeyNumpad5', 'KeyNumpad6', 'KeyNumpad7', 'KeyNumpad8', 'KeyNumpad9',
		'KeyAdd', 'KeySub', 'KeyMul', 'KeyDiv', 'KeyEnter',
		'KeyA', 'KeyB', 'KeyC', 'KeyD', 'KeyE', 'KeyF', 'KeyG', 'KeyH', 'KeyI', 'KeyJ', 'KeyK', 'KeyL', 'KeyM', 'KeyN', 'KeyO', 'KeyP', 'KeyQ', 'KeyR', 'KeyS', 'KeyT', 'KeyU', 'KeyV', 'KeyW', 'KeyX', 'KeyY', 'KeyZ',
		'KeyLast'
	])

	gen.bind_named_enum('gs::InputDevice::ButtonCode', [
		'Button0', 'Button1', 'Button2', 'Button3', 'Button4', 'Button5', 'Button6', 'Button7', 'Button8', 'Button9', 'Button10',
		'Button11', 'Button12', 'Button13', 'Button14', 'Button15', 'Button16', 'Button17', 'Button18', 'Button19', 'Button20',
		'Button21', 'Button22', 'Button23', 'Button24', 'Button25', 'Button26', 'Button27', 'Button28', 'Button29', 'Button30',
		'Button31', 'Button32', 'Button33', 'Button34', 'Button35', 'Button36', 'Button37', 'Button38', 'Button39', 'Button40',
		'Button41', 'Button42', 'Button43', 'Button44', 'Button45', 'Button46', 'Button47', 'Button48', 'Button49', 'Button50',
		'Button51', 'Button52', 'Button53', 'Button54', 'Button55', 'Button56', 'Button57', 'Button58', 'Button59', 'Button60',
		'Button61', 'Button62', 'Button63', 'Button64', 'Button65', 'Button66', 'Button67', 'Button68', 'Button69', 'Button70',
		'Button71', 'Button72', 'Button73', 'Button74', 'Button75', 'Button76', 'Button77', 'Button78', 'Button79', 'Button80',
		'Button81', 'Button82', 'Button83', 'Button84', 'Button85', 'Button86', 'Button87', 'Button88', 'Button89', 'Button90',
		'Button91', 'Button92', 'Button93', 'Button94', 'Button95', 'Button96', 'Button97', 'Button98', 'Button99', 'Button100',
		'Button101', 'Button102', 'Button103', 'Button104', 'Button105', 'Button106', 'Button107', 'Button108', 'Button109',
		'Button110', 'Button111', 'Button112', 'Button113', 'Button114', 'Button115', 'Button116', 'Button117', 'Button118',
		'Button119', 'Button120', 'Button121', 'Button122', 'Button123', 'Button124', 'Button125', 'Button126', 'Button127',
		'ButtonBack', 'ButtonStart', 'ButtonSelect', 'ButtonL1', 'ButtonL2', 'ButtonL3', 'ButtonR1', 'ButtonR2', 'ButtonR3',
		'ButtonCrossUp', 'ButtonCrossDown', 'ButtonCrossLeft', 'ButtonCrossRight',
		'ButtonLast'
	])

	gen.bind_named_enum('gs::InputDevice::InputCode', [
		'InputAxisX', 'InputAxisY', 'InputAxisZ', 'InputAxisS', 'InputAxisT', 'InputAxisR',
		'InputRotX', 'InputRotY', 'InputRotZ', 'InputRotS', 'InputRotT', 'InputRotR',
		'InputButton0', 'InputButton1', 'InputButton2', 'InputButton3', 'InputButton4', 'InputButton5', 'InputButton6', 'InputButton7', 'InputButton8', 'InputButton9', 'InputButton10', 'InputButton11', 'InputButton12', 'InputButton13', 'InputButton14', 'InputButton15',
		'InputLast'
	])

	gen.bind_named_enum('gs::InputDevice::Effect', ['Vibrate', 'VibrateLeft', 'VibrateRight', 'ConstantForce'], bound_name='InputEffect', prefix='Input')
	gen.bind_named_enum('gs::InputDevice::MatrixCode', ['MatrixHead'], bound_name='InputMatrixCode', prefix='Input')

	# gs::InputDevice
	input_device = gen.begin_class('gs::InputDevice', bound_name='InputDevice_nobind', noncopyable=True, nobind=True)
	gen.end_class(input_device)

	shared_input_device = gen.begin_class('std::shared_ptr<gs::InputDevice>', bound_name='InputDevice', features={'proxy': lib.stl.SharedPtrProxyFeature(input_device)})

	gen.bind_method(shared_input_device, 'GetType', 'gs::InputDevice::Type', [], ['proxy'])

	gen.bind_method(shared_input_device, 'Update', 'void', [], ['proxy'])

	gen.bind_method(shared_input_device, 'IsDown', 'bool', ['gs::InputDevice::KeyCode key'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasDown', 'bool', ['gs::InputDevice::KeyCode key'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasPressed', 'bool', ['gs::InputDevice::KeyCode key'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasReleased', 'bool', ['gs::InputDevice::KeyCode key'], ['proxy'])

	gen.bind_method(shared_input_device, 'IsButtonDown', 'bool', ['gs::InputDevice::ButtonCode button'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasButtonDown', 'bool', ['gs::InputDevice::ButtonCode button'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasButtonPressed', 'bool', ['gs::InputDevice::ButtonCode button'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasButtonReleased', 'bool', ['gs::InputDevice::ButtonCode button'], ['proxy'])

	gen.bind_method(shared_input_device, 'GetValue', 'float', ['gs::InputDevice::InputCode input'], ['proxy'])
	gen.bind_method(shared_input_device, 'GetLastValue', 'float', ['gs::InputDevice::InputCode input'], ['proxy'])
	gen.bind_method(shared_input_device, 'GetValueRange', 'bool', ['gs::InputDevice::InputCode input', 'float &min', 'float &max'], {'proxy': None, 'arg_out': ['min', 'max']})
	gen.bind_method(shared_input_device, 'GetDelta', 'float', ['gs::InputDevice::InputCode input'], ['proxy'])

	gen.bind_method(shared_input_device, 'GetMatrix', 'gs::Matrix4', ['gs::InputDevice::MatrixCode matrix_code'], ['proxy'])

	gen.bind_method(shared_input_device, 'SetValue', 'bool', ['gs::InputDevice::InputCode input', 'float value'], ['proxy'])
	gen.bind_method(shared_input_device, 'SetEffect', 'bool', ['gs::InputDevice::Effect effect', 'float value'], ['proxy'])

	gen.bind_method(shared_input_device, 'IsConnected', 'bool', [], ['proxy'])

	gen.end_class(shared_input_device)

	# gs::InputSystem
	input_system = gen.begin_class('gs::InputSystem', noncopyable=True)

	gen.bind_method(input_system, 'Update', 'void', [])

	gen.bind_method(input_system, 'GetDevices', 'std::vector<std::string>', [])
	gen.bind_method(input_system, 'GetDevice', 'std::shared_ptr<gs::InputDevice>', ['const std::string &name'])

	gen.end_class(input_system)

	gen.insert_binding_code('static gs::InputSystem &GetInputSystem() { return gs::g_input_system.get(); }\n\n')
	gen.bind_function('GetInputSystem', 'gs::InputSystem &', [])


def bind_engine(gen):
	gen.add_include('engine/engine.h')

	gen.bind_function('gs::core::GetExecutablePath', 'std::string', [])

	gen.bind_function('gs::core::EndFrame', 'void', [])

	gen.bind_function('gs::core::GetLastFrameDuration', 'gs::time_ns', [])
	gen.bind_function('gs::core::GetLastFrameDurationSec', 'float', [])
	gen.bind_function('gs::core::ResetLastFrameDuration', 'void', [])

	gen.bind_function('gs::core::_DebugHalt', 'void', [])

	gen.add_include('foundation/projection.h')

	gen.bind_function('gs::ZoomFactorToFov', 'float', ['float zoom_factor'])
	gen.bind_function('gs::FovToZoomFactor', 'float', ['float fov'])

	gen.bind_function('gs::ComputeOrthographicProjectionMatrix', 'gs::Matrix44', ['float znear', 'float zfar', 'float size', 'const gs::tVector2<float> &aspect_ratio'])
	gen.bind_function('gs::ComputePerspectiveProjectionMatrix', 'gs::Matrix44', ['float znear', 'float zfar', 'float zoom_factor', 'const gs::tVector2<float> &aspect_ratio'])


def bind_plugins(gen):
	gen.bind_function_overloads('gs::core::LoadPlugins', [('gs::uint', [], []), ('gs::uint', ['const char *path'], [])])
	gen.bind_function('gs::core::UnloadPlugins', 'void', [])


def bind_window_system(gen):
	gen.add_include('platform/window_system.h')

	# gs::Surface
	surface = gen.begin_class('gs::Surface')
	gen.end_class(surface)

	# gs::Monitor
	monitor = gen.begin_class('gs::Monitor')
	gen.end_class(monitor)
	bind_std_vector(gen, monitor)

	gen.bind_function('gs::GetMonitors', 'std::vector<gs::Monitor>', [])

	# gs::Window
	gen.bind_named_enum('gs::Window::Visibility', ['Windowed', 'Undecorated', 'Fullscreen', 'Hidden', 'FullscreenMonitor1', 'FullscreenMonitor2', 'FullscreenMonitor3'])

	window = gen.begin_class('gs::Window')
	gen.end_class(window)

	gen.bind_function_overloads('gs::NewWindow', [
		('gs::Window', ['int width', 'int height'], []),
		('gs::Window', ['int width', 'int height', 'int bpp'], []),
		('gs::Window', ['int width', 'int height', 'int bpp', 'gs::Window::Visibility visibility'], [])
	])
	gen.bind_function('gs::NewWindowFrom', 'gs::Window', ['void *handle'])

	gen.bind_function('gs::GetWindowHandle', 'void *', ['const gs::Window &window'])
	gen.bind_function('gs::UpdateWindow', 'bool', ['const gs::Window &window'])
	gen.bind_function('gs::DestroyWindow', 'bool', ['const gs::Window &window'])

	gen.bind_function('gs::GetWindowClientSize', 'bool', ['const gs::Window &window', 'int &width', 'int &height'], features={'arg_out': ['width', 'height']})
	gen.bind_function('gs::SetWindowClientSize', 'bool', ['const gs::Window &window', 'int width', 'int height'])

	gen.bind_function('gs::GetWindowTitle', 'bool', ['const gs::Window &window', 'std::string &title'], features={'arg_out': ['title']})
	gen.bind_function('gs::SetWindowTitle', 'bool', ['const gs::Window &window', 'const std::string &title'])

	gen.bind_function('gs::WindowHasFocus', 'bool', ['const gs::Window &window'])
	gen.bind_function('gs::GetWindowInFocus', 'gs::Window', [])

	gen.bind_function('gs::GetWindowPos', 'gs::tVector2<int>', ['const gs::Window &window'])
	gen.bind_function('gs::SetWindowPos', 'bool', ['const gs::Window &window', 'const gs::tVector2<int> position'])

	gen.bind_function('gs::IsWindowOpen', 'bool', ['const gs::Window &window'])

	lib.stl.bind_future_T(gen, 'gs::Window', 'FutureWindow')
	lib.stl.bind_future_T(gen, 'gs::Surface', 'FutureSurface')


def bind_type_value(gen):
	gen.add_include('foundation/reflection.h')
	gen.add_include('foundation/base_type_reflection.h')

	if gen.get_language() == 'CPython':
		class PythonTypeValueConverter(lang.cpython.PythonTypeConverterCommon):
			def get_type_glue(self, gen, module_name):
				check = '''\
bool check_TypeValue(PyObject *o) {
	using namespace gs;
	return true;
}
'''
				to_c = '''\
void to_c_TypeValue(PyObject *o, void *obj) {
	using namespace gs;

	TypeValue &value = *(TypeValue *)obj;

	if (check_bool(o)) {
		bool v;
		to_c_bool(o, &v);
		value = MakeTypeValue(v);
	} else if (check_int(o)) {
		int v;
		to_c_int(o, &v);
		value = MakeTypeValue(v);
	} else if (check_float(o)) {
		float v;
		to_c_float(o, &v);
		value = MakeTypeValue(v);
	} else if (check_string(o)) {
		std::string v;
		to_c_string(o, &v);
		value = MakeTypeValue(v);
	} else if (wrapped_Object *w = cast_to_wrapped_Object_safe(o)) {
		//gs::Type *type = type_tag_to_reflection_type(w->type_tag); // TODO
		//value.Set(type, w->obj);
	}
}
'''
				from_c = '''\
PyObject *from_c_TypeValue(void *obj, OwnershipPolicy policy) {
	using namespace gs;

	TypeValue &value = *(TypeValue *)obj;

	static Type *bool_type = g_type_registry.get().GetType("bool");
	static Type *int_type = g_type_registry.get().GetType("int");
	static Type *float_type = g_type_registry.get().GetType("float");
	static Type *string_type = g_type_registry.get().GetType("string");

	const Type *type = value.GetType();

	if (type == bool_type) {
		return from_c_bool(value.GetData(), policy);
	} else if (type == int_type) {
		return from_c_int(value.GetData(), policy);
	} else if (type == float_type) {
		return from_c_float(value.GetData(), policy);
	} else if (type == string_type) {
		return from_c_string(value.GetData(), policy);
	}

//	type_tag_info *info = get_type_tag_info(type_tag); // TODO

//	if (!info) {
	PyErr_SetString(PyExc_RuntimeError, "unsupported TypeValue conversion");
	return NULL;
//	}
//	return (*info->from_c)(obj, policy);
//	return NULL;
}
'''
				return check + to_c + from_c

		type_value = gen.bind_type(PythonTypeValueConverter('gs::TypeValue'))
	else:
		type_value = gen.begin_class('gs::TypeValue')
		gen.end_class(type_value)

	bind_std_vector(gen, type_value)


def bind_core(gen):
	# gs::core::Shader
	gen.add_include('engine/shader.h')

	gen.bind_named_enum('gs::core::ShaderType', ['ShaderNoType', 'ShaderInt', 'ShaderUInt', 'ShaderFloat', 'ShaderVector2', 'ShaderVector3', 'ShaderVector4', 'ShaderMatrix3', 'ShaderMatrix4', 'ShaderTexture2D', 'ShaderTexture3D', 'ShaderTextureCube', 'ShaderTextureShadow', 'ShaderTextureExternal'], storage_type='uint8_t')
	gen.bind_named_enum('gs::core::ShaderTypePrecision', ['ShaderDefaultPrecision', 'ShaderLowPrecision', 'ShaderMediumPrecision', 'ShaderHighPrecision'], storage_type='uint8_t')

	gen.bind_named_enum('gs::core::VertexAttribute::Semantic', ['Position', 'Normal', 'UV0', 'UV1', 'UV2', 'UV3', 'Color0', 'Color1', 'Color2', 'Color3', 'Tangent', 'Bitangent', 'BoneIndex', 'BoneWeight', 'InstanceModelMatrix', 'InstancePreviousModelMatrix', 'InstancePickingId'], storage_type='uint8_t', prefix='Vertex', bound_name='VertexSemantic')

	gen.bind_named_enum('gs::core::TextureUV', ['TextureUVClamp', 'TextureUVRepeat', 'TextureUVMirror', 'TextureUVCount'], storage_type='uint8_t')
	gen.bind_named_enum('gs::core::TextureFilter', ['TextureFilterNearest', 'TextureFilterLinear', 'TextureFilterTrilinear', 'TextureFilterAnisotropic', 'TextureFilterCount'], storage_type='uint8_t')

	shader = gen.begin_class('gs::core::Shader', bound_name='Shader_nobind', noncopyable=True, nobind=True)
	gen.end_class(shader)

	shared_shader = gen.begin_class('std::shared_ptr<gs::core::Shader>', bound_name='Shader', features={'proxy': lib.stl.SharedPtrProxyFeature(shader)})
	gen.bind_members(shared_shader, ['std::string name', 'uint8_t surface_attributes', 'uint8_t surface_draw_state', 'uint8_t alpha_threshold'], ['proxy'])
	gen.end_class(shared_shader)

	gen.bind_named_enum('gs::core::ShaderVariable::Semantic', [
		'Clock', 'Viewport', 'TechniqueIsForward', 'FxScale', 'InverseInternalResolution', 'InverseViewportSize', 'AmbientColor', 'FogColor', 'FogState', 'DepthBuffer', 'FrameBuffer', 'GBuffer0', 'GBuffer1', 'GBuffer2', 'GBuffer3',
		'ViewVector', 'ViewPosition', 'ViewState',
		'ModelMatrix', 'InverseModelMatrix', 'NormalMatrix', 'PreviousModelMatrix', 'ViewMatrix', 'InverseViewMatrix', 'ModelViewMatrix', 'NormalViewMatrix', 'ProjectionMatrix', 'ViewProjectionMatrix', 'ModelViewProjectionMatrix', 'InverseViewProjectionMatrix', 'InverseViewProjectionMatrixAtOrigin',
		'LightState', 'LightDiffuseColor', 'LightSpecularColor', 'LightShadowColor', 'LightViewPosition', 'LightViewDirection', 'LightShadowMatrix', 'InverseShadowMapSize', 'LightShadowMap', 'LightPSSMSliceDistance', 'ViewToLightMatrix', 'LightProjectionMap',
		'BoneMatrix', 'PreviousBoneMatrix',
		'PickingId',
		'TerrainHeightmap', 'TerrainHeightmapSize', 'TerrainSize', 'TerrainPatchOrigin', 'TerrainPatchSize'
	], storage_type='uint8_t', prefix='Shader', bound_name='ShaderSemantic')

	shader_variable = gen.begin_class('gs::core::ShaderVariable')
	gen.bind_members(shader_variable, ['std::string name', 'std::string hint', 'gs::core::ShaderType type', 'gs::core::ShaderTypePrecision precision', 'uint8_t array_size'])
	gen.end_class(shader_variable)

	shader_value = gen.begin_class('gs::core::ShaderValue')
	gen.end_class(shader_value)

	# gs::core::Material
	gen.add_include('engine/material.h')

	material = gen.begin_class('gs::core::Material', bound_name='Material_nobind', noncopyable=True, nobind=True)
	gen.end_class(material)

	gen.insert_binding_code('''
static void _Material_SetName(gs::core::Material *m, const char *name) { m->name = name; }
static void _Material_SetShader(gs::core::Material *m, const char *shader) { m->shader = shader; }
''')

	shared_material = gen.begin_class('std::shared_ptr<gs::core::Material>', bound_name='Material', features={'proxy': lib.stl.SharedPtrProxyFeature(material)})
	gen.bind_constructor(shared_material, [], ['proxy'])
	gen.bind_method(shared_material, 'AddValue', 'void', ['const char *name', 'gs::core::ShaderType type'], ['proxy'])
	gen.bind_method(shared_material, 'SetName', 'void', ['const char *name'], {'proxy': None, 'route': lambda args: '_Material_SetName(%s);' % ', '.join(args)})
	gen.bind_method(shared_material, 'SetShader', 'void', ['const char *shader'], {'proxy': None, 'route': lambda args: '_Material_SetShader(%s);' % ', '.join(args)})
	gen.end_class(shared_material)

	# gs::core::Geometry
	gen.add_include('engine/geometry.h')

	geometry = gen.begin_class('gs::core::Geometry', bound_name='Geometry_nobind', noncopyable=True, nobind=True)
	gen.end_class(geometry)

	shared_geometry = gen.begin_class('std::shared_ptr<gs::core::Geometry>', bound_name='Geometry', features={'proxy': lib.stl.SharedPtrProxyFeature(geometry)})
	gen.bind_constructor(shared_geometry, [], ['proxy'])

	#gen.bind_members(shared_geometry, ['std::string name', 'std::string lod_proxy', 'float lod_distance', 'std::string shadow_proxy'])

	gen.bind_method(shared_geometry, 'SetName', 'bool', ['const char *name'], ['proxy'])

	gen.bind_method(shared_geometry, 'GetTriangleCount', 'gs::uint', [], ['proxy'])

	gen.bind_method(shared_geometry, 'ComputeLocalMinMax', 'gs::MinMax', [], ['proxy'])
	#gen.bind_method(shared_geometry, 'ComputeLocalBoneMinMax', 'bool', [''], ['proxy'])

	gen.bind_method(shared_geometry, 'AllocateVertex', 'void', ['gs::uint count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocatePolygon', 'void', ['gs::uint count'], ['proxy'])

	gen.bind_method(shared_geometry, 'AllocatePolygonBinding', 'bool', [], ['proxy'])
	gen.bind_method(shared_geometry, 'ComputePolygonBindingCount', 'gs::uint', [], ['proxy'])

	gen.bind_method(shared_geometry, 'AllocateVertexNormal', 'void', ['gs::uint count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocateVertexTangent', 'void', ['gs::uint count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocateRgb', 'void', ['gs::uint count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocateMaterialTable', 'void', ['gs::uint count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocateUVChannels', 'bool', ['gs::uint channel_count', 'gs::uint uv_per_channel'], ['proxy'])

	gen.bind_method(shared_geometry, 'GetVertexCount', 'int', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetPolygonCount', 'int', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetVertexNormalCount', 'int', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetVertexTangentCount', 'int', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetRgbCount', 'int', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetUVCount', 'int', [], ['proxy'])

	gen.bind_method(shared_geometry, 'GetVertex', 'gs::Vector3', ['gs::uint index'], ['proxy'])
	gen.bind_method(shared_geometry, 'SetVertex', 'bool', ['gs::uint index', 'const gs::Vector3 &vertex'], ['proxy'])
	gen.bind_method(shared_geometry, 'GetVertexNormal', 'gs::Vector3', ['gs::uint index'], ['proxy'])
	gen.bind_method(shared_geometry, 'SetVertexNormal', 'bool', ['gs::uint index', 'const gs::Vector3 &vertex'], ['proxy'])

	gen.bind_method(shared_geometry, 'GetRgb', 'gs::Color', ['gs::uint index'], ['proxy'])
	protos = [('bool', ['gs::uint poly_index', 'const std::vector<gs::Color> &colors'], ['proxy'])]
	if gen.get_language() == 'CPython':
		protos += [('bool', ['gs::uint poly_index', 'PySequenceOfColor colors'], ['proxy'])]
	gen.bind_method_overloads(shared_geometry, 'SetRgb', protos)

	gen.bind_method(shared_geometry, 'GetUV', 'gs::tVector2<float>', ['gs::uint channel', 'gs::uint index'], ['proxy'])
	protos = [('bool', ['gs::uint channel', 'gs::uint poly_index', 'const std::vector<gs::tVector2<float>> &uvs'], ['proxy'])]
	if gen.get_language() == 'CPython':
		protos += [('bool', ['gs::uint channel', 'gs::uint poly_index', 'PySequenceOfVector2 uvs'], ['proxy'])]
	gen.bind_method_overloads(shared_geometry, 'SetUV', protos)

	gen.bind_method(shared_geometry, 'SetPolygonVertexCount', 'bool', ['gs::uint index', 'uint8_t vtx_count'], ['proxy'])
	gen.bind_method(shared_geometry, 'SetPolygonMaterialIndex', 'bool', ['gs::uint index', 'uint8_t material'], ['proxy'])
	gen.bind_method(shared_geometry, 'SetPolygon', 'bool', ['gs::uint index', 'uint8_t vtx_count', 'uint8_t material'], ['proxy'])
	gen.bind_method(shared_geometry, 'GetPolygonVertexCount', 'int', ['gs::uint index'], ['proxy'])
	gen.bind_method(shared_geometry, 'GetPolygonMaterialIndex', 'int', ['gs::uint index'], ['proxy'])

	protos = [('bool', ['gs::uint index', 'const std::vector<int> &idx'], ['proxy'])]
	if gen.get_language() == 'CPython':
		protos += [('bool', ['gs::uint index', 'PySequenceOfInt idx'], ['proxy'])]
	gen.bind_method_overloads(shared_geometry, 'SetPolygonBinding', protos)

	gen.bind_method(shared_geometry, 'ComputePolygonArea', 'float', ['gs::uint index'], ['proxy'])
	gen.bind_method(shared_geometry, 'Validate', 'bool', [], ['proxy'])

	gen.bind_method(shared_geometry, 'ComputePolygonNormal', 'bool', ['?bool force'], ['proxy'])
	gen.bind_method(shared_geometry, 'ComputePolygonTangent', 'bool', ['?gs::uint uv_index', '?bool force'], ['proxy'])

	gen.bind_method(shared_geometry, 'ComputeVertexNormal', 'bool', ['?float max_smoothing_angle', '?bool force'], ['proxy'])
	gen.bind_method(shared_geometry, 'ComputeVertexTangent', 'bool', ['?bool reverse_T', '?bool reverse_B', '?bool force'], ['proxy'])

	gen.bind_method(shared_geometry, 'ReverseTangentFrame', 'void', ['bool reverse_T', 'bool reverse_B'], ['proxy'])
	gen.bind_method(shared_geometry, 'SmoothRGB', 'void', ['gs::uint pass_count', 'float max_smoothing_angle'], ['proxy'])

	gen.bind_method(shared_geometry, 'MergeDuplicateMaterials', 'gs::uint', [], ['proxy'])
	gen.end_class(shared_geometry)

	# gs::core::TextureUnitConfig
	tex_unit_cfg = gen.begin_class('gs::core::TextureUnitConfig')
	gen.bind_constructor_overloads(tex_unit_cfg, [
		([], []),
		(['gs::core::TextureUV wrap_u', 'gs::core::TextureUV wrap_v', 'gs::core::TextureFilter min_filter', 'gs::core::TextureFilter mag_filter'], []),
	])
	gen.bind_comparison_op(tex_unit_cfg, '==', ['const gs::core::TextureUnitConfig &config'])
	gen.bind_members(tex_unit_cfg, ['gs::core::TextureUV wrap_u:', 'gs::core::TextureUV wrap_v:', 'gs::core::TextureFilter min_filter:', 'gs::core::TextureFilter mag_filter:'])
	gen.end_class(tex_unit_cfg)

	# gs::core::VertexLayout
	gen.add_include('engine/vertex_layout.h')
	
	gen.bind_named_enum('gs::core::IndexType', ['IndexUByte', 'IndexUShort', 'IndexUInt'], storage_type='uint8_t')
	gen.bind_named_enum('gs::core::VertexType', ['VertexByte', 'VertexUByte', 'VertexShort', 'VertexUShort', 'VertexInt', 'VertexUInt', 'VertexFloat', 'VertexHalfFloat'], storage_type='uint8_t')

	vtx_layout = gen.begin_class('gs::core::VertexLayout')
	gen.bind_constructor(vtx_layout, [])
	gen.bind_method(vtx_layout, 'Clear', 'void', [])
	gen.bind_method(vtx_layout, 'AddAttribute', 'bool', ['gs::core::VertexAttribute::Semantic semantic', 'uint8_t count', 'gs::core::VertexType type', '?bool is_normalized'])
	gen.bind_method(vtx_layout, 'End', 'void', [])
	gen.end_class(vtx_layout)

	#
	gen.add_include('foundation/type_serialization.h')
	gen.add_include('engine/core_reflection.h')

	gen.insert_binding_code('''\
static std::shared_ptr<gs::core::Geometry> LoadCoreGeometry(const char *path) {
	std::shared_ptr<gs::core::Geometry> geo(new gs::core::Geometry);
	geo->name = path;

	gs::DeserializationContext ctx;
	if (gs::LoadResourceFromPath(path, *geo, gs::DocumentFormatUnknown, &ctx))
		return geo;
	return nullptr;
}

static bool SaveCoreGeometry(const char *path, const std::shared_ptr<gs::core::Geometry> &geo, gs::DocumentFormat format = gs::DocumentFormatUnknown) { 
	gs::SerializationContext ctx;
	return gs::SaveResourceToPath(path, *geo, format, &ctx);
}
''')

	gen.bind_function('LoadCoreGeometry', 'std::shared_ptr<gs::core::Geometry>', ['const char *path'])
	gen.bind_function('SaveCoreGeometry', 'bool', ['const char *path', 'const std::shared_ptr<gs::core::Geometry> &geometry', '?gs::DocumentFormat format'])


def bind_create_geometry(gen):
	gen.add_include('engine/create_geometry.h')

	gen.bind_function_overloads('gs::core::CreateCapsule', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_function_overloads('gs::core::CreateCone', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_function_overloads('gs::core::CreateCube', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float height'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float height', 'float length'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float height', 'float length', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float height', 'float length', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_function_overloads('gs::core::CreateCylinder', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_function_overloads('gs::core::CreatePlane', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float length'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float length', 'int subdiv_x'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float length', 'int subdiv_x', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float length', 'int subdiv_x', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_function_overloads('gs::core::CreateSphere', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y', 'const char *material_path', 'const char *name'], [])
	])


def bind_frame_renderer(gen):
	frame_renderer = gen.begin_class('gs::core::IFrameRenderer', bound_name='FrameRenderer_nobind', noncopyable=True, nobind=True)
	gen.end_class(frame_renderer)

	shared_frame_renderer = gen.begin_class('std::shared_ptr<gs::core::IFrameRenderer>', bound_name='FrameRenderer', features={'proxy': lib.stl.SharedPtrProxyFeature(frame_renderer)})
	gen.end_class(shared_frame_renderer)

	gen.insert_binding_code('''static std::shared_ptr<gs::core::IFrameRenderer> CreateFrameRenderer(const char *name) { return gs::core::g_frame_renderer_factory.get().Instantiate(name); }
static std::shared_ptr<gs::core::IFrameRenderer> CreateFrameRenderer() { return gs::core::g_frame_renderer_factory.get().Instantiate(); }
	''', 'Frame renderer custom API')

	gen.bind_function('CreateFrameRenderer', 'std::shared_ptr<gs::core::IFrameRenderer>', ['?const char *name'], {'check_rval': check_rval_lambda(gen, 'CreateFrameRenderer failed')}, 'GetFrameRenderer')


def bind_scene(gen):
	gen.add_include('engine/scene.h')
	gen.add_include('engine/node.h')

	# forward declarations
	node = gen.begin_class('gs::core::Node', bound_name='Node_nobind', noncopyable=True, nobind=True)
	gen.end_class(node)

	shared_node = gen.begin_class('std::shared_ptr<gs::core::Node>', bound_name='Node', features={'proxy': lib.stl.SharedPtrProxyFeature(node)})

	scene = gen.begin_class('gs::core::Scene', bound_name='Scene_nobind', noncopyable=True, nobind=True)
	gen.end_class(scene)

	shared_scene = gen.begin_class('std::shared_ptr<gs::core::Scene>', bound_name='Scene', features={'proxy': lib.stl.SharedPtrProxyFeature(scene)})

	scene_system = gen.begin_class('gs::core::SceneSystem', bound_name='SceneSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(scene_system)

	shared_scene_system = gen.begin_class('std::shared_ptr<gs::core::SceneSystem>', bound_name='SceneSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(scene_system)})

	gen.bind_named_enum('gs::core::ComponentState', ['NotReady', 'Ready', 'Failed'], storage_type='uint8_t')

	#
	def decl_get_set_method(conv, type, method_suffix, var_name, features=[]):
		gen.bind_method(conv, 'Get' + method_suffix, 'const %s' % type, [], features)
		gen.bind_method(conv, 'Set' + method_suffix, 'void', ['const %s &%s' % (type, var_name)], features)

	def decl_comp_get_set_method(conv, comp_type, comp_var_name, type, method_suffix, var_name, features=[]):
		gen.bind_method(conv, 'Get' + method_suffix, 'const %s &' % type, ['const %s *%s' % (comp_type, comp_var_name)], features)
		gen.bind_method(conv, 'Set' + method_suffix, 'void', ['%s *%s' % (comp_type, comp_var_name), 'const %s &%s' % (type, var_name)], features)

	# gs::core::Component
	gen.add_include('engine/component.h')

	gen.bind_named_enum('gs::core::ComponentState', ['NotReady', 'Ready', 'Failed'], storage_type='uint8_t')

	component = gen.begin_class('gs::core::Component', bound_name='Component_nobind', noncopyable=True, nobind=True)
	gen.end_class(component)

	shared_component = gen.begin_class('std::shared_ptr<gs::core::Component>', bound_name='Component', features={'proxy': lib.stl.SharedPtrProxyFeature(component)})

	gen.bind_method(shared_component, 'GetSceneSystem', 'std::shared_ptr<gs::core::SceneSystem>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'Component is not registered in a SceneSystem')})
	gen.bind_method(shared_component, 'GetScene', 'std::shared_ptr<gs::core::Scene>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'Component is not registered in a Scene')})
	gen.bind_method(shared_component, 'GetNode', 'std::shared_ptr<gs::core::Node>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'Component is not registered in a Node')})

	gen.bind_method(shared_component, 'IsAssigned', 'bool', [], ['proxy'])

	gen.bind_method(shared_component, 'GetEnabled', 'bool', [], ['proxy'])
	gen.bind_method(shared_component, 'SetEnabled', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_component, 'GetState', 'gs::core::ComponentState', [], ['proxy'])

	gen.bind_method(shared_component, 'GetAspect', 'const std::string &', [], ['proxy'])

	gen.bind_method(shared_component, 'GetDoNotSerialize', 'bool', [], ['proxy'])
	gen.bind_method(shared_component, 'SetDoNotSerialize', 'void', ['bool do_not_serialize'], ['proxy'])

	gen.bind_method(shared_component, 'GetShowInEditor', 'bool', [], ['proxy'])
	gen.bind_method(shared_component, 'SetShowInEditor', 'void', ['bool shown_in_editor'], ['proxy'])

	gen.bind_method(shared_component, 'GetRegisteredInScene', 'std::shared_ptr<gs::core::Scene>', [], ['proxy'])

	gen.end_class(shared_component)

	bind_std_vector(gen, shared_component)

	# gs::core::Instance
	gen.add_include('engine/instance.h')

	instance = gen.begin_class('gs::core::Instance', bound_name='Instance_nobind', noncopyable=True, nobind=True)
	gen.end_class(instance)

	shared_instance = gen.begin_class('std::shared_ptr<gs::core::Instance>', bound_name='Instance', features={'proxy': lib.stl.SharedPtrProxyFeature(instance)})
	gen.add_base(shared_instance, shared_component)

	gen.bind_constructor(shared_instance, [], ['proxy'])
	decl_get_set_method(shared_instance, 'std::string', 'Path', 'path', ['proxy'])
	gen.bind_method(shared_instance, 'GetState', 'gs::core::ComponentState', [], ['proxy'])

	gen.end_class(shared_instance)

	# gs::core::Target
	gen.add_include('engine/target.h')

	target = gen.begin_class('gs::core::Target', bound_name='Target_nobind', noncopyable=True, nobind=True)
	gen.end_class(target)

	shared_target = gen.begin_class('std::shared_ptr<gs::core::Target>', bound_name='Target', features={'proxy': lib.stl.SharedPtrProxyFeature(target)})
	gen.add_base(shared_target, shared_component)

	gen.bind_constructor(shared_target, [], ['proxy'])
	decl_get_set_method(shared_target, 'std::shared_ptr<gs::core::Node>', 'Target', 'target', ['proxy'])

	gen.end_class(shared_target)

	# gs::core::Environment
	gen.add_include('engine/environment.h')

	environment = gen.begin_class('gs::core::Environment', bound_name='Environment_nobind', noncopyable=True, nobind=True)
	gen.end_class(environment)

	shared_environment = gen.begin_class('std::shared_ptr<gs::core::Environment>', bound_name='Environment', features={'proxy': lib.stl.SharedPtrProxyFeature(environment)})
	gen.add_base(shared_environment, shared_component)

	gen.bind_constructor(shared_environment, [], ['proxy'])

	decl_get_set_method(shared_environment, 'float', 'TimeOfDay', 'time_of_day', ['proxy'])
	decl_get_set_method(shared_environment, 'gs::Color', 'BackgroundColor', 'background_color', ['proxy'])

	decl_get_set_method(shared_environment, 'float', 'AmbientIntensity', 'ambient_intensity', ['proxy'])
	decl_get_set_method(shared_environment, 'gs::Color', 'AmbientColor', 'ambient_color', ['proxy'])

	decl_get_set_method(shared_environment, 'gs::Color', 'FogColor', 'fog_color', ['proxy'])
	decl_get_set_method(shared_environment, 'float', 'FogNear', 'fog_near', ['proxy'])
	decl_get_set_method(shared_environment, 'float', 'FogFar', 'fog_far', ['proxy'])

	gen.end_class(shared_environment)

	# gs::core::SimpleGraphicSceneOverlay
	gen.add_include('engine/simple_graphic_scene_overlay.h')

	simple_graphic_scene_overlay = gen.begin_class('gs::core::SimpleGraphicSceneOverlay', bound_name='SimpleGraphicSceneOverlay_nobind', noncopyable=True, nobind=True)
	gen.end_class(simple_graphic_scene_overlay)

	shared_simple_graphic_scene_overlay = gen.begin_class('std::shared_ptr<gs::core::SimpleGraphicSceneOverlay>', bound_name='SimpleGraphicSceneOverlay', features={'proxy': lib.stl.SharedPtrProxyFeature(simple_graphic_scene_overlay)})
	gen.add_base(shared_simple_graphic_scene_overlay, shared_component)

	gen.bind_constructor_overloads(shared_simple_graphic_scene_overlay, [
		([], ['proxy']),
		(['bool is_2d_overlay'], ['proxy'])
	])

	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetSnapGlyphToGrid', 'void', ['bool snap'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetSnapGlyphToGrid', 'bool', [], ['proxy'])

	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetBlendMode', 'void', ['gs::render::BlendMode mode'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetBlendMode', 'gs::render::BlendMode', [], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetCullMode', 'void', ['gs::render::CullMode mode'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetCullMode', 'gs::render::CullMode', [], ['proxy'])

	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetDepthWrite', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetDepthWrite', 'bool', [], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetDepthTest', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetDepthTest', 'bool', [], ['proxy'])

	gen.bind_method(shared_simple_graphic_scene_overlay, 'Line', 'void', ['float sx', 'float sy', 'float sz', 'float ex', 'float ey', 'float ez', 'const gs::Color &start_color', 'const gs::Color &end_color'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'Triangle', 'void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'const gs::Color &a_color', 'const gs::Color &b_color', 'const gs::Color &c_color'], ['proxy'])
	gen.bind_method_overloads(shared_simple_graphic_scene_overlay, 'Text', [
		('void', ['float x', 'float y', 'float z', 'const char *text', 'const gs::Color &color', 'std::shared_ptr<gs::render::RasterFont> font', 'float scale'], ['proxy']),
		('void', ['const gs::Matrix4 &mat', 'const char *text', 'const gs::Color &color', 'std::shared_ptr<gs::render::RasterFont> font', 'float scale'], ['proxy'])
	])

	gen.insert_binding_code('''
static void _SimpleGraphicSceneOverlay_Quad(gs::core::SimpleGraphicSceneOverlay *overlay, float ax, float ay, float az, float bx, float by, float bz, float cx, float cy, float cz, float dx, float dy, float dz, const gs::Color &a_color, const gs::Color &b_color, const gs::Color &c_color, const gs::Color &d_color) {
	overlay->Quad(ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz, 0, 0, 1, 1, nullptr, a_color, b_color, c_color, d_color);
}
''')
	gen.bind_method_overloads(shared_simple_graphic_scene_overlay, 'Quad', [
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'const gs::Color &a_color', 'const gs::Color &b_color', 'const gs::Color &c_color', 'const gs::Color &d_color'], {'proxy': None, 'route': route_lambda('_SimpleGraphicSceneOverlay_Quad')}),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'float uv_sx', 'float uv_sy', 'float uv_ex', 'float uv_ey', 'std::shared_ptr<gs::gpu::Texture> texture', 'const gs::Color &a_color', 'const gs::Color &b_color', 'const gs::Color &c_color', 'const gs::Color &d_color'], ['proxy'])
	])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'Geometry', 'void', ['float x', 'float y', 'float z', 'float ex', 'float ey', 'float ez', 'float sx', 'float sy', 'float sz', 'std::shared_ptr<gs::render::Geometry> geometry'], ['proxy'])

	gen.end_class(shared_simple_graphic_scene_overlay)

	# gs::core::Transform
	gen.add_include('engine/transform.h')

	transform = gen.begin_class('gs::core::Transform', bound_name='Transform_nobind', noncopyable=True, nobind=True)
	gen.end_class(transform)

	shared_transform = gen.begin_class('std::shared_ptr<gs::core::Transform>', bound_name='Transform', features={'proxy': lib.stl.SharedPtrProxyFeature(transform)})
	gen.add_base(shared_transform, shared_component)

	gen.bind_constructor_overloads(shared_transform, [
		([], ['proxy']),
		(['const gs::Vector3 &pos', '?const gs::Vector3 &rot', '?const gs::Vector3 &scl'], ['proxy'])
	])

	gen.bind_method(shared_transform, 'GetParent', 'std::shared_ptr<gs::core::Node>', [], ['proxy'])
	gen.bind_method(shared_transform, 'SetParent', 'void', ['std::shared_ptr<gs::core::Node> parent'], ['proxy'])

	gen.bind_method(shared_transform, 'GetPreviousWorld', 'gs::Matrix4', [], ['proxy'])
	gen.bind_method(shared_transform, 'GetWorld', 'gs::Matrix4', [], ['proxy'])

	decl_get_set_method(shared_transform, 'gs::Vector3', 'Position', 'position', ['proxy'])
	decl_get_set_method(shared_transform, 'gs::Vector3', 'Rotation', 'rotation', ['proxy'])
	decl_get_set_method(shared_transform, 'gs::Vector3', 'Scale', 'scale', ['proxy'])

	gen.bind_method(shared_transform, 'SetRotationMatrix', 'void', ['const gs::Matrix3 &rotation'], ['proxy'])

	gen.bind_method(shared_transform, 'SetLocal', 'void', ['gs::Matrix4 &local'], ['proxy'])
	gen.bind_method(shared_transform, 'SetWorld', 'void', ['gs::Matrix4 &world'], ['proxy'])
	gen.bind_method(shared_transform, 'OffsetWorld', 'void', ['gs::Matrix4 &offset'], ['proxy'])

	gen.bind_method(shared_transform, 'TransformLocalPoint', 'gs::Vector3', ['const gs::Vector3 &local_point'], ['proxy'])
	gen.end_class(shared_transform)

	# gs::core::Camera
	gen.add_include('engine/camera.h')

	cam = gen.begin_class('gs::core::Camera', bound_name='Camera_nobind', noncopyable=True, nobind=True)
	gen.end_class(cam)

	shared_cam = gen.begin_class('std::shared_ptr<gs::core::Camera>', bound_name='Camera', features={'proxy': lib.stl.SharedPtrProxyFeature(cam)})
	gen.add_base(shared_cam, shared_component)

	gen.bind_constructor(shared_cam, [], ['proxy'])

	decl_get_set_method(shared_cam, 'float', 'ZoomFactor', 'zoom_factor', ['proxy'])
	decl_get_set_method(shared_cam, 'float', 'ZNear', 'z_near', ['proxy'])
	decl_get_set_method(shared_cam, 'float', 'ZFar', 'z_far', ['proxy'])

	decl_get_set_method(shared_cam, 'bool', 'Orthographic', 'is_orthographic', ['proxy'])
	decl_get_set_method(shared_cam, 'float', 'OrthographicSize', 'orthographic_size', ['proxy'])

	gen.bind_method(shared_cam, 'GetProjectionMatrix', 'gs::Matrix44', ['const gs::tVector2<float> &aspect_ratio'], ['proxy'])
	gen.end_class(shared_cam)

	gen.bind_function('gs::core::Project', 'bool', ['const gs::Matrix4 &camera_world', 'float zoom_factor', 'const gs::tVector2<float> &aspect_ratio', 'const gs::Vector3 &position', 'gs::Vector3 &out'], {'arg_out': ['out']})
	gen.bind_function('gs::core::Unproject', 'bool', ['const gs::Matrix4 &camera_world', 'float zoom_factor', 'const gs::tVector2<float> &aspect_ratio', 'const gs::Vector3 &position', 'gs::Vector3 &out'], {'arg_out': ['out']})

	gen.bind_function('gs::core::ExtractZoomFactorFromProjectionMatrix', 'float', ['const gs::Matrix44 &projection_matrix'])
	gen.bind_function('gs::core::ExtractZRangeFromProjectionMatrix', 'void', ['const gs::Matrix44 &projection_matrix', 'float &znear', 'float &zfar'], {'arg_out': ['znear', 'zfar']})

	# gs::core::Object
	gen.add_include('engine/object.h')

	obj = gen.begin_class('gs::core::Object', bound_name='Object_nobind', noncopyable=True, nobind=True)
	gen.end_class(obj)

	shared_obj = gen.begin_class('std::shared_ptr<gs::core::Object>', bound_name='Object', features={'proxy': lib.stl.SharedPtrProxyFeature(obj)})
	gen.add_base(shared_obj, shared_component)

	gen.bind_constructor(shared_obj, [], ['proxy'])

	gen.bind_method(shared_obj, 'GetState', 'gs::core::ComponentState', [], ['proxy'])

	decl_get_set_method(shared_obj, 'std::shared_ptr<gs::render::Geometry>', 'Geometry', 'geometry', ['proxy'])

	gen.bind_method(shared_obj, 'GetLocalMinMax', 'gs::MinMax', [], ['proxy'])

	gen.bind_method(shared_obj, 'GetBindMatrix', 'bool', ['gs::uint index', 'gs::Matrix4 &bind_matrix'], ['proxy'])
	gen.bind_method(shared_obj, 'HasSkeleton', 'bool', [], ['proxy'])
	gen.bind_method(shared_obj, 'IsSkinBound', 'bool', [], ['proxy'])

	gen.bind_method(shared_obj, 'GetBoneCount', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_obj, 'GetBone', 'const std::shared_ptr<gs::core::Node> &', ['gs::uint index'], ['proxy'])
	gen.end_class(shared_obj)

	# gs::core::Light
	gen.add_include('engine/light.h')

	gen.bind_named_enum('gs::core::Light::Model', ['ModelPoint', 'ModelLinear', 'ModelSpot', 'ModelLast'], prefix='Light')
	gen.bind_named_enum('gs::core::Light::Shadow', ['ShadowNone', 'ShadowProjectionMap', 'ShadowMap'], prefix='Light')

	light = gen.begin_class('gs::core::Light', bound_name='Light_nobind', noncopyable=True, nobind=True)
	gen.end_class(light)

	shared_light = gen.begin_class('std::shared_ptr<gs::core::Light>', bound_name='Light', features={'proxy': lib.stl.SharedPtrProxyFeature(light)})
	gen.add_base(shared_light, shared_component)

	gen.bind_constructor(shared_light, [], ['proxy'])

	decl_get_set_method(shared_light, 'gs::core::Light::Model', 'Model', ' model', ['proxy'])
	decl_get_set_method(shared_light, 'gs::core::Light::Shadow', 'Shadow', ' shadow', ['proxy'])
	decl_get_set_method(shared_light, 'bool', 'ShadowCastAll', ' shadow_cast_all', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ShadowRange', ' shadow_range', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ShadowBias', ' shadow_bias', ['proxy'])
	decl_get_set_method(shared_light, 'gs::Vector4', 'ShadowSplit', ' shadow_split', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ZNear', ' z_near', ['proxy'])

	decl_get_set_method(shared_light, 'float', 'Range', ' range', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ClipDistance', ' clip_distance', ['proxy'])

	decl_get_set_method(shared_light, 'gs::Color', 'DiffuseColor', ' diffuse_color', ['proxy'])
	decl_get_set_method(shared_light, 'gs::Color', 'SpecularColor', ' specular_color', ['proxy'])
	decl_get_set_method(shared_light, 'gs::Color', 'ShadowColor', ' shadow_color', ['proxy'])

	decl_get_set_method(shared_light, 'float', 'DiffuseIntensity', ' diffuse_intensity', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'SpecularIntensity', ' specular_intensity', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ConeAngle', ' cone_angle', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'EdgeAngle', ' edge_angle', ['proxy'])

	decl_get_set_method(shared_light, 'std::shared_ptr<gs::gpu::Texture>', 'ProjectionTexture', ' projection_texture', ['proxy'])

	gen.end_class(shared_light)

	# gs::core::RigidBody
	gen.add_include('engine/rigid_body.h')

	gen.bind_named_enum('gs::core::RigidBodyType', ['RigidBodyDynamic', 'RigidBodyKinematic', 'RigidBodyStatic'])

	rigid_body = gen.begin_class('gs::core::RigidBody', bound_name='RigidBody_nobind', noncopyable=True, nobind=True)
	gen.end_class(rigid_body)

	shared_rigid_body = gen.begin_class('std::shared_ptr<gs::core::RigidBody>', bound_name='RigidBody', features={'proxy': lib.stl.SharedPtrProxyFeature(rigid_body)})
	gen.add_base(shared_rigid_body, shared_component)

	gen.bind_constructor(shared_rigid_body, [], ['proxy'])

	decl_get_set_method(shared_rigid_body, 'bool', 'IsSleeping', 'is_sleeping', ['proxy'])

	gen.bind_method(shared_rigid_body, 'GetVelocity', 'const gs::Vector3', ['const gs::Vector3 &position'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'SetVelocity', 'void', ['const gs::Vector3 &V', 'const gs::Vector3 &position'], ['proxy'])

	decl_get_set_method(shared_rigid_body, 'gs::Vector3', 'LinearVelocity', 'V', ['proxy'])
	decl_get_set_method(shared_rigid_body, 'gs::Vector3', 'AngularVelocity', 'W', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'float', 'LinearDamping', 'damping', ['proxy'])
	decl_get_set_method(shared_rigid_body, 'float', 'AngularDamping', 'damping', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'float', 'StaticFriction', 'sF', ['proxy'])
	decl_get_set_method(shared_rigid_body, 'float', 'DynamicFriction', 'dF', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'float', 'Restitution', 'restitution', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'gs::core::RigidBodyType', 'Type', 'type', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'int', 'AxisLock', 'axis_lock', ['proxy'])
	decl_get_set_method(shared_rigid_body, 'int', 'CollisionLayer', 'layer', ['proxy'])

	gen.bind_method(shared_rigid_body, 'ApplyLinearImpulse', 'void', ['const gs::Vector3 &I'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'ApplyLinearForce', 'void', ['const gs::Vector3 &F'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'ApplyImpulse', 'void', ['const gs::Vector3 &I', 'const gs::Vector3 &position'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'ApplyForce', 'void', ['const gs::Vector3 &F', 'const gs::Vector3 &position'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'ApplyTorque', 'void', ['const gs::Vector3 &T'], ['proxy'])

	gen.bind_method(shared_rigid_body, 'ResetWorld', 'void', ['const gs::Matrix4 &m'], ['proxy'])

	gen.end_class(shared_rigid_body)

	# gs::core::BoxCollision
	gen.add_include('engine/box_collision.h')

	box_collision = gen.begin_class('gs::core::BoxCollision', bound_name='BoxCollision_nobind', noncopyable=True, nobind=True)
	gen.end_class(box_collision)

	shared_box_collision = gen.begin_class('std::shared_ptr<gs::core::BoxCollision>', bound_name='BoxCollision', features={'proxy': lib.stl.SharedPtrProxyFeature(box_collision)})
	gen.add_base(shared_box_collision, shared_component)
	gen.bind_constructor(shared_box_collision, [], ['proxy'])
	decl_get_set_method(shared_box_collision, 'gs::Vector3', 'Dimensions', 'dimensions', ['proxy'])
	gen.end_class(shared_box_collision)	

	# gs::core::MeshCollision
	gen.add_include('engine/mesh_collision.h')

	mesh_collision = gen.begin_class('gs::core::MeshCollision', bound_name='MeshCollision_nobind', noncopyable=True, nobind=True)
	gen.end_class(mesh_collision)

	shared_mesh_collision = gen.begin_class('std::shared_ptr<gs::core::MeshCollision>', bound_name='MeshCollision', features={'proxy': lib.stl.SharedPtrProxyFeature(mesh_collision)})
	gen.add_base(shared_mesh_collision, shared_component)
	gen.bind_constructor(shared_mesh_collision, [], ['proxy'])
	decl_get_set_method(shared_mesh_collision, 'std::shared_ptr<gs::core::Geometry>', 'Geometry', 'geometry', ['proxy'])
	gen.end_class(shared_mesh_collision)	

	# gs::core::Terrain
	gen.add_include('engine/terrain.h')

	terrain = gen.begin_class('gs::core::Terrain', bound_name='Terrain_nobind', noncopyable=True, nobind=True)
	gen.end_class(terrain)

	shared_terrain = gen.begin_class('std::shared_ptr<gs::core::Terrain>', bound_name='Terrain', features={'proxy': lib.stl.SharedPtrProxyFeature(terrain)})
	gen.add_base(shared_terrain, shared_component)

	gen.bind_constructor(shared_terrain, [], ['proxy'])

	decl_get_set_method(shared_terrain, 'std::string', 'Heightmap', 'heightmap', ['proxy'])
	decl_get_set_method(shared_terrain, 'gs::tVector2<int>', 'HeightmapResolution', 'heightmap_resolution', ['proxy'])
	decl_get_set_method(shared_terrain, 'gs::uint', 'HeightmapBpp', 'heightmap_bpp', ['proxy'])

	decl_get_set_method(shared_terrain, 'gs::Vector3', 'Size', 'size', ['proxy'])

	decl_get_set_method(shared_terrain, 'std::string', 'SurfaceShader', 'surface_shader', ['proxy'])

	decl_get_set_method(shared_terrain, 'int', 'PatchSubdivisionThreshold', 'patch_subdv_threshold', ['proxy'])
	decl_get_set_method(shared_terrain, 'int', 'MaxRecursion', 'max_recursion', ['proxy'])
	decl_get_set_method(shared_terrain, 'float', 'MinPrecision', 'min_precision', ['proxy'])

	decl_get_set_method(shared_terrain, 'bool', 'Wireframe', 'wireframe', ['proxy'])

	gen.end_class(shared_terrain)

	# gs::core::ScriptEngineEnv
	gen.add_include('engine/script_system.h')

	script_env = gen.begin_class('gs::core::ScriptEngineEnv', bound_name='ScriptEnv_nobind', noncopyable=True, nobind=True)
	gen.end_class(script_env)

	shared_script_env = gen.begin_class('std::shared_ptr<gs::core::ScriptEngineEnv>', bound_name='ScriptEnv', features={'proxy': lib.stl.SharedPtrProxyFeature(script_env)})
	gen.bind_constructor(shared_script_env, ['std::shared_ptr<gs::render::RenderSystemAsync> render_system_async', 'std::shared_ptr<gs::gpu::RendererAsync> renderer_async', 'std::shared_ptr<gs::audio::MixerAsync> mixer'], ['proxy'])
	gen.bind_member(shared_script_env, 'float dt', ['proxy'])
	gen.end_class(shared_script_env)

	# gs::core::Script
	gen.bind_named_enum('gs::core::ScriptExecutionContext::Type', ['Standalone', 'Editor', 'All'], prefix='ScriptContext', bound_name='ScriptExecutionContext', namespace='gs::core::ScriptExecutionContext')

	script = gen.begin_class('gs::core::Script', bound_name='Script_nobind', noncopyable=True, nobind=True)
	gen.end_class(script)

	shared_script = gen.begin_class('std::shared_ptr<gs::core::Script>', bound_name='Script', features={'proxy': lib.stl.SharedPtrProxyFeature(script)})
	gen.add_base(shared_script, shared_component)

	gen.bind_method(shared_script, 'BlockingGet', 'gs::TypeValue', ['const char *name'], ['proxy'])

	gen.bind_method(shared_script, 'Get', 'gs::TypeValue', ['const char *name'], ['proxy'])
	gen.bind_method(shared_script, 'Set', 'void', ['const char *name', 'const gs::TypeValue &value'], ['proxy'])

	gen.bind_method(shared_script, 'Expose', 'void', ['const char *name', 'const gs::TypeValue &value'], ['proxy'])
	gen.bind_method(shared_script, 'Call', 'void', ['const char *name', 'const std::vector<gs::TypeValue> &parms'], ['proxy'])

	gen.end_class(shared_script)

	# gs::core::RenderScript
	render_script = gen.begin_class('gs::core::RenderScript', bound_name='RenderScript_nobind', noncopyable=True, nobind=True)
	gen.end_class(render_script)

	shared_render_script = gen.begin_class('std::shared_ptr<gs::core::RenderScript>', bound_name='RenderScript', features={'proxy': lib.stl.SharedPtrProxyFeature(render_script)})
	gen.add_base(shared_render_script, shared_script)
	gen.bind_constructor(shared_render_script, ['?const char *path'], ['proxy'])
	gen.end_class(shared_render_script)

	# gs::core::LogicScript
	logic_script = gen.begin_class('gs::core::LogicScript', bound_name='LogicScript_nobind', noncopyable=True, nobind=True)
	gen.end_class(logic_script)

	shared_logic_script = gen.begin_class('std::shared_ptr<gs::core::LogicScript>', bound_name='LogicScript', features={'proxy': lib.stl.SharedPtrProxyFeature(logic_script)})
	gen.add_base(shared_logic_script, shared_script)
	gen.bind_constructor(shared_logic_script, ['?const char *path'], ['proxy'])
	gen.end_class(shared_logic_script)

	# gs::core::ScriptSystem
	script_system = gen.begin_class('gs::core::ScriptSystem', bound_name='ScriptSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(script_system)

	shared_script_system = gen.begin_class('std::shared_ptr<gs::core::ScriptSystem>', bound_name='ScriptSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(script_system)})
	gen.add_base(shared_script_system, shared_scene_system)

	gen.bind_method(shared_script_system, 'GetExecutionContext', 'gs::core::ScriptExecutionContext::Type', [], ['proxy'])
	gen.bind_method(shared_script_system, 'SetExecutionContext', 'void', ['gs::core::ScriptExecutionContext::Type ctx'], ['proxy'])

	gen.bind_method(shared_script_system, 'TestScriptIsReady', 'bool', ['const gs::core::Script &script'], ['proxy'])

	gen.bind_method(shared_script_system, 'GetImplementationName', 'const std::string &', [], ['proxy'])

	gen.bind_method(shared_script_system, 'Open', 'bool', [], ['proxy'])
	gen.bind_method(shared_script_system, 'Close', 'void', [], ['proxy'])

	gen.bind_method(shared_script_system, 'Reset', 'void', [], ['proxy'])

	gen.end_class(shared_script_system)

	# gs::core::LuaSystem
	gen.add_include('engine/lua_system.h')

	lua_system = gen.begin_class('gs::script::LuaSystem', bound_name='LuaSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(lua_system)

	shared_lua_system = gen.begin_class('std::shared_ptr<gs::script::LuaSystem>', bound_name='LuaSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(lua_system)})
	gen.add_base(shared_lua_system, shared_script_system)
	gen.bind_constructor(shared_lua_system, ['?std::shared_ptr<gs::core::ScriptEngineEnv> environment'], ['proxy'])
	gen.end_class(shared_lua_system)

	# gs::core::Node
	gen.bind_constructor_overloads(shared_node, [
		([], ['proxy']),
		(['const char *name'], ['proxy'])
	])

	gen.bind_method(shared_node, 'GetScene', 'std::shared_ptr<gs::core::Scene>', [], ['proxy'])
	gen.bind_method(shared_node, 'GetUid', 'gs::uint', [], ['proxy'])

	gen.bind_method(shared_node, 'GetName', 'const std::string &', [], ['proxy'])
	gen.bind_method(shared_node, 'SetName', 'void', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_node, 'AddComponent', 'void', ['std::shared_ptr<gs::core::Component> component'], ['proxy'])
	gen.bind_method(shared_node, 'RemoveComponent', 'void', ['const std::shared_ptr<gs::core::Component> &component'], ['proxy'])

	gen.bind_method_overloads(shared_node, 'GetComponents', [
		('const std::vector<std::shared_ptr<gs::core::Component>> &', [], ['proxy']),
		('std::vector<std::shared_ptr<gs::core::Component>>', ['const char *aspect'], ['proxy'])
	])

	gen.bind_method(shared_node, 'GetComponent<gs::core::Transform>', 'std::shared_ptr<gs::core::Transform>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'GetTransform failed, node has no Transform component')}, bound_name='GetTransform')
	gen.bind_method(shared_node, 'GetComponent<gs::core::Camera>', 'std::shared_ptr<gs::core::Camera>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'GetCamera failed, node has no Camera component')}, bound_name='GetCamera')
	gen.bind_method(shared_node, 'GetComponent<gs::core::Object>', 'std::shared_ptr<gs::core::Object>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'GetObject failed, node has no Object component')}, bound_name='GetObject')
	gen.bind_method(shared_node, 'GetComponent<gs::core::Light>', 'std::shared_ptr<gs::core::Light>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'GetLight failed, node has no Light component')}, bound_name='GetLight')
	gen.bind_method(shared_node, 'GetComponent<gs::core::Instance>', 'std::shared_ptr<gs::core::Instance>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'GetInstance failed, node has no Instance component')}, bound_name='GetInstance')
	gen.bind_method(shared_node, 'GetComponent<gs::core::Target>', 'std::shared_ptr<gs::core::Target>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'GetTarget failed, node has no Target component')}, bound_name='GetTarget')

	gen.bind_method(shared_node, 'HasAspect', 'bool', ['const char *aspect'], ['proxy'])
	gen.bind_method(shared_node, 'IsReady', 'bool', [], ['proxy'])

	gen.bind_method(shared_node, 'IsInstantiated', 'bool', [], ['proxy'])

	decl_get_set_method(shared_node, 'bool', 'Enabled', 'enable', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'IsStatic', 'is_static', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'DoNotSerialize', 'do_not_serialize', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'DoNotInstantiate', 'do_not_instantiate', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'UseForNavigation', 'use_for_navigation', features=['proxy'])

	gen.bind_method_overloads(shared_node, 'GetNode', [
		('std::shared_ptr<gs::core::Node>', ['gs::uint uid'], ['proxy']),
		('std::shared_ptr<gs::core::Node>', ['const char *name', '?const std::shared_ptr<gs::core::Node> &node'], ['proxy'])
	])

	gen.end_class(shared_node)

	bind_std_vector(gen, shared_node)

	# gs::core::SceneSystem
	gen.bind_method(shared_scene_system, 'GetAspect', 'const std::string &', [], ['proxy'])

	#inline Type *GetConcreteType() const { return concrete_type; }

	gen.bind_method(shared_scene_system, 'Update', 'void', ['gs::time_ns dt'], ['proxy'])
	gen.bind_method_overloads(shared_scene_system, 'WaitUpdate', [
		('bool', [], ['proxy']),
		('bool', ['bool blocking'], ['proxy'])
	])
	gen.bind_method(shared_scene_system, 'Commit', 'void', [], ['proxy'])
	gen.bind_method_overloads(shared_scene_system, 'WaitCommit', [
		('bool', [], ['proxy']),
		('bool', ['bool blocking'], ['proxy'])
	])

	gen.bind_method(shared_scene_system, 'AddComponent', 'void', ['std::shared_ptr<gs::core::Component> component'], ['proxy'])
	gen.bind_method(shared_scene_system, 'RemoveComponent', 'void', ['const std::shared_ptr<gs::core::Component> &component'], ['proxy'])

	gen.bind_method(shared_scene_system, 'Cleanup', 'void', [], ['proxy'])

	gen.bind_method(shared_scene_system, 'SetDebugVisuals', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_scene_system, 'GetDebugVisuals', 'bool', [], ['proxy'])

	gen.bind_method(shared_scene_system, 'DrawDebugPanel', 'void', ['gs::render::RenderSystem &render_system'], ['proxy'])
	gen.bind_method(shared_scene_system, 'DrawDebugVisuals', 'void', ['gs::render::RenderSystem &render_system'], ['proxy'])

	gen.end_class(shared_scene_system)

	# gs::core::RenderableSystem
	gen.add_include('engine/renderable_system.h')

	renderable_system = gen.begin_class('gs::core::RenderableSystem', bound_name='RenderableSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(renderable_system)

	shared_renderable_system = gen.begin_class('std::shared_ptr<gs::core::RenderableSystem>', bound_name='RenderableSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(renderable_system)})
	gen.add_base(shared_renderable_system, shared_scene_system)

	gen.bind_constructor_overloads(shared_renderable_system, [
		(['std::shared_ptr<gs::render::RenderSystem> render_system'], ['proxy']),
		(['std::shared_ptr<gs::render::RenderSystem> render_system', 'bool async'], ['proxy'])
	])

	gen.bind_method(shared_renderable_system, 'DrawGeometry', 'void', ['std::shared_ptr<gs::render::Geometry> geometry', 'const gs::Matrix4 &world'], ['proxy'])

	gen.end_class(shared_renderable_system)

	# gs::core::PhysicTrace
	gen.add_include('engine/physic_system.h')

	physic_trace = gen.begin_class('gs::core::PhysicTrace')
	gen.insert_binding_code('''\
static gs::Vector3 PhysicTraceGetPosition(gs::core::PhysicTrace *trace) { return trace->p; }
static gs::Vector3 PhysicTraceGetNormal(gs::core::PhysicTrace *trace) { return trace->n; }
static std::shared_ptr<gs::core::Node> PhysicTraceGetNode(gs::core::PhysicTrace *trace) { return trace->i->shared_from_this(); }
\n''', 'PhysicTrace extension')
	gen.bind_method(physic_trace, 'GetPosition', 'gs::Vector3', [], {'route': route_lambda('PhysicTraceGetPosition')})
	gen.bind_method(physic_trace, 'GetNormal', 'gs::Vector3', [], {'route': route_lambda('PhysicTraceGetNormal')})
	gen.bind_method(physic_trace, 'GetNode', 'std::shared_ptr<gs::core::Node>', [], {'route': route_lambda('PhysicTraceGetNode')})
	gen.end_class(physic_trace)

	# gs::core::IPhysicSystem
	physic_system = gen.begin_class('gs::core::IPhysicSystem', bound_name='PhysicSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(physic_system)

	shared_physic_system = gen.begin_class('std::shared_ptr<gs::core::IPhysicSystem>', bound_name='PhysicSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(physic_system)})
	gen.add_base(shared_physic_system, shared_scene_system)

	gen.bind_method(shared_physic_system, 'GetImplementationName', 'const std::string &', [], ['proxy'])

	decl_get_set_method(shared_physic_system, 'float', 'Timestep', 'timestep', ['proxy'])
	decl_get_set_method(shared_physic_system, 'bool', 'ForceRigidBodyToSleepOnCreation', 'force_sleep_body', ['proxy'])
	decl_get_set_method(shared_physic_system, 'gs::uint', 'ForceRigidBodyAxisLockOnCreation', 'force_axis_lock', ['proxy'])

	decl_get_set_method(shared_physic_system, 'gs::Vector3', 'Gravity', 'G', ['proxy'])

	gen.bind_method_overloads(shared_physic_system, 'Raycast', [
		('bool', ['const gs::Vector3 &start', 'const gs::Vector3 &direction', 'gs::core::PhysicTrace &hit'], {'proxy': None, 'arg_out': ['hit']}),
		('bool', ['const gs::Vector3 &start', 'const gs::Vector3 &direction', 'gs::core::PhysicTrace &hit', 'uint8_t collision_layer_mask'], {'proxy': None, 'arg_out': ['hit']}),
		('bool', ['const gs::Vector3 &start', 'const gs::Vector3 &direction', 'gs::core::PhysicTrace &hit', 'uint8_t collision_layer_mask', 'float max_distance'], {'proxy': None, 'arg_out': ['hit']})
	])

	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'bool', 'RigidBodyIsSleeping', 'sleeping', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'gs::Vector3', 'RigidBodyAngularVelocity', 'W', ['proxy'])
	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'gs::Vector3', 'RigidBodyLinearVelocity', 'V', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'float', 'RigidBodyLinearDamping', 'k', ['proxy'])
	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'float', 'RigidBodyAngularDamping', 'k', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'float', 'RigidBodyStaticFriction', 'static_friction', ['proxy'])
	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'float', 'RigidBodyDynamicFriction', 'dynamic_friction', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'float', 'RigidBodyRestitution', 'restitution', ['proxy'])

	#decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'gs::RigidBodyType', 'RigidBodyType', 'type', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'uint8_t', 'RigidBodyAxisLock', 'axis_lock', ['proxy'])
	decl_comp_get_set_method(shared_physic_system, 'gs::core::RigidBody', 'rigid_body', 'uint8_t', 'RigidBodyCollisionLayer', 'layer', ['proxy'])

	gen.bind_method(shared_physic_system, 'GetRigidBodyVelocity', 'gs::Vector3', ['const gs::core::RigidBody *body', 'const gs::Vector3 &p'], ['proxy'])
	gen.bind_method(shared_physic_system, 'SetRigidBodyVelocity', 'void', ['gs::core::RigidBody *body', 'const gs::Vector3 &V', 'const gs::Vector3 &p'], ['proxy'])

	gen.bind_method(shared_physic_system, 'RigidBodyApplyLinearImpulse', 'void', ['gs::core::RigidBody *body', 'const gs::Vector3 &I'], ['proxy'])
	gen.bind_method(shared_physic_system, 'RigidBodyApplyLinearForce', 'void', ['gs::core::RigidBody *body', 'const gs::Vector3 &F'], ['proxy'])
	gen.bind_method(shared_physic_system, 'RigidBodyApplyTorque', 'void', ['gs::core::RigidBody *body', 'const gs::Vector3 &T'], ['proxy'])

	gen.bind_method(shared_physic_system, 'RigidBodyApplyImpulse', 'void', ['gs::core::RigidBody *body', 'const gs::Vector3 &I', 'const gs::Vector3 &p'], ['proxy'])
	gen.bind_method(shared_physic_system, 'RigidBodyApplyForce', 'void', ['gs::core::RigidBody *body', 'const gs::Vector3 &F', 'const gs::Vector3 &p'], ['proxy'])

	gen.bind_method(shared_physic_system, 'RigidBodyResetWorld', 'void', ['gs::core::RigidBody *body', 'const gs::Matrix4 &M'], ['proxy'])

	"""
	void OnCollisionModified(const sCollision &collision);
	void OnJointModified(const sJoint &joint);

	/// Return collision pairs for the last update.
	const std::vector<CollisionPair> &GetCollisionPairs() const { return collision_pairs[current_collision_pair_array_index]; }
	/// Return collision pairs involving a specific node for the last update.
	std::vector<CollisionPair> GetCollisionPairs(const sNode &node) const;
	"""

	gen.bind_method_overloads(shared_physic_system, 'HasCollided', [
		('bool', ['const std::shared_ptr<gs::core::Node> &node'], ['proxy']),
		('bool', ['const std::shared_ptr<gs::core::Node> &node_a', 'const std::shared_ptr<gs::core::Node> &node_b'], ['proxy'])
	])

	gen.bind_method(shared_physic_system, 'SetCollisionLayerPairState', 'void', ['uint16_t layer_a', 'uint16_t layer_b', 'bool enable_collision'], ['proxy'])
	gen.bind_method(shared_physic_system, 'GetCollisionLayerPairState', 'bool', ['uint16_t layer_a', 'uint16_t layer_b'], ['proxy'])

	gen.end_class(shared_physic_system)

	gen.insert_binding_code('''static std::shared_ptr<gs::core::IPhysicSystem> CreatePhysicSystem(const char *name) { return gs::core::g_physic_system_factory.get().Instantiate(name); }
static std::shared_ptr<gs::core::IPhysicSystem> CreatePhysicSystem() { return gs::core::g_physic_system_factory.get().Instantiate(); }
	''', 'Physic system custom API')

	gen.bind_function('CreatePhysicSystem', 'std::shared_ptr<gs::core::IPhysicSystem>', ['?const char *name'], {'check_rval': check_rval_lambda(gen, 'CreatePhysicSystem failed, was LoadPlugins called succesfully?')})

	# gs::core::NavigationPath
	gen.add_include('engine/navigation_system.h')

	navigation_path = gen.begin_class('gs::core::NavigationPath')
	gen.bind_member(navigation_path, 'const std::vector<gs::Vector3> point')
	gen.end_class(navigation_path)

	# gs::core::NavigationLayer
	navigation_layer = gen.begin_class('gs::core::NavigationLayer')
	gen.bind_members(navigation_layer, ['float radius', 'float height', 'float slope'])
	gen.bind_comparison_ops(navigation_layer, ['==', '!='], ['const gs::core::NavigationLayer &layer'])
	gen.end_class(navigation_layer)

	bind_std_vector(gen, navigation_layer)

	# gs::core::NavigationConfig
	navigation_config = gen.begin_class('gs::core::NavigationConfig')
	gen.bind_member(navigation_config, 'std::vector<gs::core::NavigationLayer> layers')
	gen.end_class(navigation_config)

	# gs::core::NavigationSystem
	navigation_system = gen.begin_class('gs::core::NavigationSystem', bound_name='NavigationSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(navigation_system)

	shared_navigation_system = gen.begin_class('std::shared_ptr<gs::core::NavigationSystem>', bound_name='NavigationSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(navigation_system)})
	gen.add_base(shared_navigation_system, shared_scene_system)

	gen.bind_constructor(shared_navigation_system, [], ['proxy'])
	gen.bind_method_overloads(shared_navigation_system, 'FindPathTo', [
		('bool', ['const gs::Vector3 &from', 'const gs::Vector3 &to', 'gs::core::NavigationPath &path'], ['proxy']),
		('bool', ['const gs::Vector3 &from', 'const gs::Vector3 &to', 'gs::core::NavigationPath &path', 'gs::uint layer_index'], ['proxy'])
	])
	gen.bind_method(shared_navigation_system, 'GetConfig', 'const gs::core::NavigationConfig &', [], ['proxy'])
	gen.end_class(shared_navigation_system)

	# gs::core::Group
	gen.add_include('engine/group.h')

	group = gen.begin_class('gs::core::Group', bound_name='Group_nobind', noncopyable=True, nobind=True)
	gen.end_class(group)

	shared_group = gen.begin_class('std::shared_ptr<gs::core::Group>', bound_name='Group', features={'proxy': lib.stl.SharedPtrProxyFeature(group)})

	std_vector_shared_group = gen.begin_class('std::vector<std::shared_ptr<gs::core::Group>>', bound_name='GroupList', features={'sequence': lib.std.VectorSequenceFeature(shared_group)})
	gen.end_class(std_vector_shared_group)

	gen.bind_method(shared_group, 'GetNodes', 'const std::vector<std::shared_ptr<gs::core::Node>> &', [], ['proxy'])
	gen.bind_method(shared_group, 'GetGroups', 'const std::vector<std::shared_ptr<gs::core::Group>> &', [], ['proxy'])

	gen.bind_method(shared_group, 'AddNode', 'void', ['std::shared_ptr<gs::core::Node> node'], ['proxy'])
	gen.bind_method(shared_group, 'RemoveNode', 'void', ['const std::shared_ptr<gs::core::Node> &node'], ['proxy'])
	gen.bind_method_overloads(shared_group, 'IsMember', [
		('bool', ['const std::shared_ptr<gs::core::Node> &node'], ['proxy']),
		('bool', ['const std::shared_ptr<gs::core::Group> &group'], ['proxy'])
	])

	gen.bind_method(shared_group, 'IsReady', 'bool', [], ['proxy'])

	gen.bind_method_overloads(shared_group, 'GetNode', [
		('std::shared_ptr<gs::core::Node>', ['uint32_t uid'], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'Node not found')}),
		('std::shared_ptr<gs::core::Node>', ['const char *name', '?const std::shared_ptr<gs::core::Node> &parent'], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'Node not found')})
	])

	gen.bind_method(shared_group, 'AddGroup', 'void', ['std::shared_ptr<gs::core::Group> group'], ['proxy'])
	gen.bind_method(shared_group, 'RemoveGroup', 'void', ['const std::shared_ptr<gs::core::Group> &group'], ['proxy'])

	gen.bind_method(shared_group, 'GetGroup', 'std::shared_ptr<gs::core::Group>', ['const char *name'], ['proxy'])

	gen.bind_method(shared_group, 'AppendGroup', 'void', ['const gs::core::Group &group'], ['proxy'])

	gen.bind_method(shared_group, 'GetName', 'const std::string &', [], ['proxy'])
	gen.bind_method(shared_group, 'SetName', 'void', ['const char *name'], ['proxy'])

	gen.end_class(shared_group)

	# gs::core::Scene
	gen.bind_constructor(shared_scene, [], ['proxy'])

	gen.bind_method(shared_scene, 'GetCurrentCamera', 'const std::shared_ptr<gs::core::Node> &', [], ['proxy'])
	gen.bind_method(shared_scene, 'SetCurrentCamera', 'void', ['std::shared_ptr<gs::core::Node> node'], ['proxy'])

	gen.bind_method(shared_scene, 'AddGroup', 'void', ['std::shared_ptr<gs::core::Group> group'], ['proxy'])
	gen.bind_method(shared_scene, 'RemoveGroup', 'void', ['const std::shared_ptr<gs::core::Group> &group'], ['proxy'])
	gen.bind_method(shared_scene, 'FindGroup', 'std::shared_ptr<gs::core::Group>', ['const char *name'], ['proxy'])

	gen.bind_method(shared_scene, 'GetNodeGroupList', 'std::vector<std::shared_ptr<gs::core::Group>>', ['const std::shared_ptr<gs::core::Node> &node'], ['proxy'])
	gen.bind_method(shared_scene, 'UnregisterNodeFromGroups', 'void', ['const std::shared_ptr<gs::core::Node> &node'], ['proxy'])
	gen.bind_method(shared_scene, 'GetGroups', 'const std::vector<std::shared_ptr<gs::core::Group>> &', [], ['proxy'])

	gen.bind_method(shared_scene, 'GroupMembersSetActive', 'void', ['const gs::core::Group &group', 'bool active'], ['proxy'])
	gen.bind_method(shared_scene, 'DeleteGroupAndMembers', 'void', ['const std::shared_ptr<gs::core::Group> &group'], ['proxy'])

	gen.bind_method(shared_scene, 'Clear', 'void', [], ['proxy'])
	gen.bind_method(shared_scene, 'Dispose', 'void', [], ['proxy'])
	gen.bind_method(shared_scene, 'IsReady', 'bool', [], ['proxy'])

	gen.bind_method(shared_scene, 'AddSystem', 'void', ['std::shared_ptr<gs::core::SceneSystem> system'], ['proxy'])
	#gen.bind_method(shared_scene, 'GetSystem', 'std::shared_ptr<gs::core::SceneSystem>', ['const char *name'], ['proxy'])

	gen.bind_method(shared_scene, 'GetSystem<gs::core::RenderableSystem>', 'std::shared_ptr<gs::core::RenderableSystem>', [], ['proxy'], bound_name='GetRenderableSystem')
	gen.bind_method(shared_scene, 'GetSystem<gs::core::IPhysicSystem>', 'std::shared_ptr<gs::core::IPhysicSystem>', [], ['proxy'], bound_name='GetPhysicSystem')

	#const std::vector<sSceneSystem> &GetSystems() const { return systems; }

	gen.bind_method(shared_scene, 'AddNode', 'void', ['std::shared_ptr<gs::core::Node> node'], ['proxy'])
	gen.bind_method(shared_scene, 'RemoveNode', 'void', ['const std::shared_ptr<gs::core::Node> &node'], ['proxy'])

	gen.bind_method(shared_scene, 'AddComponentToSystems', 'void', ['std::shared_ptr<gs::core::Component> node'], ['proxy'])
	gen.bind_method(shared_scene, 'RemoveComponentFromSystems', 'void', ['const std::shared_ptr<gs::core::Component> &component'], ['proxy'])

	gen.bind_method_overloads(shared_scene, 'GetNode', [
		('std::shared_ptr<gs::core::Node>', ['gs::uint uid'], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'Node not found')}),
		('std::shared_ptr<gs::core::Node>', ['const char *name', '?const std::shared_ptr<gs::core::Node> &parent'], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'Node not found')})
	])

	gen.bind_method_overloads(shared_scene, 'GetNodes', [
		('const std::vector<std::shared_ptr<gs::core::Node>> &', [], ['proxy']),
		('std::vector<std::shared_ptr<gs::core::Node>>', ['const char *filter'], ['proxy'])
	])
	gen.bind_method(shared_scene, 'GetNodeChildren', 'std::vector<std::shared_ptr<gs::core::Node>>', ['const gs::core::Node &node'], ['proxy'])
	gen.bind_method(shared_scene, 'GetNodesWithAspect', 'std::vector<std::shared_ptr<gs::core::Node>>', ['const char *aspect'], ['proxy'])

	gen.insert_binding_code('static bool _Scene_Load(gs::core::Scene *scene, const char *path, std::shared_ptr<gs::render::RenderSystem> &render_system, std::vector<std::shared_ptr<gs::core::Node>> *nodes) { return gs::core::LoadScene(*scene, path, render_system, nodes); }')
	gen.bind_method(shared_scene, 'Load', 'bool', ['const char *path', 'std::shared_ptr<gs::render::RenderSystem> &render_system', 'std::vector<std::shared_ptr<gs::core::Node>> *nodes'], {'proxy': None, 'route': route_lambda('_Scene_Load'), 'arg_out': ['nodes']})

	gen.bind_method_overloads(shared_scene, 'Update', [
		('void', [], ['proxy']),
		('void', ['gs::time_ns dt'], ['proxy'])
	])
	gen.bind_method_overloads(shared_scene, 'WaitUpdate', [
		('bool', [], ['proxy']),
		('bool', ['bool blocking'], ['proxy'])
	])
	gen.bind_method(shared_scene, 'Commit', 'void', [], ['proxy'])
	gen.bind_method_overloads(shared_scene, 'WaitCommit', [
		('bool', [], ['proxy']),
		('bool', ['bool blocking'], ['proxy'])
	])

	gen.bind_method_overloads(shared_scene, 'UpdateAndCommitWaitAll', [
		('void', [], ['proxy']),
		('void', ['gs::time_ns dt'], ['proxy'])
	])

	#const Signal<void(SceneSerializationState &)> &GetSerializationSignal() const { return serialization_signal; }
	#Signal<void(SceneSerializationState &)> &GetSerializationSignal() { return serialization_signal; }

	#const Signal<void(SceneDeserializationState &)> &GetDeserializationSignal() const { return deserialization_signal; }
	#Signal<void(SceneDeserializationState &)> &GetDeserializationSignal() { return deserialization_signal; }

	gen.bind_method(shared_scene, 'AddComponent', 'void', ['std::shared_ptr<gs::core::Component> component'], ['proxy'])
	gen.bind_method(shared_scene, 'RemoveComponent', 'void', ['const std::shared_ptr<gs::core::Component> &component'], ['proxy'])

	gen.bind_method_overloads(shared_scene, 'GetComponents', [
		('const std::vector<std::shared_ptr<gs::core::Component>> &', [], ['proxy']),
		('std::vector<std::shared_ptr<gs::core::Component>>', ['const char *aspect'], ['proxy'])
	])

	gen.bind_method(shared_scene, 'GetComponent<gs::core::Environment>', 'std::shared_ptr<gs::core::Environment>', [], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'GetEnvironment failed, scene has no Environment component')}, bound_name='GetEnvironment')

	gen.bind_method(shared_scene, 'HasAspect', 'bool', ['const char *aspect'], ['proxy'])
	gen.bind_method(shared_scene, 'GetMinMax', 'gs::MinMax', [], ['proxy'])

	gen.end_class(shared_scene)

	# global functions
	gen.bind_function('gs::core::NewDefaultScene', 'std::shared_ptr<gs::core::Scene>', ['std::shared_ptr<gs::render::RenderSystem> render_system'])
	#gen.bind_function('gs::core::LoadScene', 'bool', ['gs::core::Scene &scene', 'const char *path', 'std::shared_ptr<gs::render::RenderSystem> render_system'])
	gen.bind_function('gs::core::SceneSetupCoreSystemsAndComponents', 'void', ['std::shared_ptr<gs::core::Scene> scene', 'std::shared_ptr<gs::render::RenderSystem> render_system'])


def bind_gpu(gen):
	# types
	gen.add_include('engine/types.h')

	gen.bind_named_enum('gs::gpu::PrimitiveType', ['PrimitiveLine', 'PrimitiveTriangle', 'PrimitivePoint', 'PrimitiveLast'], bound_name='GpuPrimitiveType', prefix='Gpu', storage_type='uint8_t')

	# gs::gpu::Buffer
	gen.add_include('engine/gpu_buffer.h')

	gen.bind_named_enum('gs::gpu::Buffer::Usage', ['Static', 'Dynamic'], bound_name='GpuBufferUsage', prefix='GpuBuffer')
	gen.bind_named_enum('gs::gpu::Buffer::Type', ['Index', 'Vertex'], bound_name='GpuBufferType', prefix='GpuBuffer')

	buffer = gen.begin_class('gs::gpu::Buffer', bound_name='Buffer_nobind', noncopyable=True, nobind=True)
	gen.end_class(buffer)

	shared_buffer = gen.begin_class('std::shared_ptr<gs::gpu::Buffer>', bound_name='GpuBuffer', features={'proxy': lib.stl.SharedPtrProxyFeature(buffer)})
	gen.end_class(shared_buffer)

	# gs::gpu::Resource
	gen.add_include('engine/resource.h')

	resource = gen.begin_class('gs::gpu::Resource', bound_name='GpuResource_nobind', noncopyable=True, nobind=True)
	gen.end_class(resource)

	shared_resource = gen.begin_class('std::shared_ptr<gs::gpu::Resource>', bound_name='GpuResource', features={'proxy': lib.stl.SharedPtrProxyFeature(resource)})

	gen.bind_method(shared_resource, 'GetName', 'const std::string &', [], ['proxy'])

	gen.bind_method(shared_resource, 'IsReadyOrFailed', 'bool', [], ['proxy'])
	gen.bind_method(shared_resource, 'IsFailed', 'bool', [], ['proxy'])

	gen.bind_method(shared_resource, 'SetReady', 'void', [], ['proxy'])
	gen.bind_method(shared_resource, 'SetFailed', 'void', [], ['proxy'])
	gen.bind_method(shared_resource, 'SetNotReady', 'bool', [], ['proxy'])

	gen.end_class(shared_resource)

	# gs::gpu::Texture
	gen.add_include('engine/texture.h')

	gen.bind_named_enum('gs::gpu::TextureUsage::Type', ['IsRenderTarget', 'IsShaderResource', 'Default'], prefix='Texture', bound_name='TextureUsageFlags', namespace='gs::gpu::TextureUsage')
	gen.bind_named_enum('gs::gpu::Texture::Format', ['RGBA8', 'BGRA8', 'RGBA16', 'RGBAF', 'Depth', 'DepthF', 'R8', 'R16', 'InvalidFormat'], 'uint8_t', 'TextureFormat', 'Texture')
	gen.bind_named_enum('gs::gpu::Texture::AA', ['NoAA', 'MSAA2x', 'MSAA4x', 'MSAA8x', 'MSAA16x', 'AALast'], 'uint8_t', 'TextureAA', 'Texture')

	texture = gen.begin_class('gs::gpu::Texture', bound_name='Texture_nobind', noncopyable=True, nobind=True)
	gen.end_class(texture)

	shared_texture = gen.begin_class('std::shared_ptr<gs::gpu::Texture>', bound_name='Texture', features={'proxy': lib.stl.SharedPtrProxyFeature(texture)})

	gen.add_base(shared_texture, shared_resource)

	gen.bind_method(shared_texture, 'GetWidth', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_texture, 'GetHeight', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_texture, 'GetDepth', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_texture, 'GetRect', 'gs::Rect<float>', [], ['proxy'])

	gen.end_class(shared_texture)

	# gs::gpu::RenderTarget
	render_target = gen.begin_class('gs::gpu::RenderTarget', bound_name='RenderTarget_nobind', noncopyable=True, nobind=True)
	gen.end_class(render_target)

	shared_render_target = gen.begin_class('std::shared_ptr<gs::gpu::RenderTarget>', bound_name='RenderTarget', features={'proxy': lib.stl.SharedPtrProxyFeature(render_target)})
	gen.end_class(shared_render_target)

	# gs::gpu::HardwareInfo
	hw_info = gen.begin_class('gs::gpu::HardwareInfo')
	gen.bind_members(hw_info, ['std::string name', 'std::string vendor'])
	gen.end_class(hw_info)

	# gs::gpu::Shader
	gen.add_include('engine/gpu_shader.h')

	shader = gen.begin_class('gs::gpu::Shader', bound_name='GpuShader_nobind', noncopyable=True, nobind=True)
	gen.end_class(shader)

	shared_shader = gen.begin_class('std::shared_ptr<gs::gpu::Shader>', bound_name='GpuShader', features={'proxy': lib.stl.SharedPtrProxyFeature(shader)})
	gen.add_base(shared_shader, shared_resource)
	gen.end_class(shared_shader)

	lib.stl.bind_future_T(gen, 'std::shared_ptr<gs::gpu::Shader>', 'FutureGpuShader')

	shader_value = gen.begin_class('gs::gpu::ShaderValue', bound_name='GpuShaderValue')
	gen.bind_members(shader_value, ['std::shared_ptr<gs::gpu::Texture> texture', 'gs::core::TextureUnitConfig tex_unit_cfg'])
	gen.end_class(shader_value)

	shader_variable = gen.begin_class('gs::gpu::ShaderVariable', bound_name='GpuShaderVariable')
	gen.end_class(shader_variable)

	# gs::TCache<T>
	gen.add_include("engine/resource_cache.h")

	def bind_tcache_T(T, bound_name):
		tcache = gen.begin_class('gs::TCache<%s>'%T, bound_name=bound_name, noncopyable=True)

		gen.bind_method(tcache, 'Purge', 'size_t', [])

		gen.bind_method(tcache, 'Clear', 'void', [])
		gen.bind_method(tcache, 'Has', 'std::shared_ptr<%s>'%T, ['const char *name'])

		gen.bind_method(tcache, 'Add', 'void', ['std::shared_ptr<%s> &resource'%T])
		#const std::vector<std::shared_ptr<T>> &GetContent() const { return cache; }

		gen.end_class(tcache)

	bind_tcache_T('gs::gpu::Texture', 'TextureCache')
	bind_tcache_T('gs::gpu::Shader', 'ShaderCache')

	# gs::gpu::Renderer
	gen.add_include('engine/renderer.h')

	gen.bind_named_enum('gs::gpu::Renderer::FillMode', ['FillSolid', 'FillWireframe', 'FillLast'])
	gen.bind_named_enum('gs::gpu::Renderer::CullFunc', ['CullFront', 'CullBack', 'CullLast'])
	gen.bind_named_enum('gs::gpu::Renderer::DepthFunc', ['DepthNever', 'DepthLess', 'DepthEqual', 'DepthLessEqual', 'DepthGreater', 'DepthNotEqual', 'DepthGreaterEqual', 'DepthAlways', 'DepthFuncLast'])
	gen.bind_named_enum('gs::gpu::Renderer::BlendFunc', ['BlendZero', 'BlendOne', 'BlendSrcAlpha', 'BlendOneMinusSrcAlpha', 'BlendDstAlpha', 'BlendOneMinusDstAlpha', 'BlendLast'])
	gen.bind_named_enum('gs::gpu::Renderer::ClearFunction', ['ClearColor', 'ClearDepth', 'ClearAll'])

	renderer = gen.begin_class('gs::gpu::Renderer', bound_name='Renderer_nobind', noncopyable=True, nobind=True)
	gen.end_class(renderer)

	shared_renderer = gen.begin_class('std::shared_ptr<gs::gpu::Renderer>', bound_name='Renderer', features={'proxy': lib.stl.SharedPtrProxyFeature(renderer)})

	gen.bind_method(shared_renderer, 'GetName', 'const char *', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetDescription', 'const char *', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetVersion', 'const char *', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetNativeHandle', 'void *', [], ['proxy'])

	gen.bind_method(shared_renderer, 'GetHardwareInfo', 'const gs::gpu::HardwareInfo &', [], ['proxy'])

	gen.bind_method(shared_renderer, 'PurgeCache', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_renderer, 'RefreshCacheEntry', 'void', ['const char *name'], ['proxy'])

	gen.bind_method(shared_renderer, 'IsCooked', 'bool', ['const char *name'], ['proxy'])

	gen.bind_method(shared_renderer, 'GetTextureCache', 'const gs::TCache<gs::gpu::Texture> &', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetShaderCache', 'const gs::TCache<gs::gpu::Shader> &', [], ['proxy'])

	"""
	Signal<void(Renderer &)> open_signal, close_signal;
	Signal<void(Renderer &, const Surface &)> output_surface_created_signal;
	Signal<void(Renderer &, const Surface &)> output_surface_changed_signal;
	Signal<void(Renderer &, const Surface &)> output_surface_destroyed_signal;

	Signal<void(Renderer &)> pre_draw_frame_signal, post_draw_frame_signal;
	Signal<void(Renderer &)> show_frame_signal;
	"""

	gen.bind_method(shared_renderer, 'GetWorkerAffinity', 'gs::task_affinity', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetWorkerAffinity', 'void', ['gs::task_affinity affinity'], ['proxy'])

	gen.bind_method(shared_renderer, 'NewRenderTarget', 'std::shared_ptr<gs::gpu::RenderTarget>', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'SetRenderTargetColorTexture', [
		('void', ['gs::gpu::RenderTarget &render_target', 'std::shared_ptr<gs::gpu::Texture> texture'], ['proxy'])
		#('void', ['gs::gpu::RenderTarget &render_target', 'std::shared_ptr<gs::gpu::Texture> texture *', 'uint count'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'SetRenderTargetDepthTexture', 'void', ['gs::gpu::RenderTarget &render_target', 'std::shared_ptr<gs::gpu::Texture> texture'], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'BlitRenderTarget', [
		('void', ['const std::shared_ptr<gs::gpu::RenderTarget> &src_render_target', 'const std::shared_ptr<gs::gpu::RenderTarget> &dst_render_target', 'const gs::Rect<int> &src_rect', 'const gs::Rect<int> &dst_rect'], ['proxy']),
		('void', ['const std::shared_ptr<gs::gpu::RenderTarget> &src_render_target', 'const std::shared_ptr<gs::gpu::RenderTarget> &dst_render_target', 'const gs::Rect<int> &src_rect', 'const gs::Rect<int> &dst_rect', 'bool blit_color', 'bool blit_depth'], ['proxy'])
	])
	#gen.bind_method(shared_renderer, 'ReadRenderTargetColorPixels', 'void', ['const std::shared_ptr<gs::gpu::RenderTarget> &src_render_target', 'const std::shared_ptr<gs::Picture> &out', 'const gs::Rect<int> &rect'], ['proxy'])
	gen.bind_method(shared_renderer, 'ClearRenderTarget', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetRenderTarget', 'const std::shared_ptr<gs::gpu::RenderTarget> &', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetRenderTarget', 'void', ['std::shared_ptr<gs::gpu::RenderTarget> render_target'], ['proxy'])
	gen.bind_method(shared_renderer, 'CheckRenderTarget', 'bool', [], ['proxy'])

	gen.bind_method(shared_renderer, 'CreateRenderTarget', 'bool', ['gs::gpu::RenderTarget &render_target'], ['proxy'])
	gen.bind_method(shared_renderer, 'FreeRenderTarget', 'void', ['gs::gpu::RenderTarget &render_target'], ['proxy'])

	gen.bind_method(shared_renderer, 'NewBuffer', 'std::shared_ptr<gs::gpu::Buffer>', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetBufferSize', 'size_t', ['gs::gpu::Buffer &buffer'], ['proxy'])
	#std::future<void *> MapBuffer(sBuffer buf) {
	#void UnmapBuffer(sBuffer buf) { run_call<void>(std::bind(&Renderer::UnmapBuffer, shared_ref(renderer), shared_ref(buf)), RA_task_affinity); }
	#std::future<bool> UpdateBuffer(sBuffer buf, const void *p, size_t start = 0, size_t size = 0) {
	#std::future<bool> CreateBuffer(sBuffer buf, const void *data, size_t size, Buffer::Type type, Buffer::Usage usage = Buffer::Static) {
	#std::future<bool> CreateBuffer(sBuffer buf, const BinaryBlob &data, Buffer::Type type, Buffer::Usage usage = Buffer::Static) {

	gen.insert_binding_code('''\
static bool _CreateBuffer(gs::gpu::Renderer *renderer, gs::gpu::Buffer &buffer, gs::BinaryBlob &data, gs::gpu::Buffer::Type type, gs::gpu::Buffer::Usage usage = gs::gpu::Buffer::Static) {
	return renderer->CreateBuffer(buffer, data.GetData(), data.GetDataSize(), type, usage);
}
''')
	gen.bind_method(shared_renderer, 'CreateBuffer', 'void', ['gs::gpu::Buffer &buffer', 'gs::BinaryBlob &data', 'gs::gpu::Buffer::Type type', '?gs::gpu::Buffer::Usage usage'], {'proxy': None, 'route': lambda args: '_CreateBuffer(%s);' % ', '.join(args)})
	gen.bind_method(shared_renderer, 'FreeBuffer', 'void', ['gs::gpu::Buffer &buffer'], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'NewTexture', [
		('std::shared_ptr<gs::gpu::Texture>', [], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'int width', 'int height'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa', '?gs::gpu::TextureUsage::Type usage', '?bool mipmapped'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'const gs::Picture &picture', '?gs::gpu::TextureUsage::Type usage', '?bool mipmapped'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'NewShadowMap', 'std::shared_ptr<gs::gpu::Texture>', ['int width', 'int height', '?const char *name'], ['proxy'])
	gen.bind_method(shared_renderer, 'NewExternalTexture', 'std::shared_ptr<gs::gpu::Texture>', ['?const char *name'], ['proxy'])
	gen.bind_method_overloads(shared_renderer, 'CreateTexture', [
		('bool', ['gs::gpu::Texture &texture', 'int width', 'int height', '?gs::gpu::Texture::Format format', '?gs::gpu::Texture::AA aa', '?gs::gpu::TextureUsage::Type usage', '?bool mipmapped'], ['proxy']),
		('bool', ['gs::gpu::Texture &texture', 'const gs::Picture &picture', '?gs::gpu::TextureUsage::Type usage', '?bool mipmapped'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'FreeTexture', 'void', ['gs::gpu::Texture &texture'], ['proxy'])

	gen.bind_method(shared_renderer, 'LoadNativeTexture', 'bool', ['gs::gpu::Texture &texture', 'const char *path'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetNativeTextureExt', 'const char *', [], ['proxy'])

	gen.insert_binding_code('''\
static void RendererBlitTexture_wrapper(gs::gpu::Renderer *renderer, gs::gpu::Texture &texture, const gs::Picture &picture) { renderer->BlitTexture(texture, picture.GetData(), picture.GetDataSize(), picture.GetWidth(), picture.GetHeight()); }
\n''')

	gen.bind_method_overloads(shared_renderer, 'BlitTexture', [
		('void', ['gs::gpu::Texture &texture', 'const gs::Picture &picture'], {'proxy': None, 'route': lambda args: 'RendererBlitTexture_wrapper(%s);' % ', '.join(args)}),
		#('void', ['gs::gpu::Texture &texture', 'const void *data', 'size_t data_size', 'gs::uint width', 'gs::uint height'], ['proxy']),
		#('void', ['gs::gpu::Texture &texture', 'const void *data', 'size_t data_size', 'gs::uint width', 'gs::uint height', 'gs::uint x', 'gs::uint y'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'ResizeTexture', 'void', ['gs::gpu::Texture &texture', 'gs::uint width', 'gs::uint height'], ['proxy'])

	gen.bind_method(shared_renderer, 'CaptureTexture', 'bool', ['const gs::gpu::Texture &texture', 'gs::Picture &picture'], ['proxy'])

	gen.bind_method(shared_renderer, 'GenerateTextureMipmap', 'void', ['gs::gpu::Texture &texture'], ['proxy'])

	gen.bind_method(shared_renderer, 'HasTexture', 'std::shared_ptr<gs::gpu::Texture>', ['const char *path'], ['proxy'])
	gen.bind_method(shared_renderer, 'LoadTexture', 'std::shared_ptr<gs::gpu::Texture>', ['const char *path', '?bool use_cache'], ['proxy'])

	#
	gen.bind_method(shared_renderer, 'NewShader', 'std::shared_ptr<gs::gpu::Shader>', ['?const char *name'], ['proxy'])

	gen.bind_method(shared_renderer, 'HasShader', 'std::shared_ptr<gs::gpu::Shader>', ['const char *name'], ['proxy'])
	gen.bind_method_overloads(shared_renderer, 'LoadShader', [
		('std::shared_ptr<gs::gpu::Shader>', ['const char *name', '?bool use_cache'], ['proxy']),
		('std::shared_ptr<gs::gpu::Shader>', ['const char *name', 'const char *source', '?bool use_cache'], ['proxy'])
	])

	gen.bind_method(shared_renderer, 'CreateShader', 'void', ['const std::shared_ptr<gs::gpu::Shader> &shader', 'const std::shared_ptr<gs::core::Shader> &core_shader'], ['proxy'])
	gen.bind_method(shared_renderer, 'FreeShader', 'void', ['gs::gpu::Shader &shader'], ['proxy'])

	gen.bind_method(shared_renderer, 'GetShaderVariable', 'gs::gpu::ShaderVariable', ['const char *name'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetShaderBuiltin', 'gs::gpu::ShaderVariable', ['gs::core::ShaderVariable::Semantic semantic'], ['proxy'])

	gen.insert_binding_code('''\
static void _renderer_SetShaderInt(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, int x) { renderer->SetShaderInt(var, &x); }
static void _renderer_SetShaderInt2(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, int x, int y) { int v2[] = {x, y}; renderer->SetShaderInt2(var, v2); }
static void _renderer_SetShaderInt3(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, int x, int y, int z) { int v3[] = {x, y, z}; renderer->SetShaderInt3(var, v3); }
static void _renderer_SetShaderInt4(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, int x, int y, int z, int w) { int v4[] = {x, y, z, w}; renderer->SetShaderInt4(var, v4); }

static void _renderer_SetShaderUnsigned(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, gs::uint x) { renderer->SetShaderUnsigned(var, &x); }
static void _renderer_SetShaderUnsigned2(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, gs::uint x, gs::uint y) { gs::uint v2[] = {x, y}; renderer->SetShaderUnsigned2(var, v2); }
static void _renderer_SetShaderUnsigned3(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, gs::uint x, gs::uint y, gs::uint z) { gs::uint v3[] = {x, y, z}; renderer->SetShaderUnsigned3(var, v3); }
static void _renderer_SetShaderUnsigned4(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, gs::uint x, gs::uint y, gs::uint z, gs::uint w) { gs::uint v4[] = {x, y, z, w}; renderer->SetShaderUnsigned4(var, v4); }

static void _renderer_SetShaderFloat(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, float x) { renderer->SetShaderFloat(var, &x); }
static void _renderer_SetShaderFloat2(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, float x, float y) { float v2[] = {x, y}; renderer->SetShaderFloat2(var, v2); }
static void _renderer_SetShaderFloat3(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, float x, float y, float z) { float v3[] = {x, y, z}; renderer->SetShaderFloat3(var, v3); }
static void _renderer_SetShaderFloat4(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, float x, float y, float z, float w) { float v4[] = {x, y, z, w}; renderer->SetShaderFloat4(var, v4); }

static void _renderer_SetShaderMatrix3(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, const gs::Matrix3 &m) { renderer->SetShaderMatrix3(var, &m); }
static void _renderer_SetShaderMatrix4(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, const gs::Matrix4 &m) { renderer->SetShaderMatrix4(var, &m); }
static void _renderer_SetShaderMatrix44(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, const gs::Matrix44 &m) { renderer->SetShaderMatrix44(var, &m); }

static void _renderer_SetShaderTexture(gs::gpu::Renderer *renderer, const gs::gpu::ShaderVariable &var, const gs::gpu::Texture &t) { renderer->SetShaderTexture(var, t); }

static void _renderer_SetShaderInt_name(gs::gpu::Renderer *renderer, const char *name, int x) { renderer->SetShaderInt(renderer->GetShaderVariable(name), &x); }
static void _renderer_SetShaderInt2_name(gs::gpu::Renderer *renderer, const char *name, int x, int y) { int v2[] = {x, y}; renderer->SetShaderInt2(renderer->GetShaderVariable(name), v2); }
static void _renderer_SetShaderInt3_name(gs::gpu::Renderer *renderer, const char *name, int x, int y, int z) { int v3[] = {x, y, z}; renderer->SetShaderInt3(renderer->GetShaderVariable(name), v3); }
static void _renderer_SetShaderInt4_name(gs::gpu::Renderer *renderer, const char *name, int x, int y, int z, int w) { int v4[] = {x, y, z, w}; renderer->SetShaderInt4(renderer->GetShaderVariable(name), v4); }

static void _renderer_SetShaderUnsigned_name(gs::gpu::Renderer *renderer, const char *name, gs::uint x) { renderer->SetShaderUnsigned(renderer->GetShaderVariable(name), &x); }
static void _renderer_SetShaderUnsigned2_name(gs::gpu::Renderer *renderer, const char *name, gs::uint x, gs::uint y) { gs::uint v2[] = {x, y}; renderer->SetShaderUnsigned2(renderer->GetShaderVariable(name), v2); }
static void _renderer_SetShaderUnsigned3_name(gs::gpu::Renderer *renderer, const char *name, gs::uint x, gs::uint y, gs::uint z) { gs::uint v3[] = {x, y, z}; renderer->SetShaderUnsigned3(renderer->GetShaderVariable(name), v3); }
static void _renderer_SetShaderUnsigned4_name(gs::gpu::Renderer *renderer, const char *name, gs::uint x, gs::uint y, gs::uint z, gs::uint w) { gs::uint v4[] = {x, y, z, w}; renderer->SetShaderUnsigned4(renderer->GetShaderVariable(name), v4); }

static void _renderer_SetShaderFloat_name(gs::gpu::Renderer *renderer, const char *name, float x) { renderer->SetShaderFloat(renderer->GetShaderVariable(name), &x); }
static void _renderer_SetShaderFloat2_name(gs::gpu::Renderer *renderer, const char *name, float x, float y) { float v2[] = {x, y}; renderer->SetShaderFloat2(renderer->GetShaderVariable(name), v2); }
static void _renderer_SetShaderFloat3_name(gs::gpu::Renderer *renderer, const char *name, float x, float y, float z) { float v3[] = {x, y, z}; renderer->SetShaderFloat3(renderer->GetShaderVariable(name), v3); }
static void _renderer_SetShaderFloat4_name(gs::gpu::Renderer *renderer, const char *name, float x, float y, float z, float w) { float v4[] = {x, y, z, w}; renderer->SetShaderFloat4(renderer->GetShaderVariable(name), v4); }

static void _renderer_SetShaderMatrix3_name(gs::gpu::Renderer *renderer, const char *name, const gs::Matrix3 &m) { renderer->SetShaderMatrix3(renderer->GetShaderVariable(name), &m); }
static void _renderer_SetShaderMatrix4_name(gs::gpu::Renderer *renderer, const char *name, const gs::Matrix4 &m) { renderer->SetShaderMatrix4(renderer->GetShaderVariable(name), &m); }
static void _renderer_SetShaderMatrix44_name(gs::gpu::Renderer *renderer, const char *name, const gs::Matrix44 &m) { renderer->SetShaderMatrix44(renderer->GetShaderVariable(name), &m); }

static void _renderer_SetShaderTexture_name(gs::gpu::Renderer *renderer, const char *name, const gs::gpu::Texture &t) { renderer->SetShaderTexture(renderer->GetShaderVariable(name), t); }
''')

	gen.bind_method_overloads(shared_renderer, 'SetShaderInt', [
		('void', ['const gs::gpu::ShaderVariable &var', 'int x'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderInt(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'int x'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderInt_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderInt2', [
		('void', ['const gs::gpu::ShaderVariable &var', 'int x', 'int y'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderInt2(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'int x', 'int y'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderInt2_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderInt3', [
		('void', ['const gs::gpu::ShaderVariable &var', 'int x', 'int y', 'int z'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderInt3(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'int x', 'int y', 'int z'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderInt3_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderInt4', [
		('void', ['const gs::gpu::ShaderVariable &var', 'int x', 'int y', 'int z', 'int w'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderInt4(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'int x', 'int y', 'int z', 'int w'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderInt4_name(%s);' % (', '.join(args))})
	])

	gen.bind_method_overloads(shared_renderer, 'SetShaderUnsigned', [
		('void', ['const gs::gpu::ShaderVariable &var', 'gs::uint x'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderUnsigned(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'gs::uint x'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderUnsigned_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderUnsigned2', [
		('void', ['const gs::gpu::ShaderVariable &var', 'gs::uint x', 'gs::uint y'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderUnsigned2(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'gs::uint x', 'gs::uint y'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderUnsigned2_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderUnsigned3', [
		('void', ['const gs::gpu::ShaderVariable &var', 'gs::uint x', 'gs::uint y', 'gs::uint z'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderUnsigned3(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'gs::uint x', 'gs::uint y', 'gs::uint z'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderUnsigned3_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderUnsigned4', [
		('void', ['const gs::gpu::ShaderVariable &var', 'gs::uint x', 'gs::uint y', 'gs::uint z', 'gs::uint w'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderUnsigned4(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'gs::uint x', 'gs::uint y', 'gs::uint z', 'gs::uint w'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderUnsigned4_name(%s);' % (', '.join(args))})
	])

	gen.bind_method_overloads(shared_renderer, 'SetShaderFloat', [
		('void', ['const gs::gpu::ShaderVariable &var', 'float x'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderFloat(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'float x'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderFloat_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderFloat2', [
		('void', ['const gs::gpu::ShaderVariable &var', 'float x', 'float y'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderFloat2(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'float x', 'float y'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderFloat2_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderFloat3', [
		('void', ['const gs::gpu::ShaderVariable &var', 'float x', 'float y', 'float z'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderFloat3(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'float x', 'float y', 'float z'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderFloat3_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderFloat4', [
		('void', ['const gs::gpu::ShaderVariable &var', 'float x', 'float y', 'float z', 'float w'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderFloat4(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'float x', 'float y', 'float z', 'float w'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderFloat4_name(%s);' % (', '.join(args))})
	])

	gen.bind_method_overloads(shared_renderer, 'SetShaderMatrix3', [
		('void', ['const gs::gpu::ShaderVariable &var', 'const gs::Matrix3 &m'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderMatrix3(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'const gs::Matrix3 &m'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderMatrix3_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderMatrix4', [
		('void', ['const gs::gpu::ShaderVariable &var', 'const gs::Matrix4 &m'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderMatrix4(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'const gs::Matrix4 &m'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderMatrix4_name(%s);' % (', '.join(args))})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderMatrix44', [
		('void', ['const gs::gpu::ShaderVariable &var', 'const gs::Matrix44 &m'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderMatrix44(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'const gs::Matrix44 &m'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderMatrix44_name(%s);' % (', '.join(args))})
	])

	gen.bind_method_overloads(shared_renderer, 'SetShaderTexture', [
		('void', ['const gs::gpu::ShaderVariable &var', 'const gs::gpu::Texture &texture'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderTexture(%s);' % (', '.join(args))}),
		('void', ['const char *name', 'const gs::gpu::Texture &texture'], {'proxy': None, 'route': lambda args: '_renderer_SetShaderTexture_name(%s);' % (', '.join(args))})
	])

	"""
	gen.bind_method(shared_renderer, 'SetShaderSystemBuiltins', 'void', ['float clock', 'const gs::tVector2<int> &internal_resolution', 'gs::uint fx_scale', 'const gs::Color &ambient_color', 'bool is_forward', 'bool fog_enabled', 'const gs::Color &fog_color', 'float fog_near', 'float fog_far', 'gs::gpu::Texture &depth_map'])
	gen.bind_method(shared_renderer, 'SetShaderCameraBuiltins', 'void', ['const gs::Matrix4 &view_world', 'float z_near', 'float z_far', 'float zoom_factor', 'float eye'])
	gen.bind_method(shared_renderer, 'SetShaderTransformationBuiltins', 'void', ['const gs::Matrix44 &view_pm', 'const gs::Matrix4 &view_m', 'const gs::Matrix4 &view_im', 'const gs::Matrix4 *node_m', 'const gs::Matrix4 *node_im', 'const gs::Matrix44 &prv_view_pm', 'const gs::Matrix4 &prv_view_im', 'const gs::Matrix4 *i_m', 'uint count'])
	gen.bind_method(shared_renderer, 'SetShaderLightBuiltins', 'void', ['const gs::Matrix4 &light_world', 'const gs::Color &light_diffuse', 'const gs::Color &light_specular', 'float range', 'float clip_dist', 'float cone_angle', 'float edge_angle', 'gs::gpu::Texture *projection_map', 'const gs::Matrix4 &view_world', 'gs::gpu::Texture *shadow_map', 'float shadow_bias', 'float inv_shadow_map_size', 'const gs::Color &shadow_color', 'gs::uint shadow_data_count', 'const gs::Matrix4 *shadow_data_inv_world', 'const gs::Matrix44 *shadow_data_projection_to_map', 'const float *shadow_data_slice_distance'])
	gen.bind_method(shared_renderer, 'SetShaderSkeletonValues', 'void', ['gs::uint skin_bone_count', 'const gs::Matrix4 *skin_bone_matrices', 'const gs::Matrix4 *skin_bone_previous_matrices', 'const uint16_t *skin_bone_idx'])
	gen.bind_method(shared_renderer, 'SetShaderPickingBuiltins', 'void', ['gs::uint uid'])
	gen.bind_method(shared_renderer, 'SetShaderValues', 'void', ['const ShaderValues &shader_values', '?const ShaderValues *material_values'])
	"""

	#
	gen.bind_method(shared_renderer, 'SetFillMode', 'void', ['gs::gpu::Renderer::FillMode mode'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetCullFunc', 'void', ['gs::gpu::Renderer::CullFunc func'], ['proxy'])
	gen.bind_method(shared_renderer, 'EnableCulling', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetDepthFunc', 'void', ['gs::gpu::Renderer::DepthFunc func'], ['proxy'])
	gen.bind_method(shared_renderer, 'EnableDepthTest', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_renderer, 'EnableDepthWrite', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetBlendFunc', 'void', ['gs::gpu::Renderer::BlendFunc src', 'gs::gpu::Renderer::BlendFunc dst'], ['proxy'])
	gen.bind_method(shared_renderer, 'EnableBlending', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer, 'EnableAlphaToCoverage', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetColorMask', 'void', ['bool red', 'bool green', 'bool blue', 'bool alpha'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetDefaultStates', 'void', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'SetIndexSource', [
		('void', [], ['proxy']),
		('void', ['gs::gpu::Buffer &buffer'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'SetVertexSource', 'void', ['gs::gpu::Buffer &buffer', 'const gs::core::VertexLayout &layout'], ['proxy'])

	gen.bind_method(shared_renderer, 'GetShader', 'const std::shared_ptr<gs::gpu::Shader> &', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetShader', 'bool', ['std::shared_ptr<gs::gpu::Shader> shader'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetPolygonDepthOffset', 'void', ['float slope_scale', 'float bias'], ['proxy'])

	gen.bind_method(shared_renderer, 'NewOutputSurface', 'gs::Surface', ['const gs::Window &window'], ['proxy'])
	gen.bind_method(shared_renderer, 'SetOutputSurface', 'void', ['const gs::Surface &surface'], ['proxy'])
	gen.bind_method(shared_renderer, 'DestroyOutputSurface', 'void', ['const gs::Surface &surface'], ['proxy'])
	gen.bind_method(shared_renderer, 'NewOffscreenOutputSurface', 'gs::Surface', ['int width', 'int height'], ['proxy'])

	gen.bind_method(shared_renderer, 'GetOutputSurface', 'const gs::Surface &', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetOutputSurfaceSize', 'gs::tVector2<int>', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'Open', [
		('bool', [], ['proxy']),
		('bool', ['bool debug'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'Close', 'void', [], ['proxy'])

	gen.bind_method(shared_renderer, 'IsOpen', 'bool', [], ['proxy'])

	gen.bind_method(shared_renderer, 'GetInverseViewMatrix', 'gs::Matrix4', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetInverseWorldMatrix', 'gs::Matrix4', [], ['proxy'])

	gen.bind_method(shared_renderer, 'SetViewMatrix', 'void', ['const gs::Matrix4 &view_matrix'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetViewMatrix', 'gs::Matrix4', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetProjectionMatrix', 'void', ['const gs::Matrix44 &projection_matrix'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetProjectionMatrix', 'gs::Matrix44', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetWorldMatrix', 'void', ['const gs::Matrix4 &world_matrix'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetWorldMatrix', 'gs::Matrix4', [], ['proxy'])

	gen.bind_method(shared_renderer, 'SetIdentityMatrices', 'void', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'Set2DMatrices', [
		('void', [], ['proxy']),
		('void', ['const gs::tVector2<float> &resolution'], ['proxy']),
		('void', ['const gs::tVector2<float> &resolution', 'bool y_origin_bottom'], ['proxy']),
		('void', ['bool y_origin_bottom'], ['proxy'])
	])

	gen.bind_method(shared_renderer, 'ScreenVertex', 'gs::Vector3', ['int x', 'int y'], ['proxy'])

	gen.bind_method(shared_renderer, 'ClearClippingPlane', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetClippingPlane', 'void', ['const gs::Vector3 &plane_origin', 'const gs::Vector3 &plane_normal'], ['proxy'])

	gen.bind_method(shared_renderer, 'ClearClippingRect', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetClippingRect', 'void', ['const gs::Rect<float> &rect'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetClippingRect', 'gs::Rect<float>', [], ['proxy'])

	gen.bind_method(shared_renderer, 'SetViewport', 'void', ['const gs::Rect<float> &rect'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetViewport', 'gs::Rect<float>', [], ['proxy'])

	gen.bind_method(shared_renderer, 'GetAspectRatio', 'gs::tVector2<float>', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'Clear', [
		('void', ['gs::Color color'], ['proxy']),
		('void', ['gs::Color color', 'float z', 'gs::gpu::Renderer::ClearFunction flags'], ['proxy'])
	])

	#virtual void DrawElements(PrimitiveType prim_type, int idx_count, core::IndexType idx_type = core::IndexUShort, uint idx_offset = 0) = 0;
	#virtual void DrawElementsInstanced(uint instance_count, Buffer &instance_data, PrimitiveType prim_type, int idx_count, core::IndexType idx_type = core::IndexUShort) = 0;

	gen.bind_method(shared_renderer, 'DrawFrame', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer, 'ShowFrame', 'void', [], ['proxy'])

	gen.bind_method(shared_renderer, 'SetVSync', 'void', ['bool enabled'], ['proxy'])

	gen.bind_method(shared_renderer, 'CaptureFramebuffer', 'bool', ['gs::Picture &out'], ['proxy'])
	gen.bind_method(shared_renderer, 'InvalidateStateCache', 'void', [], ['proxy'])

	gen.bind_method(shared_renderer, 'GetFrameShownCount', 'gs::uint', [], ['proxy'])

	gen.end_class(shared_renderer)

	#
	gen.insert_binding_code('''static std::shared_ptr<gs::gpu::Renderer> CreateRenderer(const char *name) { return gs::core::g_renderer_factory.get().Instantiate(name); }
static std::shared_ptr<gs::gpu::Renderer> CreateRenderer() { return gs::core::g_renderer_factory.get().Instantiate(); }
	''', 'Renderer custom API')

	gen.bind_function('CreateRenderer', 'std::shared_ptr<gs::gpu::Renderer>', ['?const char *name'], {'check_rval': check_rval_lambda(gen, 'CreateRenderer failed, was LoadPlugins called succesfully?')})

	# gs::gpu::RendererAsync
	gen.add_include('engine/renderer_async.h')

	renderer_async = gen.begin_class('gs::gpu::RendererAsync', bound_name='RendererAsync_nobind', noncopyable=True, nobind=True)
	gen.end_class(renderer_async)

	shared_renderer_async = gen.begin_class('std::shared_ptr<gs::gpu::RendererAsync>', bound_name='RendererAsync', features={'proxy': lib.stl.SharedPtrProxyFeature(renderer_async)})

	gen.bind_constructor_overloads(shared_renderer_async, [
		(['std::shared_ptr<gs::gpu::Renderer> renderer'], ['proxy']),
		(['std::shared_ptr<gs::gpu::Renderer> renderer', 'gs::task_affinity affinity'], ['proxy'])
	])
	gen.bind_method(shared_renderer_async, 'GetRenderer', 'const std::shared_ptr<gs::gpu::Renderer> &', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'PurgeCache', 'std::future<gs::uint>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'RefreshCacheEntry', 'void', ['const char *name'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'NewRenderTarget', 'std::shared_ptr<gs::gpu::RenderTarget>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetRenderTargetColorTexture', 'void', ['const std::shared_ptr<gs::gpu::RenderTarget> &render_target', 'const std::shared_ptr<gs::gpu::Texture> &texture'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetRenderTargetDepthTexture', 'void', ['const std::shared_ptr<gs::gpu::RenderTarget> &render_target', 'const std::shared_ptr<gs::gpu::Texture> &texture'], ['proxy'])
	gen.bind_method_overloads(shared_renderer_async, 'BlitRenderTarget', [
		('void', ['const std::shared_ptr<gs::gpu::RenderTarget> &src_render_target', 'const std::shared_ptr<gs::gpu::RenderTarget> &dst_render_target', 'const gs::Rect<int> &src_rect', 'const gs::Rect<int> &dst_rect'], ['proxy']),
		('void', ['const std::shared_ptr<gs::gpu::RenderTarget> &src_render_target', 'const std::shared_ptr<gs::gpu::RenderTarget> &dst_render_target', 'const gs::Rect<int> &src_rect', 'const gs::Rect<int> &dst_rect', 'bool blit_color', 'bool blit_depth'], ['proxy'])
	])
	gen.bind_method(shared_renderer_async, 'ReadRenderTargetColorPixels', 'void', ['const std::shared_ptr<gs::gpu::RenderTarget> &src_render_target', 'const std::shared_ptr<gs::Picture> &out', 'const gs::Rect<int> &rect'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'ClearRenderTarget', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetRenderTarget', 'void', ['std::shared_ptr<gs::gpu::RenderTarget> &render_target'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'CheckRenderTarget', 'std::future<bool>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'CreateRenderTarget', 'std::future<bool>', ['std::shared_ptr<gs::gpu::RenderTarget> &render_target'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'FreeRenderTarget', 'void', ['const std::shared_ptr<gs::gpu::RenderTarget> &render_target'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'NewBuffer', 'std::shared_ptr<gs::gpu::Buffer>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetBufferSize', 'std::future<size_t>', ['std::shared_ptr<gs::gpu::Buffer> buffer'], ['proxy'])
	#std::future<void *> MapBuffer(sBuffer buf) {
	#void UnmapBuffer(sBuffer buf) { run_call<void>(std::bind(&Renderer::UnmapBuffer, shared_ref(renderer), shared_ref(buf)), RA_task_affinity); }
	#std::future<bool> UpdateBuffer(sBuffer buf, const void *p, size_t start = 0, size_t size = 0) {
	#std::future<bool> CreateBuffer(sBuffer buf, const void *data, size_t size, Buffer::Type type, Buffer::Usage usage = Buffer::Static) {
	#std::future<bool> CreateBuffer(sBuffer buf, const BinaryBlob &data, Buffer::Type type, Buffer::Usage usage = Buffer::Static) {
	gen.bind_method(shared_renderer_async, 'FreeBuffer', 'void', ['std::shared_ptr<gs::gpu::Buffer> buffer'], ['proxy'])

	gen.bind_method_overloads(shared_renderer_async, 'NewTexture', [
		('std::shared_ptr<gs::gpu::Texture>', [], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name'], ['proxy'])
	])
	gen.bind_method_overloads(shared_renderer_async, 'NewShadowMap', [
		('std::shared_ptr<gs::gpu::Texture>', ['int width', 'int height'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['int width', 'int height', 'const char *name'], ['proxy'])
	])
	gen.bind_method_overloads(shared_renderer_async, 'CreateTexture', [
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'int width', 'int height'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa', 'gs::gpu::TextureUsage::Type usage'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa', 'gs::gpu::TextureUsage::Type usage', 'bool mipmapped'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'gs::BinaryBlob &data', 'int width', 'int height'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'gs::BinaryBlob &data', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'gs::BinaryBlob &data', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa', 'gs::gpu::TextureUsage::Type usage'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'gs::BinaryBlob &data', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa', 'gs::gpu::TextureUsage::Type usage', 'bool mipmapped'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'std::shared_ptr<gs::Picture> picture'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'std::shared_ptr<gs::Picture> picture', 'gs::gpu::TextureUsage::Type usage'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'std::shared_ptr<gs::Picture> picture', 'gs::gpu::TextureUsage::Type usage', 'bool mipmapped'], ['proxy'])

	])
	gen.bind_method(shared_renderer_async, 'FreeTexture', 'void', ['std::shared_ptr<gs::gpu::Texture> texture'], ['proxy'])
	gen.bind_method_overloads(shared_renderer_async, 'BlitTexture', [
		('void', ['std::shared_ptr<gs::gpu::Texture> texture', 'const gs::BinaryBlob &data', 'gs::uint width', 'gs::uint height'], ['proxy']),
		('void', ['std::shared_ptr<gs::gpu::Texture> texture', 'const gs::BinaryBlob &data', 'gs::uint width', 'gs::uint height', 'gs::uint x', 'gs::uint y'], ['proxy'])
	])
	gen.bind_method(shared_renderer_async, 'ResizeTexture', 'void', ['std::shared_ptr<gs::gpu::Texture> texture', 'gs::uint width', 'gs::uint height'], ['proxy'])
	gen.bind_method_overloads(shared_renderer_async, 'BlitTextureBackground', [
		('void', ['std::shared_ptr<gs::gpu::Texture> texture', 'const gs::BinaryBlob &data', 'gs::uint width', 'gs::uint height'], ['proxy']),
		('void', ['std::shared_ptr<gs::gpu::Texture> texture', 'const gs::BinaryBlob &data', 'gs::uint width', 'gs::uint height', 'gs::uint x', 'gs::uint y'], ['proxy'])
	])
	gen.bind_method(shared_renderer_async, 'CaptureTexture', 'std::future<bool>', ['std::shared_ptr<gs::gpu::Texture> texture', 'std::shared_ptr<gs::Picture> out'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GenerateTextureMipmap', 'void', ['std::shared_ptr<gs::gpu::Texture> texture'], ['proxy'])
	gen.bind_method_overloads(shared_renderer_async, 'LoadTexture', [
		('std::shared_ptr<gs::gpu::Texture>', ['const char *path'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *path', 'bool use_cache'], ['proxy'])
	])
	gen.bind_method(shared_renderer_async, 'GetNativeTextureExt', 'const char *', [], ['proxy'])

	#
	gen.bind_method(shared_renderer_async, 'SetFillMode', 'void', ['gs::gpu::Renderer::FillMode fill_mode'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetCullFunc', 'void', ['gs::gpu::Renderer::CullFunc cull_mode'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'EnableCulling', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetDepthFunc', 'void', ['gs::gpu::Renderer::DepthFunc depth_func'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'EnableDepthTest', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'EnableDepthWrite', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetBlendFunc', 'void', ['gs::gpu::Renderer::BlendFunc src_blend', 'gs::gpu::Renderer::BlendFunc dst_blend'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'EnableBlending', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'EnableAlphaToCoverage', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetDefaultStates', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetIndexSource', 'void', ['?std::shared_ptr<gs::gpu::Buffer> &buffer'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetVertexSource', 'void', ['std::shared_ptr<gs::gpu::Buffer> &buffer', 'const gs::core::VertexLayout &layout'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'GetShader', 'std::future<std::shared_ptr<gs::gpu::Shader>>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetShader', 'std::future<bool>', ['std::shared_ptr<gs::gpu::Shader> &shader'], ['proxy'])

	#
	gen.bind_method(shared_renderer_async, 'NewWindow', 'std::future<gs::Window>', ['int w', 'int h', 'int bpp', 'gs::Window::Visibility visibility'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'NewOutputSurface', 'std::future<gs::Surface>', ['const gs::Window &window'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'NewOffscreenOutputSurface', 'std::future<gs::Surface>', ['int width', 'int height'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetOutputSurface', 'void', ['const gs::Surface &surface'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'DestroyOutputSurface', 'void', ['gs::Surface &surface'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'GetOutputSurface', 'std::future<gs::Surface>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetOutputSurfaceSize', 'std::future<gs::tVector2<int>>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'FitViewportToOutputSurface', 'void', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'UpdateWindow', 'void', ['const gs::Window &window'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'Open', 'std::future<bool>', ['?bool debug'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'Close', 'std::future<void>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'GetInverseViewMatrix', 'std::future<gs::Matrix4>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetInverseWorldMatrix', 'std::future<gs::Matrix4>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetViewMatrix', 'void', ['const gs::Matrix4 &view'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetViewMatrix', 'std::future<gs::Matrix4>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetProjectionMatrix', 'void', ['const gs::Matrix44 &projection'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetProjectionMatrix', 'std::future<gs::Matrix44>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetWorldMatrix', 'void', ['const gs::Matrix4 &world'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetWorldMatrix', 'std::future<gs::Matrix4>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetIdentityMatrices', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'Set2DMatrices', 'void', ['?bool reverse_y'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'ClearClippingPlane', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetClippingPlane', 'void', ['const gs::Vector3 &p', 'const gs::Vector3 &n'], ['proxy'])

	#
	gen.bind_method(shared_renderer_async, 'ClearClippingRect', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetClippingRect', 'void', ['const gs::Rect<float> &clip_rect'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetClippingRect', 'std::future<gs::Rect<float>>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetViewport', 'void', ['const gs::Rect<float> &rect'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetViewport', 'std::future<gs::Rect<float>>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetAspectRatio', 'std::future<gs::tVector2<float>>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'Clear', 'void', ['gs::Color color', '?float z', '?gs::gpu::Renderer::ClearFunction clear_mask'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'DrawFrame', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'ShowFrame', 'void', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'Sync', 'bool', ['?int timeout_ms'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetVSync', 'void', ['bool enabled'], ['proxy'])

	gen.end_class(shared_renderer_async)

	# global rendering functions
	gen.bind_function('DrawBuffers', 'void', ['gs::gpu::Renderer &renderer', 'gs::uint index_count', 'gs::gpu::Buffer &idx', 'gs::gpu::Buffer &vtx', 'gs::core::VertexLayout &layout', '?gs::core::IndexType idx_type', '?gs::gpu::PrimitiveType primitive_type'])


def bind_render(gen):
	gen.add_include('engine/render_system.h')

	gen.bind_named_enum('gs::render::Eye', ['EyeMono', 'EyeStereoLeft', 'EyeStereoRight'])
	gen.bind_named_enum('gs::render::CullMode', ['CullBack', 'CullFront', 'CullNever'])
	gen.bind_named_enum('gs::render::BlendMode', ['BlendOpaque', 'BlendAlpha', 'BlendAdditive'])

	render_system = gen.begin_class('gs::render::RenderSystem', bound_name='RenderSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(render_system)
	shared_render_system = gen.begin_class('std::shared_ptr<gs::render::RenderSystem>', bound_name='RenderSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(render_system)})

	# gs::render::SurfaceShader
	gen.add_include('engine/surface_shader.h')

	surface_shader = gen.begin_class('gs::render::SurfaceShader', bound_name='SurfaceShader_nobind', noncopyable=True, nobind=True)
	gen.end_class(surface_shader)

	shared_surface_shader = gen.begin_class('std::shared_ptr<gs::render::SurfaceShader>', bound_name='SurfaceShader', features={'proxy': lib.stl.SharedPtrProxyFeature(surface_shader)})
	gen.bind_method_overloads(shared_surface_shader, 'SetUserUniformValue', [
		('bool', ['const char *name', 'gs::Vector4 value'], ['proxy']),
		('bool', ['const char *name', 'std::shared_ptr<gs::gpu::Texture> texture'], ['proxy'])
	])
	gen.end_class(shared_surface_shader)

	# gs::render::Material
	gen.add_include('engine/render_material.h')

	material = gen.begin_class('gs::render::Material', bound_name='RenderMaterial_nobind', noncopyable=True, nobind=True)
	gen.end_class(material)

	shared_material = gen.begin_class('std::shared_ptr<gs::render::Material>', bound_name='RenderMaterial', features={'proxy': lib.stl.SharedPtrProxyFeature(material)})
	gen.add_base(shared_material, gen.get_conv('std::shared_ptr<gs::gpu::Resource>'))

	gen.bind_method(shared_material, 'Create', 'bool', ['gs::render::RenderSystem &render_system', 'std::shared_ptr<gs::core::Material> material'], ['proxy'])
	gen.bind_method(shared_material, 'Free', 'void', [], ['proxy'])

	gen.bind_method(shared_material, 'Clone', 'std::shared_ptr<gs::render::Material>', [], ['proxy'])
	gen.bind_method(shared_material, 'IsReadyOrFailed', 'bool', [], ['proxy'])

	gen.bind_method(shared_material, 'GetSurfaceShader', 'const std::shared_ptr<gs::render::SurfaceShader> &', [], ['proxy'])
	gen.bind_method(shared_material, 'SetSurfaceShader', 'void', ['std::shared_ptr<gs::render::SurfaceShader> surface_shader'], ['proxy'])

	gen.insert_binding_code('''
static bool _RenderMaterial_GetFloat(gs::render::Material *m, const char *name, float &o0) { if (auto v = m->GetValue(name)) { o0 = v->fv[0]; return true; } return false; }
static bool _RenderMaterial_GetFloat2(gs::render::Material *m, const char *name, float &o0, float &o1) { if (auto v = m->GetValue(name)) { o0 = v->fv[0]; o1 = v->fv[1]; return true; } return false; }
static bool _RenderMaterial_GetFloat3(gs::render::Material *m, const char *name, float &o0, float &o1, float &o2) { if (auto v = m->GetValue(name)) { o0 = v->fv[0]; o1 = v->fv[1]; o2 = v->fv[2]; return true; } return false; }
static bool _RenderMaterial_GetFloat4(gs::render::Material *m, const char *name, float &o0, float &o1, float &o2, float &o3) { if (auto v = m->GetValue(name)) { o0 = v->fv[0]; o1 = v->fv[1]; o2 = v->fv[2]; o3 = v->fv[3]; return true; } return false; }

static bool _RenderMaterial_GetInt(gs::render::Material *m, const char *name, int &o0) { if (auto v = m->GetValue(name)) { o0 = v->iv[0]; return true; } return false; }
static bool _RenderMaterial_GetInt2(gs::render::Material *m, const char *name, int &o0, int &o1) { if (auto v = m->GetValue(name)) { o0 = v->iv[0]; o1 = v->iv[1]; return true; } return false; }
static bool _RenderMaterial_GetInt3(gs::render::Material *m, const char *name, int &o0, int &o1, int &o2) { if (auto v = m->GetValue(name)) { o0 = v->iv[0]; o1 = v->iv[1]; o2 = v->iv[2]; return true; } return false; }
static bool _RenderMaterial_GetInt4(gs::render::Material *m, const char *name, int &o0, int &o1, int &o2, int &o3) { if (auto v = m->GetValue(name)) { o0 = v->iv[0]; o1 = v->iv[1]; o2 = v->iv[2]; o3 = v->iv[3]; return true; } return false; }

static bool _RenderMaterial_GetUnsigned(gs::render::Material *m, const char *name, unsigned int &o0) { if (auto v = m->GetValue(name)) { o0 = v->uv[0]; return true; } return false; }
static bool _RenderMaterial_GetUnsigned2(gs::render::Material *m, const char *name, unsigned int &o0, unsigned int &o1) { if (auto v = m->GetValue(name)) { o0 = v->uv[0]; o1 = v->uv[1]; return true; } return false; }
static bool _RenderMaterial_GetUnsigned3(gs::render::Material *m, const char *name, unsigned int &o0, unsigned int &o1, unsigned int &o2) { if (auto v = m->GetValue(name)) { o0 = v->uv[0]; o1 = v->uv[1]; o2 = v->uv[2]; return true; } return false; }
static bool _RenderMaterial_GetUnsigned4(gs::render::Material *m, const char *name, unsigned int &o0, unsigned int &o1, unsigned int &o2, unsigned int &o3) { if (auto v = m->GetValue(name)) { o0 = v->uv[0]; o1 = v->uv[1]; o2 = v->uv[2]; o3 = v->uv[3]; return true; } return false; }

static bool _RenderMaterial_GetTexture(gs::render::Material *m, const char *name, std::shared_ptr<gs::gpu::Texture> &o) { if (auto v = m->GetValue(name)) { o = v->texture; return true; } return false; }

static bool _RenderMaterial_SetFloat(gs::render::Material *m, const char *name, float o0) { if (auto v = m->GetValue(name)) { v->fv[0] = o0; return true; } return false; }
static bool _RenderMaterial_SetFloat2(gs::render::Material *m, const char *name, float o0, float o1) { if (auto v = m->GetValue(name)) { v->fv[0] = o0; v->fv[1] = o1; return true; } return false; }
static bool _RenderMaterial_SetFloat3(gs::render::Material *m, const char *name, float o0, float o1, float o2) { if (auto v = m->GetValue(name)) { v->fv[0] = o0; v->fv[1] = o1; v->fv[2] = o2; return true; } return false; }
static bool _RenderMaterial_SetFloat4(gs::render::Material *m, const char *name, float o0, float o1, float o2, float o3) { if (auto v = m->GetValue(name)) { v->fv[0] = o0; v->fv[1] = o1; v->fv[2] = o2; v->fv[3] = o3; return true; } return false; }

static bool _RenderMaterial_SetInt(gs::render::Material *m, const char *name, int o0) { if (auto v = m->GetValue(name)) { v->iv[0] = o0; return true; } return false; }
static bool _RenderMaterial_SetInt2(gs::render::Material *m, const char *name, int o0, int o1) { if (auto v = m->GetValue(name)) { v->iv[0] = o0; v->iv[1] = o1; return true; } return false; }
static bool _RenderMaterial_SetInt3(gs::render::Material *m, const char *name, int o0, int o1, int o2) { if (auto v = m->GetValue(name)) { v->iv[0] = o0; v->iv[1] = o1; v->iv[2] = o2; return true; } return false; }
static bool _RenderMaterial_SetInt4(gs::render::Material *m, const char *name, int o0, int o1, int o2, int o3) { if (auto v = m->GetValue(name)) { v->iv[0] = o0; v->iv[1] = o1; v->iv[2] = o2; v->iv[3] = o3; return true; } return false; }

static bool _RenderMaterial_SetUnsigned(gs::render::Material *m, const char *name, unsigned int o0) { if (auto v = m->GetValue(name)) { v->uv[0] = o0; return true; } return false; }
static bool _RenderMaterial_SetUnsigned2(gs::render::Material *m, const char *name, unsigned int o0, unsigned int o1) { if (auto v = m->GetValue(name)) { v->uv[0] = o0; v->uv[1] = o1; return true; } return false; }
static bool _RenderMaterial_SetUnsigned3(gs::render::Material *m, const char *name, unsigned int o0, unsigned int o1, unsigned int o2) { if (auto v = m->GetValue(name)) { v->uv[0] = o0; v->uv[1] = o1; v->uv[2] = o2; return true; } return false; }
static bool _RenderMaterial_SetUnsigned4(gs::render::Material *m, const char *name, int o0, unsigned int o1, unsigned int o2, unsigned int o3) { if (auto v = m->GetValue(name)) { v->uv[0] = o0; v->uv[1] = o1; v->uv[2] = o2; v->uv[3] = o3; return true; } return false; }

static bool _RenderMaterial_SetTexture(gs::render::Material *m, const char *name, std::shared_ptr<gs::gpu::Texture> &o) { if (auto v = m->GetValue(name)) { v->texture = o; return true; } return false; }
''')

	# 
	gen.bind_method(shared_material, 'GetFloat', 'bool', ['const char *name', 'float &o0'], {'proxy': None, 'arg_out': ['o0'], 'route': lambda args: '_RenderMaterial_GetFloat(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetFloat2', 'bool', ['const char *name', 'float &o0', 'float &o1'], {'proxy': None, 'arg_out': ['o0', 'o1'], 'route': lambda args: '_RenderMaterial_GetFloat2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetFloat3', 'bool', ['const char *name', 'float &o0', 'float &o1', 'float &o2'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2'], 'route': lambda args: '_RenderMaterial_GetFloat3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetFloat4', 'bool', ['const char *name', 'float &o0', 'float &o1', 'float &o2', 'float &o3'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2', 'o3'], 'route': lambda args: '_RenderMaterial_GetFloat4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'GetInt', 'bool', ['const char *name', 'int &o0'], {'proxy': None, 'arg_out': ['o0'], 'route': lambda args: '_RenderMaterial_GetInt(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetInt2', 'bool', ['const char *name', 'int &o0', 'int &o1'], {'proxy': None, 'arg_out': ['o0', 'o1'], 'route': lambda args: '_RenderMaterial_GetInt2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetInt3', 'bool', ['const char *name', 'int &o0', 'int &o1', 'int &o2'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2'], 'route': lambda args: '_RenderMaterial_GetInt3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetInt4', 'bool', ['const char *name', 'int &o0', 'int &o1', 'int &o2', 'int &o3'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2', 'o3'], 'route': lambda args: '_RenderMaterial_GetInt4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'GetUnsigned', 'bool', ['const char *name', 'unsigned int &o0'], {'proxy': None, 'arg_out': ['o0'], 'route': lambda args: '_RenderMaterial_GetUnsigned(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetUnsigned2', 'bool', ['const char *name', 'unsigned int &o0', 'unsigned int &o1'], {'proxy': None, 'arg_out': ['o0', 'o1'], 'route': lambda args: '_RenderMaterial_GetUnsigned2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetUnsigned3', 'bool', ['const char *name', 'unsigned int &o0', 'unsigned int &o1', 'unsigned int &o2'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2'], 'route': lambda args: '_RenderMaterial_GetUnsigned3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetUnsigned4', 'bool', ['const char *name', 'unsigned int &o0', 'unsigned int &o1', 'unsigned int &o2', 'unsigned int &o3'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2', 'o3'], 'route': lambda args: '_RenderMaterial_GetUnsigned4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'GetTexture', 'bool', ['const char *name', 'std::shared_ptr<gs::gpu::Texture> &o'], {'proxy': None, 'arg_out': ['o'], 'route': lambda args: '_RenderMaterial_GetTexture(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'SetFloat', 'bool', ['const char *name', 'float o0'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetFloat(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetFloat2', 'bool', ['const char *name', 'float o0', 'float o1'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetFloat2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetFloat3', 'bool', ['const char *name', 'float o0', 'float o1', 'float o2'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetFloat3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetFloat4', 'bool', ['const char *name', 'float o0', 'float o1', 'float o2', 'float o3'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetFloat4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'SetInt', 'bool', ['const char *name', 'int o0'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetInt(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetInt2', 'bool', ['const char *name', 'int o0', 'int o1'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetInt2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetInt3', 'bool', ['const char *name', 'int o0', 'int o1', 'int o2'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetInt3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetInt4', 'bool', ['const char *name', 'int o0', 'int o1', 'int o2', 'int o3'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetInt4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'SetUnsigned', 'bool', ['const char *name', 'unsigned int o0'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetUnsigned(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetUnsigned2', 'bool', ['const char *name', 'unsigned int o0', 'unsigned int o1'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetUnsigned2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetUnsigned3', 'bool', ['const char *name', 'unsigned int o0', 'unsigned int o1', 'unsigned int o2'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetUnsigned3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetUnsigned4', 'bool', ['const char *name', 'unsigned int o0', 'unsigned int o1', 'unsigned int o2', 'unsigned int o3'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetUnsigned4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'SetTexture', 'bool', ['const char *name', 'std::shared_ptr<gs::gpu::Texture> &o'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetTexture(%s);' % (', '.join(args))})

	gen.end_class(shared_material)

	# gs::render::Geometry
	gen.add_include('engine/render_geometry.h')

	geometry = gen.begin_class('gs::render::Geometry', bound_name='RenderGeometry_nobind', noncopyable=True, nobind=True)
	gen.end_class(geometry)

	shared_geometry = gen.begin_class('std::shared_ptr<gs::render::Geometry>', bound_name='RenderGeometry', features={'proxy': lib.stl.SharedPtrProxyFeature(geometry)})
	gen.bind_constructor_overloads(shared_geometry, [
		([], ['proxy']),
		(['const char *name'], ['proxy']),
	])
	gen.bind_method(shared_geometry, 'SetMaterial', 'bool', ['gs::uint index', 'std::shared_ptr<gs::render::Material> material'], ['proxy'])

	gen.insert_binding_code('static gs::MinMax _render_Geometry_GetMinMax(gs::render::Geometry *geo) { return geo->minmax; }')
	gen.bind_method(shared_geometry, 'GetMinMax', 'gs::MinMax', [], {'proxy': None, 'route': route_lambda('_render_Geometry_GetMinMax')})

	gen.insert_binding_code('''
static std::shared_ptr<gs::render::Material> _RenderGeometry_GetMaterial(gs::render::Geometry *geo, gs::uint idx) {
	if (idx >= geo->materials.size())
		return nullptr;
	return geo->materials[idx];
}
static int _RenderGeometry_GetMaterialCount(gs::render::Geometry *geo) { return geo->materials.size(); } 
''')
	gen.bind_method(shared_geometry, 'GetMaterial', 'std::shared_ptr<gs::render::Material>', ['gs::uint index'], {'proxy': None, 'route': route_lambda('_RenderGeometry_GetMaterial'), 'check_rval': check_rval_lambda(gen, 'Empty material')})
	gen.bind_method(shared_geometry, 'GetMaterialCount', 'int', [], {'proxy': None, 'route': route_lambda('_RenderGeometry_GetMaterialCount')})

	gen.insert_binding_code('''
static void _RenderGeometry_SetLodProxy(gs::render::Geometry *geo, std::shared_ptr<gs::render::Geometry> &proxy, float distance) {
	geo->flag &= ~gs::core::GeometryFlag::NullLodProxy;
	geo->lod_proxy = proxy;
	geo->lod_distance = distance;
}

static void _RenderGeometry_SetNullLodProxy(gs::render::Geometry *geo) {
	geo->flag |= gs::core::GeometryFlag::NullLodProxy;
	geo->lod_proxy = nullptr;
	geo->lod_distance = 0;
}

static void _RenderGeometry_SetShadowProxy(gs::render::Geometry *geo, std::shared_ptr<gs::render::Geometry> &proxy) {
	geo->flag &= ~gs::core::GeometryFlag::NullShadowProxy;
	geo->shadow_proxy = proxy;
}

static void _RenderGeometry_SetNullShadowProxy(gs::render::Geometry *geo) {
	geo->flag |= gs::core::GeometryFlag::NullShadowProxy;
	geo->shadow_proxy = nullptr;
}
''')
	gen.bind_method(shared_geometry, 'SetLodProxy', 'void', ['std::shared_ptr<gs::render::Geometry> &proxy', 'float distance'], {'proxy': None, 'route': route_lambda('_RenderGeometry_SetLodProxy')})
	gen.bind_method(shared_geometry, 'SetNullLodProxy', 'void', [], {'proxy': None, 'route': route_lambda('_RenderGeometry_SetNullLodProxy')})
	gen.bind_method(shared_geometry, 'SetShadowProxy', 'void', ['std::shared_ptr<gs::render::Geometry> &proxy'], {'proxy': None, 'route': route_lambda('_RenderGeometry_SetShadowProxy')})
	gen.bind_method(shared_geometry, 'SetNullShadowProxy', 'void', [], {'proxy': None, 'route': route_lambda('_RenderGeometry_SetNullShadowProxy')})

	gen.end_class(shared_geometry)

	# gs::render::Statistics
	gen.add_include('engine/render_stats.h')

	render_stats = gen.begin_class('gs::render::Statistics')
	gen.bind_members(render_stats, ['gs::time_ns frame_start', 'uint32_t render_primitive_drawn', 'uint32_t line_drawn', 'uint32_t triangle_drawn', 'uint32_t instanced_batch_count', 'uint32_t instanced_batch_size'])
	gen.end_class(render_stats)

	# gs::render::ViewState
	view_state = gen.begin_class('gs::render::ViewState')
	gen.bind_members(view_state, ['gs::Rect<float> viewport', 'gs::Rect<float> clipping', 'gs::Matrix4 view', 'gs::Matrix44 projection', 'gs::FrustumPlanes frustum_planes', 'gs::render::Eye eye'])
	gen.end_class(view_state)

	# gs::render::RenderSystem
	gen.bind_named_enum('gs::render::RenderSystem::RenderTechnique', ['TechniqueForward', 'TechniqueDeferred'], prefix='Render')
	lib.stl.bind_future_T(gen, 'gs::render::RenderSystem::RenderTechnique', 'FutureRenderTechnique')

	gen.bind_constructor(shared_render_system, [], ['proxy'])

	gen.bind_method(shared_render_system, 'GetRenderer', 'const std::shared_ptr<gs::gpu::Renderer> &', [], ['proxy'])

	gen.bind_method_overloads(shared_render_system, 'Initialize', [
		('bool', ['std::shared_ptr<gs::gpu::Renderer> renderer'], ['proxy']),
		('bool', ['std::shared_ptr<gs::gpu::Renderer> renderer', 'bool support_3d'], ['proxy'])
	])
	gen.bind_method(shared_render_system, 'IsInitialized', 'bool', [], ['proxy'])

	gen.bind_method(shared_render_system, 'GetInternalResolution', 'gs::tVector2<int>', [], ['proxy'])
	gen.bind_method(shared_render_system, 'SetInternalResolution', 'void', ['const gs::tVector2<int> &resolution'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetViewportToInternalResolutionRatio', 'gs::tVector2<float>', [], ['proxy'])

	gen.bind_method(shared_render_system, 'GetStatistics', 'gs::render::Statistics', [], ['proxy'])

	gen.bind_method(shared_render_system, 'SetAA', 'void', ['gs::uint sample_count'], ['proxy'])
	gen.bind_method(shared_render_system, 'PurgeCache', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_render_system, 'RefreshCacheEntry', 'void', ['const char *name'], ['proxy'])

	gen.bind_method(shared_render_system, 'HasMaterial', 'std::shared_ptr<gs::render::Material>', ['const char *name'], ['proxy'])
	gen.bind_method_overloads(shared_render_system, 'LoadMaterial', [
		('std::shared_ptr<gs::render::Material>', ['const char *name'], ['proxy']),
		('std::shared_ptr<gs::render::Material>', ['const char *name', 'bool use_cache'], ['proxy'])
	])
	gen.bind_method_overloads(shared_render_system, 'CreateMaterial', [
		('std::shared_ptr<gs::render::Material>', ['const std::shared_ptr<gs::core::Material> &material'], ['proxy']),
		('std::shared_ptr<gs::render::Material>', ['const std::shared_ptr<gs::core::Material> &material', 'bool use_cache'], ['proxy'])
	])

	gen.bind_method(shared_render_system, 'HasGeometry', 'std::shared_ptr<gs::render::Geometry>', ['const char *name'], ['proxy'])
	gen.bind_method_overloads(shared_render_system, 'LoadGeometry', [
		('std::shared_ptr<gs::render::Geometry>', ['const char *name'], ['proxy']),
		('std::shared_ptr<gs::render::Geometry>', ['const char *name', 'bool use_cache'], ['proxy'])
	])
	gen.bind_method_overloads(shared_render_system, 'CreateGeometry', [
		('std::shared_ptr<gs::render::Geometry>', ['const std::shared_ptr<gs::core::Geometry> &geometry'], ['proxy']),
		('std::shared_ptr<gs::render::Geometry>', ['const std::shared_ptr<gs::core::Geometry> &geometry', 'bool use_cache'], ['proxy'])
	])

	gen.bind_method(shared_render_system, 'HasSurfaceShader', 'std::shared_ptr<gs::render::SurfaceShader>', ['const char *name'], ['proxy'])
	gen.bind_method_overloads(shared_render_system, 'LoadSurfaceShader', [
		('std::shared_ptr<gs::render::SurfaceShader>', ['const char *name'], ['proxy']),
		('std::shared_ptr<gs::render::SurfaceShader>', ['const char *name', 'bool use_cache'], ['proxy'])
	])

	gen.bind_method(shared_render_system, 'GetRenderTechnique', 'gs::render::RenderSystem::RenderTechnique', [], ['proxy'])
	gen.bind_method(shared_render_system, 'SetRenderTechnique', 'void', ['gs::render::RenderSystem::RenderTechnique render_technique'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetFrameClock', 'gs::time_ns', [], ['proxy'])

	gen.bind_method_overloads(shared_render_system, 'SetView', [
		('void', ['const gs::Matrix4 &view', 'const gs::Matrix44 &projection'], ['proxy']),
		('void', ['const gs::Matrix4 &view', 'const gs::Matrix44 &projection', 'gs::render::Eye eye'], ['proxy'])
	])
	gen.bind_method(shared_render_system, 'GetEye', 'gs::render::Eye', [], ['proxy'])

	gen.bind_method(shared_render_system, 'GetViewState', 'gs::render::ViewState', [], ['proxy'])
	gen.bind_method(shared_render_system, 'SetViewState', 'void', ['const gs::render::ViewState &view_state'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetViewFrustum', 'const gs::FrustumPlanes &', [], ['proxy'])

	gen.bind_method(shared_render_system, 'DrawRasterFontBatch', 'void', [], ['proxy'])

	gen.bind_method_overloads(shared_render_system, 'SetShaderAuto', [
		('bool', ['bool has_color'], ['proxy']),
		('bool', ['bool has_color', 'const gs::gpu::Texture &texture'], ['proxy'])
	])

	gen.insert_binding_code('''\
static void RenderSystemDrawLine_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos) { render_system->DrawLine(count, pos.data()); }
static void RenderSystemDrawLine_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col) { render_system->DrawLine(count, pos.data(), col.data()); }
static void RenderSystemDrawLine_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col, const std::vector<gs::tVector2<float>> &uv) { render_system->DrawLine(count, pos.data(), col.data(), uv.data()); }

static void RenderSystemDrawTriangle_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos) { render_system->DrawTriangle(count, pos.data()); }
static void RenderSystemDrawTriangle_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col) { render_system->DrawTriangle(count, pos.data(), col.data()); }
static void RenderSystemDrawTriangle_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col, const std::vector<gs::tVector2<float>> &uv) { render_system->DrawTriangle(count, pos.data(), col.data(), uv.data()); }

static void RenderSystemDrawSprite_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos) { render_system->DrawSprite(count, pos.data()); }
static void RenderSystemDrawSprite_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col) { render_system->DrawSprite(count, pos.data(), col.data()); }
static void RenderSystemDrawSprite_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col, const std::vector<float> &size) { render_system->DrawSprite(count, pos.data(), col.data(), size.data()); }
\n''', 'wrapper signatures to cast target language list and std::vector to raw pointers')

	DrawLine_wrapper_route = lambda args: 'RenderSystemDrawLine_wrapper(%s);' % (', '.join(args))
	DrawTriangle_wrapper_route = lambda args: 'RenderSystemDrawTriangle_wrapper(%s);' % (', '.join(args))
	DrawSprite_wrapper_route = lambda args: 'RenderSystemDrawSprite_wrapper(%s);' % (', '.join(args))

	draw_line_protos = [
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos'], {'proxy': None, 'route': DrawLine_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col'], {'proxy': None, 'route': DrawLine_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col', 'const std::vector<gs::tVector2<float>> &uv'], {'proxy': None, 'route': DrawLine_wrapper_route})	]
	if gen.get_language() == "CPython":
		draw_line_protos += [
			('void', ['gs::uint count', 'PySequenceOfVector3 pos'], {'proxy': None, 'route': DrawLine_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col'], {'proxy': None, 'route': DrawLine_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col', 'PySequenceOfVector2 uv'], {'proxy': None, 'route': DrawLine_wrapper_route})	]

	gen.bind_method_overloads(shared_render_system, 'DrawLine', draw_line_protos)

	draw_triangle_protos = [
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos'], {'proxy': None, 'route': DrawTriangle_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col'], {'proxy': None, 'route': DrawTriangle_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col', 'const std::vector<gs::tVector2<float>> &uv'], {'proxy': None, 'route': DrawTriangle_wrapper_route})	]
	if gen.get_language() == "CPython":
		draw_triangle_protos += [
			('void', ['gs::uint count', 'PySequenceOfVector3 pos'], {'proxy': None, 'route': DrawTriangle_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col'], {'proxy': None, 'route': DrawTriangle_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col', 'PySequenceOfVector2 uv'], {'proxy': None, 'route': DrawTriangle_wrapper_route})	]

	gen.bind_method_overloads(shared_render_system, 'DrawTriangle', draw_triangle_protos)

	draw_sprite_protos = [
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos'], {'proxy': None, 'route': DrawSprite_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col'], {'proxy': None, 'route': DrawSprite_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col', 'const std::vector<float> &size'], {'proxy': None, 'route': DrawSprite_wrapper_route})	]
	if gen.get_language() == "CPython":
		draw_sprite_protos += [
			('void', ['gs::uint count', 'PySequenceOfVector3 pos'], {'proxy': None, 'route': DrawSprite_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col'], {'proxy': None, 'route': DrawSprite_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col', 'PySequenceOfFloat size'], {'proxy': None, 'route': DrawSprite_wrapper_route})	]

	gen.bind_method_overloads(shared_render_system, 'DrawSprite', draw_sprite_protos)

	gen.insert_binding_code('''\
static void RenderSystemDrawLineAuto_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos) { render_system->DrawLineAuto(count, pos.data()); }
static void RenderSystemDrawLineAuto_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col) { render_system->DrawLineAuto(count, pos.data(), col.data()); }
static void RenderSystemDrawLineAuto_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col, const std::vector<gs::tVector2<float>> &uv, const gs::gpu::Texture *texture) { render_system->DrawLineAuto(count, pos.data(), col.data(), uv.data(), texture); }

static void RenderSystemDrawTriangleAuto_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos) { render_system->DrawTriangleAuto(count, pos.data()); }
static void RenderSystemDrawTriangleAuto_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col) { render_system->DrawTriangleAuto(count, pos.data(), col.data()); }
static void RenderSystemDrawTriangleAuto_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const std::vector<gs::Color> &col, const std::vector<gs::tVector2<float>> &uv, const gs::gpu::Texture *texture) { render_system->DrawTriangleAuto(count, pos.data(), col.data(), uv.data(), texture); }

static void RenderSystemDrawSpriteAuto_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const gs::gpu::Texture &texture) { render_system->DrawSpriteAuto(count, pos.data(), texture); }
static void RenderSystemDrawSpriteAuto_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const gs::gpu::Texture &texture, const std::vector<gs::Color> &col) { render_system->DrawSpriteAuto(count, pos.data(), texture, col.data()); }
static void RenderSystemDrawSpriteAuto_wrapper(gs::render::RenderSystem *render_system, gs::uint count, const std::vector<gs::Vector3> &pos, const gs::gpu::Texture &texture, const std::vector<gs::Color> &col, const std::vector<float> &size) { render_system->DrawSpriteAuto(count, pos.data(), texture, col.data(), size.data()); }
\n''', 'wrapper signatures to cast target language list and std::vector to raw pointers')

	DrawLineAuto_wrapper_route = lambda args: 'RenderSystemDrawLineAuto_wrapper(%s);' % (', '.join(args))
	DrawTriangleAuto_wrapper_route = lambda args: 'RenderSystemDrawTriangleAuto_wrapper(%s);' % (', '.join(args))
	DrawSpriteAuto_wrapper_route = lambda args: 'RenderSystemDrawSpriteAuto_wrapper(%s);' % (', '.join(args))

	draw_line_auto_protos = [
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos'], {'proxy': None, 'route': DrawLineAuto_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col'], {'proxy': None, 'route': DrawLineAuto_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col', 'const std::vector<gs::tVector2<float>> &uv', 'const gs::gpu::Texture *texture'], {'proxy': None, 'route': DrawLineAuto_wrapper_route})	]
	if gen.get_language() == "CPython":
		draw_line_auto_protos += [	
			('void', ['gs::uint count', 'PySequenceOfVector3 pos'], {'proxy': None, 'route': DrawLineAuto_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col'], {'proxy': None, 'route': DrawLineAuto_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col', 'PySequenceOfVector2 uv', 'const gs::gpu::Texture *texture'], {'proxy': None, 'route': DrawLineAuto_wrapper_route})	]

	gen.bind_method_overloads(shared_render_system, 'DrawLineAuto', draw_line_auto_protos)

	draw_triangle_auto_protos = [
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos'], {'proxy': None, 'route': DrawTriangleAuto_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col'], {'proxy': None, 'route': DrawTriangleAuto_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const std::vector<gs::Color> &col', 'const std::vector<gs::tVector2<float>> &uv', 'const gs::gpu::Texture *texture'], {'proxy': None, 'route': DrawTriangleAuto_wrapper_route})	]
	if gen.get_language() == "CPython":
		draw_triangle_auto_protos += [
			('void', ['gs::uint count', 'PySequenceOfVector3 pos'], {'proxy': None, 'route': DrawTriangleAuto_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col'], {'proxy': None, 'route': DrawTriangleAuto_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'PySequenceOfColor col', 'PySequenceOfVector2 uv', 'const gs::gpu::Texture *texture'], {'proxy': None, 'route': DrawTriangleAuto_wrapper_route})	]

	gen.bind_method_overloads(shared_render_system, 'DrawTriangleAuto', draw_triangle_auto_protos)

	draw_sprite_auto_protos = [
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const gs::gpu::Texture &texture'], {'proxy': None, 'route': DrawSpriteAuto_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const gs::gpu::Texture &texture', 'const std::vector<gs::Color> &col'], {'proxy': None, 'route': DrawSpriteAuto_wrapper_route}),
		('void', ['gs::uint count', 'const std::vector<gs::Vector3> &pos', 'const gs::gpu::Texture &texture', 'const std::vector<gs::Color> &col', 'const std::vector<float> &size'], {'proxy': None, 'route': DrawSpriteAuto_wrapper_route})	]
	if gen.get_language() == "CPython":
		draw_sprite_auto_protos += [
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'const gs::gpu::Texture &texture'], {'proxy': None, 'route': DrawSpriteAuto_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'const gs::gpu::Texture &texture', 'PySequenceOfColor col'], {'proxy': None, 'route': DrawSpriteAuto_wrapper_route}),
			('void', ['gs::uint count', 'PySequenceOfVector3 pos', 'const gs::gpu::Texture &texture', 'PySequenceOfColor col', 'PySequenceOfFloat size'], {'proxy': None, 'route': DrawSpriteAuto_wrapper_route})	]

	gen.bind_method_overloads(shared_render_system, 'DrawSpriteAuto', draw_sprite_auto_protos)

	gen.bind_method(shared_render_system, 'DrawQuad2D', 'void', ['const gs::Rect<float> &src_rect', 'const gs::Rect<float> &dst_rect'], ['proxy'])
	gen.bind_method(shared_render_system, 'DrawFullscreenQuad', 'void', ['const gs::tVector2<float> &uv'], ['proxy'])

	gen.bind_method(shared_render_system, 'DrawGeometrySimple', 'void', ['const gs::render::Geometry &geometry'], ['proxy'])
	#gen.bind_method(shared_render_system, 'DrawSceneSimple', 'void', ['const gs::core::Scene &scene'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetShadowMap', 'const std::shared_ptr<gs::gpu::Texture> &', [], ['proxy'])
	gen.end_class(shared_render_system)

	# gs::render::RenderSystemAsync
	gen.add_include('engine/render_system_async.h')

	render_system_async = gen.begin_class('gs::render::RenderSystemAsync', bound_name='RenderSystemAsync_nobind', noncopyable=True, nobind=True)
	gen.end_class(render_system_async)

	shared_render_system_async = gen.begin_class('std::shared_ptr<gs::render::RenderSystemAsync>', bound_name='RenderSystemAsync', features={'proxy': lib.stl.SharedPtrProxyFeature(render_system_async)})
	gen.bind_constructor(shared_render_system_async, ['std::shared_ptr<gs::render::RenderSystem> render_system'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'GetRenderSystem', 'const std::shared_ptr<gs::render::RenderSystem> &', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'GetRenderTechnique', 'std::future<gs::render::RenderSystem::RenderTechnique>', [], ['proxy'])
	gen.bind_method(shared_render_system_async, 'SetRenderTechnique', 'void', ['gs::render::RenderSystem::RenderTechnique technique'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'GetInternalResolution', 'std::future<gs::tVector2<int>>', [], ['proxy'])
	gen.bind_method(shared_render_system_async, 'SetInternalResolution', 'void', ['const gs::tVector2<int> &resolution'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'GetViewportToInternalResolutionRatio', 'std::future<gs::tVector2<float>>', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'SetAA', 'void', ['gs::uint sample_count'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'SetView', 'void', ['const gs::Matrix4 &view', 'const gs::Matrix44 &projection'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'PurgeCache', 'std::future<gs::uint>', [], ['proxy'])
	gen.bind_method(shared_render_system_async, 'RefreshCacheEntry', 'void', ['const char *name'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'DrawRasterFontBatch', 'void', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'HasMaterial', 'std::shared_ptr<gs::render::Material>', ['const char *name'], ['proxy'])
	gen.bind_method_overloads(shared_render_system_async, 'LoadMaterial', [
		('std::shared_ptr<gs::render::Material>', ['const char *name', '?bool use_cache'], ['proxy']),
		('std::shared_ptr<gs::render::Material>', ['const char *name', 'const char *source', '?gs::DocumentFormat format', '?bool use_cache'], ['proxy'])
	])
	gen.bind_method(shared_render_system_async, 'CreateMaterial', 'std::shared_ptr<gs::render::Material>', ['const std::shared_ptr<gs::core::Material> &material', '?bool use_cache'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'HasGeometry', 'std::shared_ptr<gs::render::Geometry>', ['const char *name'], ['proxy'])
	gen.bind_method_overloads(shared_render_system_async, 'LoadGeometry', [
		('std::shared_ptr<gs::render::Geometry>', ['const char *name', '?bool use_cache'], ['proxy']),
		('std::shared_ptr<gs::render::Geometry>', ['const char *name', 'const char *source', '?gs::DocumentFormat format', '?bool use_cache'], ['proxy'])
	])
	gen.bind_method(shared_render_system_async, 'CreateGeometry', 'std::shared_ptr<gs::render::Geometry>', ['const std::shared_ptr<gs::core::Geometry> &geometry', '?bool use_cache'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'HasSurfaceShader', 'std::shared_ptr<gs::render::SurfaceShader>', ['const char *name'], ['proxy'])
	gen.bind_method(shared_render_system_async, 'LoadSurfaceShader', 'std::shared_ptr<gs::render::SurfaceShader>', ['const char *name', '?bool use_cache'], ['proxy'])

	"""
	void DrawLine(uint count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<Vector2> *uv = nullptr) {
	void DrawTriangle(uint count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<Vector2> *uv = nullptr) {
	void DrawSprite(uint count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<float> *size = nullptr, float global_size = 1.f) {
	void DrawLineAuto(uint count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<Vector2> *uv = nullptr, gpu::sTexture texture = nullptr) {
	void DrawTriangleAuto(uint count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<Vector2> *uv = nullptr, gpu::sTexture texture = nullptr) {
	void DrawSpriteAuto(uint count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<float> *size = nullptr, gpu::sTexture texture = nullptr, float global_size = 1.f) {
	"""

	gen.bind_method(shared_render_system_async, 'BeginDrawFrame', 'void', [], ['proxy'])
	gen.bind_method(shared_render_system_async, 'EndDrawFrame', 'void', [], ['proxy'])

	#gen.bind_method(shared_render_system_async, 'DrawRenderablesPicking', 'std::future<bool>', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'Initialize', 'std::future<bool>', ['std::shared_ptr<gs::gpu::Renderer> renderer', '?bool support_3d'], ['proxy'])
	gen.bind_method(shared_render_system_async, 'Free', 'std::future<void>', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'SetShaderEngineValues', 'void', [], ['proxy'])

	gen.end_class(shared_render_system_async)

	# gs::render::RasterFont
	gen.add_include('engine/raster_font.h')

	raster_font = gen.begin_class('gs::render::RasterFont', bound_name='RasterFont_nobind', nobind=True)
	gen.end_class(raster_font)

	shared_raster_font = gen.begin_class('std::shared_ptr<gs::render::RasterFont>', bound_name='RasterFont', features={'proxy': lib.stl.SharedPtrProxyFeature(raster_font)})
	gen.bind_constructor_overloads(shared_raster_font, [
		(['const char *font_path', 'float font_size'], ['proxy']),
		(['const char *font_path', 'float font_size', 'gs::uint page_resolution'], ['proxy']),
		(['const char *font_path', 'float font_size', 'gs::uint page_resolution', 'gs::uint glyph_margin'], ['proxy']),
		(['const char *font_path', 'float font_size', 'gs::uint page_resolution', 'gs::uint glyph_margin', 'bool autohint'], ['proxy'])
	])

	gen.bind_method(shared_raster_font, 'Prepare', 'bool', ['gs::render::RenderSystem &render_system', 'const char *text'], ['proxy'])
	gen.bind_method_overloads(shared_raster_font, 'Write', [
		('bool', ['gs::render::RenderSystem &render_system', 'const char *text', 'const gs::Matrix4 &matrix'], ['proxy']),
		('bool', ['gs::render::RenderSystem &render_system', 'const char *text', 'const gs::Matrix4 &matrix', 'gs::Color color'], ['proxy']),
		('bool', ['gs::render::RenderSystem &render_system', 'const char *text', 'const gs::Matrix4 &matrix', 'gs::Color color', 'float scale'], ['proxy']),
		('bool', ['gs::render::RenderSystem &render_system', 'const char *text', 'const gs::Matrix4 &matrix', 'gs::Color color', 'float scale', 'bool snap_glyph_to_grid', 'bool orient_toward_camera'], ['proxy'])
	])

	gen.bind_method(shared_raster_font, 'GetTextRect', 'gs::Rect<float>', ['gs::render::RenderSystem &render_system', 'const char *text'], ['proxy'])

	gen.bind_method(shared_raster_font, 'Load', 'bool', ['const gs::render::RenderSystem &render_system', 'const char *base_path'], ['proxy'])
	gen.bind_method(shared_raster_font, 'Save', 'bool', ['const gs::render::RenderSystem &render_system', 'const char *base_path'], ['proxy'])

	gen.bind_method(shared_raster_font, 'GetSize', 'float', [], ['proxy'])
	gen.end_class(shared_raster_font)

	# gs::render::SimpleGraphicEngine
	gen.add_include('engine/simple_graphic_engine.h')

	simple_graphic_engine = gen.begin_class('gs::render::SimpleGraphicEngine', bound_name='SimpleGraphicEngine', noncopyable=True)
	gen.bind_constructor(simple_graphic_engine, [])

	gen.bind_method(simple_graphic_engine, 'SetSnapGlyphToGrid', 'void', ['bool snap'])
	gen.bind_method(simple_graphic_engine, 'GetSnapGlyphToGrid', 'bool', [])

	gen.bind_method(simple_graphic_engine, 'SetBlendMode', 'void', ['gs::render::BlendMode mode'])
	gen.bind_method(simple_graphic_engine, 'GetBlendMode', 'gs::render::BlendMode', [])
	gen.bind_method(simple_graphic_engine, 'SetCullMode', 'void', ['gs::render::CullMode mode'])
	gen.bind_method(simple_graphic_engine, 'GetCullMode', 'gs::render::CullMode', [])

	gen.bind_method(simple_graphic_engine, 'SetDepthWrite', 'void', ['bool enable'])
	gen.bind_method(simple_graphic_engine, 'GetDepthWrite', 'bool', [])
	gen.bind_method(simple_graphic_engine, 'SetDepthTest', 'void', ['bool enable'])
	gen.bind_method(simple_graphic_engine, 'GetDepthTest', 'bool', [])

	gen.insert_binding_code('''
static void _Quad(gs::render::SimpleGraphicEngine *engine, float ax, float ay, float az, float bx, float by, float bz, float cx, float cy, float cz, float dx, float dy, float dz, const gs::Color &a_color, const gs::Color &b_color, const gs::Color &c_color, const gs::Color &d_color) {
	engine->Quad(ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz, 0, 0, 0, 0, nullptr, a_color, b_color, c_color, d_color);
}
''')

	gen.bind_method(simple_graphic_engine, 'Line', 'void', ['float sx', 'float sy', 'float sz', 'float ex', 'float ey', 'float ez', 'const gs::Color &start_color', 'const gs::Color &end_color'])
	gen.bind_method(simple_graphic_engine, 'Triangle', 'void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'const gs::Color &a_color', 'const gs::Color &b_color', 'const gs::Color &c_color'])
	gen.bind_method_overloads(simple_graphic_engine, 'Text', [
		('void', ['float x', 'float y', 'float z', 'const char *text', 'const gs::Color &color', 'std::shared_ptr<gs::render::RasterFont> font', 'float scale'], []),
		('void', ['const gs::Matrix4 &mat', 'const char *text', 'const gs::Color &color', 'std::shared_ptr<gs::render::RasterFont> font', 'float scale'], [])
	])
	gen.bind_method_overloads(simple_graphic_engine, 'Quad', [
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'const gs::Color &a_color', 'const gs::Color &b_color', 'const gs::Color &c_color', 'const gs::Color &d_color'], {'route': lambda args: '_Quad(%s);' % ', '.join(args)}),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'float uv_sx', 'float uv_sy', 'float uv_ex', 'float uv_ey', 'std::shared_ptr<gs::gpu::Texture> texture', 'const gs::Color &a_color', 'const gs::Color &b_color', 'const gs::Color &c_color', 'const gs::Color &d_color'], [])
	])
	gen.bind_method(simple_graphic_engine, 'Geometry', 'void', ['float x', 'float y', 'float z', 'float ex', 'float ey', 'float ez', 'float sx', 'float sy', 'float sz', 'std::shared_ptr<gs::render::Geometry> geometry'])

	gen.bind_method(simple_graphic_engine, 'Draw', 'void', ['gs::render::RenderSystem &render_system'])
	gen.bind_method(simple_graphic_engine, 'Clear', 'void', ['gs::render::RenderSystem &render_system'])

	gen.bind_method(simple_graphic_engine, 'Flush', 'void', ['gs::render::RenderSystem &render_system'])

	gen.end_class(simple_graphic_engine)


def bind_iso_surface(gen):
	gen.add_include('engine/iso_surface.h')

	iso_surface = gen.begin_class('gs::core::IsoSurface', bound_name='IsoSurface_nobind', nobind=True)
	gen.end_class(iso_surface)

	shared_iso_surface = gen.begin_class('std::shared_ptr<gs::core::IsoSurface>', bound_name='IsoSurface', features={'proxy': lib.stl.SharedPtrProxyFeature(iso_surface)})
	gen.bind_constructor(shared_iso_surface, [], ['proxy'])
	gen.bind_method(shared_iso_surface, 'Clear', 'void', [], ['proxy'])
	gen.bind_method(shared_iso_surface, 'AddTriangle', 'void', ['const gs::Vector3 &p0', 'const gs::Vector3 &p1', 'const gs::Vector3 &p2'], ['proxy'])
	gen.bind_method(shared_iso_surface, 'GetTriangleCount', 'gs::uint', [], ['proxy'])
	gen.end_class(shared_iso_surface)

	#
	gen.bind_function_overloads('PolygoniseIsoSurface', [
		('void', ['gs::uint width', 'gs::uint height', 'gs::uint depth', 'const float *field', 'float isolevel', 'gs::core::IsoSurface &out'], []),
		('void', ['gs::uint width', 'gs::uint height', 'gs::uint depth', 'const float *field', 'float isolevel', 'gs::core::IsoSurface &out', 'const gs::Vector3 &unit'], [])
	])
	gen.bind_function('IsoSurfaceToCoreGeometry', 'void', ['const gs::core::IsoSurface &iso', 'gs::core::Geometry &out'])

	gen.bind_function('IsoSurfaceToRenderGeometry', 'std::future<void>', ['std::shared_ptr<gs::render::RenderSystem> render_system', 'std::shared_ptr<gs::core::IsoSurface> iso', 'std::shared_ptr<gs::render::Geometry> geo', 'std::shared_ptr<gs::render::Material> mat'])
	gen.bind_function_overloads('PolygoniseIsoSurfaceToRenderGeometry', [
		('std::future<void>', ['std::shared_ptr<gs::render::RenderSystem> render_system', 'std::shared_ptr<gs::render::Geometry> geo', 'std::shared_ptr<gs::render::Material> mat', 'gs::uint width', 'gs::uint height', 'gs::uint depth', 'const float *field', 'float isolevel', 'std::shared_ptr<gs::core::IsoSurface> iso'], []),
		('std::future<void>', ['std::shared_ptr<gs::render::RenderSystem> render_system', 'std::shared_ptr<gs::render::Geometry> geo', 'std::shared_ptr<gs::render::Material> mat', 'gs::uint width', 'gs::uint height', 'gs::uint depth', 'const float *field', 'float isolevel', 'std::shared_ptr<gs::core::IsoSurface> iso', 'const gs::Vector3 &unit'], [])
	])


def bind_plus(gen):
	gen.add_include('engine/plus.h')

	# gs::RenderWindow
	window_conv = gen.begin_class('gs::RenderWindow')
	gen.end_class(window_conv)

	# gs::Plus
	plus_conv = gen.begin_class('gs::Plus', noncopyable=True)

	gen.bind_method(plus_conv, 'CreateWorkers', 'void', [])
	gen.bind_method(plus_conv, 'DeleteWorkers', 'void', [])

	gen.bind_method(plus_conv, 'MountFilePath', 'void', ['const char *path'])

	gen.bind_method(plus_conv, 'GetRenderer', 'std::shared_ptr<gs::gpu::Renderer>', [], {'check_rval': check_rval_lambda(gen, 'no renderer, was RenderInit called succesfully?')})
	gen.bind_method(plus_conv, 'GetRendererAsync', 'std::shared_ptr<gs::gpu::RendererAsync>', [], {'check_rval': check_rval_lambda(gen, 'no renderer, was RenderInit called succesfully?')})

	gen.bind_method(plus_conv, 'GetRenderSystem', 'std::shared_ptr<gs::render::RenderSystem>', [], {'check_rval': check_rval_lambda(gen, 'no render system, was RenderInit called succesfully?')})
	gen.bind_method(plus_conv, 'GetRenderSystemAsync', 'std::shared_ptr<gs::render::RenderSystemAsync>', [], {'check_rval': check_rval_lambda(gen, 'no render system, was RenderInit called succesfully?')})

	gen.bind_method(plus_conv, 'AudioInit', 'bool', [], {'check_rval': check_rval_lambda(gen, 'AudioInit failed, was LoadPlugins called succesfully?')})
	gen.bind_method(plus_conv, 'AudioUninit', 'void', [])

	gen.bind_method(plus_conv, 'GetMixer', 'std::shared_ptr<gs::audio::Mixer>', [], {'check_rval': check_rval_lambda(gen, 'no mixer, was AudioInit called succesfully?')})
	gen.bind_method(plus_conv, 'GetMixerAsync', 'std::shared_ptr<gs::audio::MixerAsync>', [], {'check_rval': check_rval_lambda(gen, 'no mixer, was AudioInit called succesfully?')})

	gen.bind_named_enum('gs::Plus::AppEndCondition', ['EndOnEscapePressed', 'EndOnDefaultWindowClosed', 'EndOnAny'], prefix='App')

	gen.bind_method_overloads(plus_conv, 'IsAppEnded', [
		('bool', [], []),
		('bool', ['gs::Plus::AppEndCondition flags'], [])
	])

	gen.insert_binding_code('''\
static bool _Plus_RenderInit(gs::Plus *plus, int width, int height, int aa = 1, gs::Window::Visibility vis = gs::Window::Windowed, bool debug = false) { return plus->RenderInit(width, height, nullptr, aa, vis, debug); }
''')
	gen.bind_method_overloads(plus_conv, 'RenderInit', [
		('bool', ['int width', 'int height', '?const char *core_path', '?int aa', '?gs::Window::Visibility visibility', '?bool debug'], {'check_rval': check_rval_lambda(gen, 'RenderInit failed, was LoadPlugins called succesfully?')}),
		('bool', ['int width', 'int height', 'int aa', '?gs::Window::Visibility visibility', '?bool debug'], {'check_rval': check_rval_lambda(gen, 'RenderInit failed, was LoadPlugins called succesfully?'), 'route': lambda args: '_Plus_RenderInit(%s);' % (', '.join(args))})
	])
	gen.bind_method(plus_conv, 'RenderUninit', 'void', [])

	gen.bind_method(plus_conv, 'NewRenderWindow', 'gs::RenderWindow', ['int width', 'int height', '?gs::Window::Visibility visibility'])
	gen.bind_method(plus_conv, 'FreeRenderWindow', 'void', ['gs::RenderWindow &window'])

	gen.bind_method(plus_conv, 'GetRenderWindow', 'gs::RenderWindow', [])
	gen.bind_method_overloads(plus_conv, 'SetRenderWindow', [
		('void', ['gs::RenderWindow &window'], {'exception': 'check your program for a missing ImGuiUnlock call'}),
		('void', [], {'exception': 'check your program for a missing ImGuiUnlock call'})
	])

	gen.bind_method(plus_conv, 'GetRenderWindowSize', 'gs::tVector2<int>', ['const gs::RenderWindow &window'])
	gen.bind_method(plus_conv, 'UpdateRenderWindow', 'void', ['const gs::RenderWindow &window'])

	gen.bind_method(plus_conv, 'InitExtern', 'void', ['std::shared_ptr<gs::gpu::Renderer> renderer', 'std::shared_ptr<gs::gpu::RendererAsync> renderer_async', 'std::shared_ptr<gs::render::RenderSystem> render_system', 'std::shared_ptr<gs::render::RenderSystemAsync> render_system_async'])
	gen.bind_method(plus_conv, 'UninitExtern', 'void', [])

	gen.bind_method(plus_conv, 'Set2DOriginIsTopLeft', 'void', ['bool top_left'])

	gen.bind_method(plus_conv, 'Commit2D', 'void', [])
	gen.bind_method(plus_conv, 'Commit3D', 'void', [])

	gen.bind_method(plus_conv, 'GetScreenWidth', 'int', [])
	gen.bind_method(plus_conv, 'GetScreenHeight', 'int', [])

	gen.bind_method(plus_conv, 'Flip', 'void', [])

	gen.bind_method(plus_conv, 'EndFrame', 'void', [])

	gen.bind_method(plus_conv, 'SetBlend2D', 'void', ['gs::render::BlendMode mode'])
	gen.bind_method(plus_conv, 'GetBlend2D', 'gs::render::BlendMode', [])
	gen.bind_method(plus_conv, 'SetCulling2D', 'void', ['gs::render::CullMode mode'])
	gen.bind_method(plus_conv, 'GetCulling2D', 'gs::render::CullMode', [])

	gen.bind_method(plus_conv, 'SetBlend3D', 'void', ['gs::render::BlendMode mode'])
	gen.bind_method(plus_conv, 'GetBlend3D', 'gs::render::BlendMode', [])
	gen.bind_method(plus_conv, 'SetCulling3D', 'void', ['gs::render::CullMode mode'])
	gen.bind_method(plus_conv, 'GetCulling3D', 'gs::render::CullMode', [])

	gen.bind_method(plus_conv, 'SetDepthTest2D', 'void', ['bool enable'])
	gen.bind_method(plus_conv, 'GetDepthTest2D', 'bool', [])
	gen.bind_method(plus_conv, 'SetDepthWrite2D', 'void', ['bool enable'])
	gen.bind_method(plus_conv, 'GetDepthWrite2D', 'bool', [])

	gen.bind_method(plus_conv, 'SetDepthTest3D', 'void', ['bool enable'])
	gen.bind_method(plus_conv, 'GetDepthTest3D', 'bool', [])
	gen.bind_method(plus_conv, 'SetDepthWrite3D', 'void', ['bool enable'])
	gen.bind_method(plus_conv, 'GetDepthWrite3D', 'bool', [])

	gen.bind_method_overloads(plus_conv, 'Clear', [
		('void', [], []),
		('void', ['gs::Color color'], [])
	])

	gen.bind_method_overloads(plus_conv, 'Plot2D', [
		('void', ['float x', 'float y'], []),
		('void', ['float x', 'float y', 'gs::Color color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Line2D', [
		('void', ['float sx', 'float sy', 'float ex', 'float ey'], []),
		('void', ['float sx', 'float sy', 'float ex', 'float ey', 'gs::Color start_color', 'gs::Color end_color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Triangle2D', [
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy'], []),
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'gs::Color a_color', 'gs::Color b_color', 'gs::Color c_color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Quad2D', [
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'float dx', 'float dy'], []),
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'float dx', 'float dy', 'gs::Color a_color', 'gs::Color b_color', 'gs::Color c_color', 'gs::Color d_color'], []),
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'float dx', 'float dy', 'gs::Color a_color', 'gs::Color b_color', 'gs::Color c_color', 'gs::Color d_color', 'std::shared_ptr<gs::gpu::Texture> texture'], []),
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'float dx', 'float dy', 'gs::Color a_color', 'gs::Color b_color', 'gs::Color c_color', 'gs::Color d_color', 'std::shared_ptr<gs::gpu::Texture> texture', 'float uv_sx', 'float uv_sy', 'float uv_ex', 'float uv_ey'], [])
	])

	gen.bind_method_overloads(plus_conv, 'Line3D', [
		('void', ['float sx', 'float sy', 'float sz', 'float ex', 'float ey', 'float ez'], []),
		('void', ['float sx', 'float sy', 'float sz', 'float ex', 'float ey', 'float ez', 'gs::Color start_color', 'gs::Color end_color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Triangle3D', [
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz'], []),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'gs::Color a_color', 'gs::Color b_color', 'gs::Color c_color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Quad3D', [
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz'], []),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'gs::Color a_color', 'gs::Color b_color', 'gs::Color c_color', 'gs::Color d_color'], []),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'gs::Color a_color', 'gs::Color b_color', 'gs::Color c_color', 'gs::Color d_color', 'std::shared_ptr<gs::gpu::Texture> texture'], []),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'gs::Color a_color', 'gs::Color b_color', 'gs::Color c_color', 'gs::Color d_color', 'std::shared_ptr<gs::gpu::Texture> texture', 'float uv_sx', 'float uv_sy', 'float uv_ex', 'float uv_ey'], [])
	])

	gen.bind_method(plus_conv, 'SetFont', 'void', ['const char *path'])
	gen.bind_method(plus_conv, 'GetFont', 'const char *', [])

	gen.bind_method_overloads(plus_conv, 'Text2D', [
		('void', ['float x', 'float y', 'const char *text'], []),
		('void', ['float x', 'float y', 'const char *text', 'float size'], []),
		('void', ['float x', 'float y', 'const char *text', 'float size', 'gs::Color color'], []),
		('void', ['float x', 'float y', 'const char *text', 'float size', 'gs::Color color', 'const char *font_path'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Text3D', [
		('void', ['float x', 'float y', 'float z', 'const char *text'], []),
		('void', ['float x', 'float y', 'float z', 'const char *text', 'float size'], []),
		('void', ['float x', 'float y', 'float z', 'const char *text', 'float size', 'gs::Color color'], []),
		('void', ['float x', 'float y', 'float z', 'const char *text', 'float size', 'gs::Color color', 'const char *font_path'], [])
	])

	gen.bind_method_overloads(plus_conv, 'Sprite2D', [
		('void', ['float x', 'float y', 'float size', 'const char *image_path'], []),
		('void', ['float x', 'float y', 'float size', 'const char *image_path', 'gs::Color tint'], []),
		('void', ['float x', 'float y', 'float size', 'const char *image_path', 'gs::Color tint', 'float pivot_x', 'float pivot_y'], []),
		('void', ['float x', 'float y', 'float size', 'const char *image_path', 'gs::Color tint', 'float pivot_x', 'float pivot_y', 'bool flip_h', 'bool flip_v'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Image2D', [
		('void', ['float x', 'float y', 'float scale', 'const char *image_path'], []),
		('void', ['float x', 'float y', 'float scale', 'const char *image_path', 'gs::Color tint'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Blit2D', [
		('void', ['float src_x', 'float src_y', 'float src_w', 'float src_h', 'float dst_x', 'float dst_y', 'float dst_w', 'float dst_h', 'const char *image_path'], []),
		('void', ['float src_x', 'float src_y', 'float src_w', 'float src_h', 'float dst_x', 'float dst_y', 'float dst_w', 'float dst_h', 'const char *image_path', 'gs::Color tint'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Texture2D', [
		('void', ['float x', 'float y', 'float scale', 'const std::shared_ptr<gs::gpu::Texture> &texture'], []),
		('void', ['float x', 'float y', 'float scale', 'const std::shared_ptr<gs::gpu::Texture> &texture', 'gs::Color tint'], []),
		('void', ['float x', 'float y', 'float scale', 'const std::shared_ptr<gs::gpu::Texture> &texture', 'gs::Color tint', 'float flip_h', 'float flip_v'], [])
	])

	gen.bind_method(plus_conv, 'LoadTexture', 'std::shared_ptr<gs::gpu::Texture>', ['const char *path'])
	gen.bind_method(plus_conv, 'LoadMaterial', 'std::shared_ptr<gs::render::Material>', ['const char *path'])
	gen.bind_method(plus_conv, 'LoadGeometry', 'std::shared_ptr<gs::render::Geometry>', ['const char *path'])
	gen.bind_method_overloads(plus_conv, 'CreateGeometry', [
		('std::shared_ptr<gs::render::Geometry>', ['const std::shared_ptr<gs::core::Geometry> &geometry'], []),
		('std::shared_ptr<gs::render::Geometry>', ['const std::shared_ptr<gs::core::Geometry> &geometry', 'bool use_cache'], [])
	])

	gen.bind_method_overloads(plus_conv, 'Geometry2D', [
		('void', ['float x', 'float y', 'const std::shared_ptr<gs::render::Geometry> &geometry'], []),
		('void', ['float x', 'float y', 'const std::shared_ptr<gs::render::Geometry> &geometry', 'float angle_x', 'float angle_y', 'float angle_z'], []),
		('void', ['float x', 'float y', 'const std::shared_ptr<gs::render::Geometry> &geometry', 'float angle_x', 'float angle_y', 'float angle_z', 'float scale'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Geometry3D', [
		('void', ['float x', 'float y', 'float z', 'const std::shared_ptr<gs::render::Geometry> &geometry'], []),
		('void', ['float x', 'float y', 'float z',  'const std::shared_ptr<gs::render::Geometry> &geometry', 'float angle_x', 'float angle_y', 'float angle_z'], []),
		('void', ['float x', 'float y', 'float z',  'const std::shared_ptr<gs::render::Geometry> &geometry', 'float angle_x', 'float angle_y', 'float angle_z', 'float scale'], [])
	])

	gen.bind_method_overloads(plus_conv, 'SetCamera3D', [
		('void', ['float x', 'float y', 'float z'], []),
		('void', ['float x', 'float y', 'float z', 'float angle_x', 'float angle_y', 'float angle_z'], []),
		('void', ['float x', 'float y', 'float z', 'float angle_x', 'float angle_y', 'float angle_z', 'float fov'], []),
		('void', ['float x', 'float y', 'float z', 'float angle_x', 'float angle_y', 'float angle_z', 'float fov', 'float z_near', 'float z_far'], []),
		('void', ['const gs::Matrix4 &view', 'const gs::Matrix44 &projection'], [])
	])
	gen.bind_method(plus_conv, 'GetCamera3DMatrix', 'gs::Matrix4', [])
	gen.bind_method(plus_conv, 'GetCamera3DProjectionMatrix', 'gs::Matrix44', [])

	gen.bind_method_overloads(plus_conv, 'CreateCapsule', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreateCone', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreateCube', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float height', 'float length'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float height', 'float length', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float height', 'float length', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreateCylinder', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreatePlane', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float length'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float length', 'int subdiv'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float length', 'int subdiv', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float width', 'float length', 'int subdiv', 'const char *material_path', 'const char *name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreateSphere', [
		('std::shared_ptr<gs::core::Geometry>', [], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y', 'const char *material_path'], []),
		('std::shared_ptr<gs::core::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y', 'const char *material_path', 'const char *name'], [])
	])
	#core::sGeometry CreateGeometryFromHeightmap(uint width, uint height, const std::vector<float> &heightmap, float scale = 1, const char *_material_path = nullptr, const char *_name = nullptr);

	gen.bind_method(plus_conv, 'NewScene', 'std::shared_ptr<gs::core::Scene>', ['?bool use_physics', '?bool use_lua'], [])
	gen.bind_method(plus_conv, 'UpdateScene', 'void', ['gs::core::Scene &scene', '?gs::time_ns dt'], [])
	gen.bind_method(plus_conv, 'AddDummy', 'std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', '?gs::Matrix4 world'], [])
	gen.bind_method(plus_conv, 'AddCamera', 'std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', '?gs::Matrix4 matrix', '?bool orthographic', '?bool set_as_current'], [])
	gen.bind_method(plus_conv, 'AddLight', 'std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', '?gs::Matrix4 matrix', '?gs::core::Light::Model model', '?float range', '?bool shadow', '?gs::Color diffuse', '?gs::Color specular'], [])
	gen.bind_method(plus_conv, 'AddObject', 'std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'std::shared_ptr<gs::render::Geometry> geometry', '?gs::Matrix4 matrix', '?bool is_static'], [])
	gen.bind_method(plus_conv, 'AddGeometry', 'std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'const char *geometry_path', '?gs::Matrix4 matrix'], [])
	gen.bind_method_overloads(plus_conv, 'AddPlane', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', '?gs::Matrix4 matrix'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float size_x', 'float size_z', '?const char *material_path', '?bool use_geometry_cache'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddCube', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', '?gs::Matrix4 matrix'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float size_x', 'float size_z', 'float size_z', '?const char *material_path', '?bool use_geometry_cache'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddSphere', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', '?gs::Matrix4 matrix', '?float radius'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float radius', 'int subdiv_x', 'int subdiv_y', '?const char *material_path', '?bool use_geometry_cache'], [])
	])

	gen.bind_method_overloads(plus_conv, 'AddEnvironment', [
		('std::shared_ptr<gs::core::Environment>', ['gs::core::Scene &scene'], []),
		('std::shared_ptr<gs::core::Environment>', ['gs::core::Scene &scene', 'gs::Color background_color', 'gs::Color ambient_color'], []),
		('std::shared_ptr<gs::core::Environment>', ['gs::core::Scene &scene', 'gs::Color background_color', 'gs::Color ambient_color', 'gs::Color fog_color', 'float fog_near', 'float fog_far'], [])
	])

	gen.bind_method_overloads(plus_conv, 'AddPhysicCube', [
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float width', 'float height', 'float depth', '?float mass', '?const char *material_path'], {'arg_out': ['rigid_body']})
	])
	gen.bind_method_overloads(plus_conv, 'AddPhysicPlane', [
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float width', 'float length', '?float mass', '?const char *material_path'], {'arg_out': ['rigid_body']})
	])
	gen.bind_method_overloads(plus_conv, 'AddPhysicSphere', [
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float radius', 'int subdiv_x', 'int subdiv_y', '?float mass', '?const char *material_path'], {'arg_out': ['rigid_body']})
	])

	#
	gen.bind_method(plus_conv, 'GetMouse', 'std::shared_ptr<gs::InputDevice>', [])
	gen.bind_method(plus_conv, 'GetKeyboard', 'std::shared_ptr<gs::InputDevice>', [])

	gen.bind_method(plus_conv, 'GetMousePos', 'void', ['float &x', 'float &y'], {'arg_out': ['x', 'y']})
	gen.bind_method(plus_conv, 'GetMouseDt', 'void', ['float &x', 'float &y'], {'arg_out': ['x', 'y']})

	gen.bind_method_overloads(plus_conv, 'MouseButtonDown', [
		('bool', [], []),
		('bool', ['gs::InputDevice::ButtonCode button'], [])
	])
	gen.bind_method(plus_conv, 'KeyDown', 'bool', ['gs::InputDevice::KeyCode key'])
	gen.bind_method(plus_conv, 'KeyPress', 'bool', ['gs::InputDevice::KeyCode key'])
	gen.bind_method(plus_conv, 'KeyReleased', 'bool', ['gs::InputDevice::KeyCode key'])

	#
	gen.bind_method(plus_conv, 'ResetClock', 'void', [])
	gen.bind_method(plus_conv, 'UpdateClock', 'gs::time_ns', [])

	gen.bind_method(plus_conv, 'GetClockDt', 'gs::time_ns', [])
	gen.bind_method(plus_conv, 'GetClock', 'gs::time_ns', [])

	gen.end_class(plus_conv)

	gen.insert_binding_code('gs::Plus &GetPlus() { return gs::g_plus.get(); }')
	gen.bind_function('GetPlus', 'gs::Plus &', [])

	# gs::FPSController
	fps_controller = gen.begin_class('gs::FPSController')

	gen.bind_constructor_overloads(fps_controller, [
		([], []),
		(['float x', 'float y', 'float z'], []),
		(['float x', 'float y', 'float z', 'float speed', 'float turbo'], [])
	])

	gen.bind_method(fps_controller, 'Reset', 'void', ['gs::Vector3 position', 'gs::Vector3 rotation'])

	gen.bind_method(fps_controller, 'SetSmoothFactor', 'void', ['float k_pos', 'float k_rot'])

	gen.bind_method(fps_controller, 'ApplyToNode', 'void', ['gs::core::Node &node'])

	gen.bind_method(fps_controller, 'Update', 'void', ['gs::time_ns dt'])
	gen.bind_method(fps_controller, 'UpdateAndApplyToNode', 'void', ['gs::core::Node &node', 'gs::time_ns dt'])

	gen.bind_method(fps_controller, 'GetPos', 'gs::Vector3', [])
	gen.bind_method(fps_controller, 'GetRot', 'gs::Vector3', [])
	gen.bind_method(fps_controller, 'SetPos', 'void', ['const gs::Vector3 &position'])
	gen.bind_method(fps_controller, 'SetRot', 'void', ['const gs::Vector3 &rotation'])

	gen.bind_method(fps_controller, 'GetSpeed', 'float', [])
	gen.bind_method(fps_controller, 'SetSpeed', 'void', ['float speed'])
	gen.bind_method(fps_controller, 'GetTurbo', 'float', [])
	gen.bind_method(fps_controller, 'SetTurbo', 'void', ['float turbo'])

	gen.end_class(fps_controller)


def bind_filesystem(gen):
	gen.add_include('foundation/filesystem.h')
	gen.add_include('foundation/io_cfile.h')
	gen.add_include('foundation/io_handle.h')
	gen.add_include('foundation/io_mode.h')

	gen.bind_named_enum('gs::SeekRef', ['SeekStart', 'SeekCurrent', 'SeekEnd'])
	gen.bind_named_enum('gs::io::Mode', ['ModeRead', 'ModeWrite'], bound_name='IOMode', prefix='IO')
	gen.bind_named_enum('gs::io::DriverCaps::Type', ['IsCaseSensitive', 'CanRead', 'CanWrite', 'CanSeek', 'CanDelete', 'CanMkDir'], bound_name='IODriverCaps', namespace='gs::io::DriverCaps', prefix='IODriver')

	# forward declarations
	io_driver = gen.begin_class('gs::io::Driver', bound_name='IODriver_nobind', noncopyable=True, nobind=True)
	gen.end_class(io_driver)

	shared_io_driver = gen.begin_class('std::shared_ptr<gs::io::Driver>', bound_name='IODriver', features={'proxy': lib.stl.SharedPtrProxyFeature(io_driver)})

	# binding specific API
	gen.insert_binding_code('''static bool MountFileDriver(gs::io::sDriver driver) {
	return gs::g_fs.get().Mount(driver);
}
static bool MountFileDriver(gs::io::sDriver driver, const char *prefix) {
	return gs::g_fs.get().Mount(driver, prefix);
}
	''', 'Filesystem custom API')

	# gs::io::Handle
	handle = gen.begin_class('gs::io::Handle', noncopyable=True)

	gen.bind_method(handle, 'GetSize', 'size_t', [])

	gen.bind_method(handle, 'Rewind', 'size_t', [])
	gen.bind_method(handle, 'IsEOF', 'bool', [])

	gen.bind_method(handle, 'Tell', 'size_t', [])
	gen.bind_method(handle, 'Seek', 'size_t', ['int offset', 'gs::SeekRef ref'])

	# Read
	gen.insert_binding_code('static size_t IOHandle_WriteBinaryBlob(gs::io::Handle *handle, gs::BinaryBlob &data) { return handle->Write(data.GetData(), data.GetDataSize()); }')
	gen.bind_method(handle, 'Write', 'size_t', ['gs::BinaryBlob &data'], {'route': lambda args: 'IOHandle_WriteBinaryBlob(%s);' % (', '.join(args))})

	gen.bind_method(handle, 'GetDriver', 'std::shared_ptr<gs::io::Driver>', [])

	gen.end_class(handle)

	# gs::io::Driver
	gen.bind_method(shared_io_driver, 'FileHash', 'std::string', ['const char *path'], ['proxy'])

	gen.bind_method(shared_io_driver, 'MapToAbsolute', 'std::string', ['std::string path'], ['proxy'])
	gen.bind_method(shared_io_driver, 'MapToRelative', 'std::string', ['std::string path'], ['proxy'])

	gen.bind_method(shared_io_driver, 'GetCaps', 'gs::io::DriverCaps::Type', [], ['proxy'])

	gen.bind_method(shared_io_driver, 'Open', 'gs::io::Handle *', ['const char *path', 'gs::io::Mode mode'], ['proxy', 'new_obj'])
	gen.bind_method(shared_io_driver, 'Close', 'void', ['gs::io::Handle &handle'], ['proxy'])

	gen.bind_method(shared_io_driver, 'Delete', 'bool', ['const char *path'], ['proxy'])

	gen.bind_method(shared_io_driver, 'Tell', 'size_t', ['gs::io::Handle &handle'], ['proxy'])
	gen.bind_method(shared_io_driver, 'Seek', 'size_t', ['gs::io::Handle &handle', 'int offset', 'gs::SeekRef ref'], ['proxy'])
	gen.bind_method(shared_io_driver, 'Size', 'size_t', ['gs::io::Handle &handle'], ['proxy'])

	gen.bind_method(shared_io_driver, 'IsEOF', 'bool', ['gs::io::Handle &handle'], ['proxy'])

	#virtual size_t Read(Handle &h, void *buffer_out, size_t size) = 0;
	#virtual size_t Write(Handle &h, const void *buffer_in, size_t size) = 0;

	#virtual std::vector<DirEntry> Dir(const char *path, const char *wildcard = "*.*", DirEntry::Type filter = DirEntry::All);

	gen.bind_method(shared_io_driver, 'MkDir', 'bool', ['const char *path'], ['proxy'])
	gen.bind_method(shared_io_driver, 'IsDir', 'bool', ['const char *path'], ['proxy'])

	gen.end_class(shared_io_driver)

	# gs::io::CFile
	io_cfile = gen.begin_class('gs::io::CFile', bound_name='CFile_nobind', nobind=True)
	gen.end_class(io_cfile)

	shared_io_cfile = gen.begin_class('std::shared_ptr<gs::io::CFile>', bound_name='StdFileDriver', features={'proxy': lib.stl.SharedPtrProxyFeature(io_cfile)})
	gen.add_base(shared_io_cfile, shared_io_driver)

	gen.bind_constructor_overloads(shared_io_cfile, [
		([], ['proxy']),
		(['const std::string &root_path'], ['proxy']),
		(['const std::string &root_path', 'bool sandbox'], ['proxy'])
	])
	gen.bind_method_overloads(shared_io_cfile, 'SetRootPath', [
		('void', ['const std::string &path'], ['proxy']),
		('void', ['const std::string &path', 'bool sandbox'], ['proxy'])
	])

	gen.end_class(shared_io_cfile)

	gen.bind_function_overloads('MountFileDriver', [
		('bool', ['std::shared_ptr<gs::io::Driver> driver'], []),
		('bool', ['std::shared_ptr<gs::io::Driver> driver', 'const char *prefix'], [])
	])

	# gs::io::Zip
	gen.add_include('engine/io_zip.h')

	io_zip = gen.begin_class('gs::io::Zip', bound_name='Zip_nobind', noncopyable=True, nobind=True)
	gen.end_class(io_zip)

	shared_io_zip = gen.begin_class('std::shared_ptr<gs::io::Zip>', bound_name='ZipFileDriver', features={'proxy': lib.stl.SharedPtrProxyFeature(io_zip)})
	gen.add_base(shared_io_zip, shared_io_driver)

	"""
	gen.bind_constructor_overloads(shared_io_cfile, [
		(['std::shared_ptr<gs::io::Handle> archive'], ['proxy']),
		(['std::shared_ptr<gs::io::Handle> archive', 'const char *password'], ['proxy'])
	])
	gen.bind_method_overloads(shared_io_cfile, 'SetArchive', [
		('bool', ['std::shared_ptr<gs::io::Handle> archive'], ['proxy']),
		('bool', ['std::shared_ptr<gs::io::Handle> archive', 'const char *password'], ['proxy'])
	])
	"""

	gen.end_class(shared_io_zip)

	# gs::io::Filesystem
	fs = gen.begin_class('gs::io::Filesystem')

	gen.bind_method_overloads(fs, 'Mount', [
		('bool', ['std::shared_ptr<gs::io::Driver> driver'], []),
		('bool', ['std::shared_ptr<gs::io::Driver> driver', 'const char *prefix'], [])
	])
	gen.bind_method(fs, 'IsPrefixMounted', 'bool', ['const char *prefix'])

	gen.bind_method_overloads(fs, 'Unmount', [
		('void', ['const char *prefix'], []),
		('void', ['const std::shared_ptr<gs::io::Driver> &driver'], [])
	])
	gen.bind_method(fs, 'UnmountAll', 'void', [])

	gen.bind_method(fs, 'MapToAbsolute', 'std::string', ['const char *path'])
	gen.bind_method(fs, 'MapToRelative', 'std::string', ['const char *path'])
	gen.bind_method(fs, 'StripPrefix', 'std::string', ['const char *path'])

	gen.bind_method(fs, 'Open', 'gs::io::Handle *', ['const char *path', 'gs::io::Mode mode'], ['new_obj'])
	gen.bind_method(fs, 'Close', 'void', ['gs::io::Handle &handle'])

	gen.bind_method(fs, 'MkDir', 'bool', ['const char *path'])

	gen.bind_method(fs, 'Exists', 'bool', ['const char *path'])
	gen.bind_method(fs, 'Delete', 'bool', ['const char *path'])

	gen.bind_method(fs, 'FileSize', 'size_t', ['const char *path'])
	#gen.bind_method(fs, 'FileLoad', 'size_t', ['const char *path'])
	#gen.bind_method(fs, 'FileSave', 'size_t', ['const char *path'])
	gen.bind_method(fs, 'FileCopy', 'bool', ['const char *src', 'const char *dst'])
	gen.bind_method(fs, 'FileMove', 'bool', ['const char *src', 'const char *dst'])

	gen.bind_method(fs, 'FileToString', 'std::string', ['const char *path'])
	gen.bind_method(fs, 'StringToFile', 'bool', ['const char *path', 'const std::string &text'])

	gen.end_class(fs)

	#
	gen.insert_binding_code('static gs::io::Filesystem &GetFilesystem() { return gs::g_fs.get(); }')
	gen.bind_function('GetFilesystem', 'gs::io::Filesystem &', [])


def bind_color(gen):
	gen.add_include('foundation/color.h')
	gen.add_include('foundation/color_api.h')

	color = gen.begin_class('gs::Color')
	color._inline = True  # use inline alloc where possible

	gen.bind_static_members(color, ['const gs::Color Zero', 'const gs::Color One', 'const gs::Color White', 'const gs::Color Grey', 'const gs::Color Black', 'const gs::Color Red', 'const gs::Color Green', 'const gs::Color Blue', 'const gs::Color Yellow', 'const gs::Color Orange', 'const gs::Color Purple', 'const gs::Color Transparent'])
	gen.bind_members(color, ['float r', 'float g', 'float b', 'float a'])

	gen.bind_constructor_overloads(color, [
		([], []),
		(['const gs::Color &color'], []),
		(['float r', 'float g', 'float b'], []),
		(['float r', 'float g', 'float b', 'float a'], [])
	])

	gen.bind_arithmetic_ops_overloads(color, ['+', '-', '/', '*'], [('gs::Color', ['const gs::Color &color'], []), ('gs::Color', ['float k'], [])])
	gen.bind_inplace_arithmetic_ops_overloads(color, ['+=', '-=', '*=', '/='], [
		(['gs::Color &color'], []),
		(['float k'], [])
	])
	gen.bind_comparison_ops(color, ['==', '!='], ['const gs::Color &color'])

	gen.end_class(color)

	gen.bind_function('gs::ColorToGrayscale', 'float', ['const gs::Color &color'])

	gen.bind_function('gs::ColorToRGBA32', 'uint32_t', ['const gs::Color &color'])
	gen.bind_function('gs::ColorFromRGBA32', 'gs::Color', ['uint32_t rgba32'])

	gen.bind_function('gs::ARGB32ToRGBA32', 'uint32_t', ['uint32_t argb'])

	#inline float Dist2(const Color &i, const Color &j) { return (j.r - i.r) * (j.r - i.r) + (j.g - i.g) * (j.g - i.g) + (j.b - i.b) * (j.b - i.b) + (j.a - i.a) * (j.a - i.a); }
	#inline float Dist(const Color &i, const Color &j) { return math::Sqrt(Dist2(i, j)); }

	#inline bool AlmostEqual(const Color &a, const Color &b, float epsilon)

	gen.bind_function('gs::ChromaScale', 'gs::Color', ['const gs::Color &color', 'float k'])
	gen.bind_function('gs::AlphaScale', 'gs::Color', ['const gs::Color &color', 'float k'])

	#Color Clamp(const Color &c, float min, float max);
	#Color Clamp(const Color &c, const Color &min, const Color &max);
	#Color ClampMagnitude(const Color &c, float min, float max);

	gen.bind_function('gs::ColorFromVector3', 'gs::Color', ['const gs::Vector3 &v'])
	gen.bind_function('gs::ColorFromVector4', 'gs::Color', ['const gs::Vector4 &v'])

	bind_std_vector(gen, color)


def bind_font_engine(gen):
	gen.add_include('engine/font_engine.h')

	font_engine = gen.begin_class('gs::FontEngine', noncopyable=True)

	gen.bind_constructor(font_engine, [])
	gen.end_class(font_engine)


def bind_picture(gen):
	gen.add_include('engine/picture.h')

	gen.bind_named_enum('gs::Picture::Format', [
		'Gray8', 'Gray16', 'GrayF', 'RGB555', 'RGB565', 'RGB8', 'BGR8', 'RGBA8', 'BGRA8', 'ARGB8', 'ABGR8', 'RGB16', 'BGR16', 'RGBA16', 'BGRA16', 'ARGB16', 'ABGR16', 'RGBF', 'BGRF', 'RGBAF', 'BGRAF', 'ARGBF', 'ABGRF', 'InvalidFormat'
	], bound_name='PictureFormat', prefix='Picture')

	gen.bind_named_enum('gs::Picture::BrushMode', ['BrushNone', 'BrushSolid'])
	gen.bind_named_enum('gs::Picture::PenMode', ['PenNone', 'PenSolid'])
	gen.bind_named_enum('gs::Picture::PenCap', ['ButtCap', 'SquareCap', 'RoundCap'])
	gen.bind_named_enum('gs::Picture::LineJoin', ['MiterJoin', 'MiterJoinRevert', 'RoundJoin', 'BevelJoin', 'MiterJoinRound'])
	gen.bind_named_enum('gs::Picture::InnerJoin', ['InnerBevel', 'InnerMiter', 'InnerJag', 'InnerRound'])

	gen.bind_named_enum('gs::Picture::Filter', ['Nearest', 'Bilinear', 'Hanning', 'Hamming', 'Hermite', 'Quadric', 'Bicubic', 'Kaiser', 'Catrom', 'Mitchell', 'Spline16', 'Spline36', 'Gaussian', 'Bessel', 'Sinc36', 'Sinc64', 'Sinc256', 'Lanczos36', 'Lanczos64', 'Lanczos256', 'Blackman36', 'Blackman64', 'Blackman256'], bound_name='PictureFilter', prefix='Filter')

	# gs::Picture
	picture = gen.begin_class('gs::Picture', bound_name='Picture_nobind', nobind=True)
	gen.end_class(picture)

	shared_picture = gen.begin_class('std::shared_ptr<gs::Picture>', bound_name='Picture', features={'proxy': lib.stl.SharedPtrProxyFeature(picture)})

	gen.bind_constructor_overloads(shared_picture, [
		([], ['proxy']),
		(['const gs::Picture &picture'], ['proxy']),
		(['gs::uint width', 'gs::uint height', 'gs::Picture::Format format'], ['proxy'])
	])

	gen.bind_method(shared_picture, 'GetWidth', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_picture, 'GetHeight', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_picture, 'GetCenter', 'gs::tVector2<float>', [], ['proxy'])
	gen.bind_method(shared_picture, 'GetStride', 'size_t', [], ['proxy'])
	gen.bind_method(shared_picture, 'GetFormat', 'gs::Picture::Format', [], ['proxy'])

	gen.bind_method(shared_picture, 'GetRect', 'gs::Rect<int>', [], ['proxy'])

	gen.bind_method_overloads(shared_picture, 'AllocAs', [
		('bool', ['gs::uint width', 'gs::uint height', 'gs::Picture::Format format'], ['proxy']),
		('bool', ['const gs::Picture &picture'], ['proxy'])
	])
	gen.bind_method(shared_picture, 'Free', 'void', [], ['proxy'])

	#uint8_t *GetData() const { return (uint8_t *)data.data(); }
	#uint8_t *GetDataAt(int x, int y) const;
	gen.bind_method(shared_picture, 'GetDataSize', 'size_t', [], ['proxy'])

	gen.bind_method(shared_picture, 'ClearClipping', 'void', [], ['proxy'])
	gen.bind_method(shared_picture, 'SetClipping', 'void', ['int start_x', 'int start_y', 'int end_x', 'int end_y'], ['proxy'])

	gen.bind_method_overloads(shared_picture, 'ClearRGBA', [
		('void', ['float r', 'float g', 'float b'], ['proxy']),
		('void', ['float r', 'float g', 'float b', 'float a'], ['proxy'])
	])
	gen.bind_method(shared_picture, 'GetPixelRGBA', 'gs::Vector4', ['int x', 'int y'], ['proxy'])
	gen.bind_method_overloads(shared_picture, 'PutPixelRGBA', [
		('void', ['int x', 'int y', 'float r', 'float g', 'float b'], ['proxy']),
		('void', ['int x', 'int y', 'float r', 'float g', 'float b', 'float a'], ['proxy'])
	])
	gen.bind_method_overloads(shared_picture, 'BlendPixelRGBA', [
		('void', ['int x', 'int y', 'float r', 'float g', 'float b'], ['proxy']),
		('void', ['int x', 'int y', 'float r', 'float g', 'float b', 'float a'], ['proxy'])
	])

	gen.bind_method_overloads(shared_picture, 'SetFillColorRGBA', [
		('void', ['float r', 'float g', 'float b'], ['proxy']),
		('void', ['float r', 'float g', 'float b', 'float a'], ['proxy'])
	])
	gen.bind_method_overloads(shared_picture, 'SetPenColorRGBA', [
		('void', ['float r', 'float g', 'float b'], ['proxy']),
		('void', ['float r', 'float g', 'float b', 'float a'], ['proxy'])
	])

	gen.bind_method(shared_picture, 'BlitCopy', 'bool', ['const gs::Picture &src', 'gs::Rect<int> src_rect', 'gs::tVector2<int> dst_pos'], ['proxy'])
	gen.bind_method_overloads(shared_picture, 'Blit', [
		('bool', ['const gs::Picture &src', 'gs::Rect<int> src_rect', 'gs::tVector2<int> dst_pos'], ['proxy']),
		('bool', ['const gs::Picture &src', 'gs::Rect<int> src_rect', 'gs::Rect<int> dst_rect'], ['proxy']),
		('bool', ['const gs::Picture &src', 'gs::Rect<int> src_rect', 'gs::Rect<int> dst_rect', 'gs::Picture::Filter filter'], ['proxy'])
	])
	gen.bind_method_overloads(shared_picture, 'BlitTransform', [
		('bool', ['const gs::Picture &src', 'gs::Rect<int> dst_rect', 'const gs::Matrix3 &m'], ['proxy']),
		('bool', ['const gs::Picture &src', 'gs::Rect<int> dst_rect', 'const gs::Matrix3 &m', 'gs::Picture::Filter filter'], ['proxy'])
	])

	gen.bind_method(shared_picture, 'Flip', 'void', ['bool horizontal', 'bool vertical'], ['proxy'])
	gen.bind_method(shared_picture, 'Reframe', 'bool', ['int top', 'int bottom', 'int left', 'int right'], ['proxy'])
	gen.bind_method(shared_picture, 'Crop', 'bool', ['int start_x', 'int start_y', 'int end_x', 'int end_y'], ['proxy'])

	gen.bind_method_overloads(shared_picture, 'Resize', [
		('bool', ['gs::uint width', 'gs::uint height'], ['proxy']),
		('bool', ['gs::uint width', 'gs::uint height', 'gs::Picture::Filter filter'], ['proxy'])
	])

	gen.bind_method(shared_picture, 'Convert', 'bool', ['gs::Picture::Format format'], ['proxy'])

	gen.bind_method(shared_picture, 'SetFillMode', 'void', ['gs::Picture::BrushMode brush_mode'], ['proxy'])
	gen.bind_method(shared_picture, 'SetPenMode', 'void', ['gs::Picture::PenMode pen_mode'], ['proxy'])
	gen.bind_method(shared_picture, 'SetPenWidth', 'void', ['float width'], ['proxy'])
	gen.bind_method(shared_picture, 'SetPenCap', 'void', ['gs::Picture::PenCap cap'], ['proxy'])
	gen.bind_method(shared_picture, 'SetLineJoin', 'void', ['gs::Picture::LineJoin join'], ['proxy'])
	gen.bind_method(shared_picture, 'SetInnerJoin', 'void', ['gs::Picture::InnerJoin join'], ['proxy'])

	gen.bind_method(shared_picture, 'MoveTo', 'void', ['float x', 'float y'], ['proxy'])
	gen.bind_method(shared_picture, 'LineTo', 'void', ['float x', 'float y'], ['proxy'])
	gen.bind_method(shared_picture, 'ClosePolygon', 'void', [], ['proxy'])
	gen.bind_method(shared_picture, 'AddRoundedRect', 'void', ['float start_x', 'float start_y', 'float end_x', 'float end_y', 'float radius'], ['proxy'])
	gen.bind_method(shared_picture, 'AddEllipse', 'void', ['float x', 'float y', 'float radius_x', 'float radius_y'], ['proxy'])
	gen.bind_method(shared_picture, 'AddCircle', 'void', ['float x', 'float y', 'float radius'], ['proxy'])
	gen.bind_method(shared_picture, 'DrawPath', 'void', [], ['proxy'])

	gen.bind_method(shared_picture, 'DrawLine', 'void', ['float start_x', 'float start_y', 'float end_x', 'float end_y'], ['proxy'])
	gen.bind_method(shared_picture, 'DrawRect', 'void', ['float start_x', 'float start_y', 'float end_x', 'float end_y'], ['proxy'])
	gen.bind_method(shared_picture, 'DrawRoundedRect', 'void', ['float start_x', 'float start_y', 'float end_x', 'float end_y', 'float radius'], ['proxy'])
	gen.bind_method(shared_picture, 'DrawEllipse', 'void', ['float x', 'float y', 'float radius_x', 'float radius_y'], ['proxy'])
	gen.bind_method(shared_picture, 'DrawCircle', 'void', ['float x', 'float y', 'float radius'], ['proxy'])

	gen.bind_method(shared_picture, 'DrawGlyph', 'void', ['gs::FontEngine &font_engine', 'char32_t glyph_utf32', 'float x', 'float y'], ['proxy'])
	gen.bind_method(shared_picture, 'DrawText', 'void', ['gs::FontEngine &font_engine', 'const char *text', 'float x', 'float y'], ['proxy'])

	gen.bind_method_overloads(shared_picture, 'Compare', [
		('bool', ['const gs::Picture &picture'], ['proxy']),
		('bool', ['const gs::Picture &picture', 'float threshold'], ['proxy'])
	])

	gen.end_class(shared_picture)


def bind_document(gen):
	gen.add_include('foundation/document.h')

	gen.bind_named_enum('gs::DocumentFormat', ['DocumentFormatUnknown', 'DocumentFormatXML', 'DocumentFormatJSON', 'DocumentFormatBinary'])

	doc_reader = gen.begin_class('gs::IDocumentReader', noncopyable=True)
	gen.bind_method(doc_reader, 'GetScopeName', 'std::string', [])
	gen.bind_method(doc_reader, 'GetChildCount', 'gs::uint', ['?const char *name'])

	gen.bind_method(doc_reader, 'EnterScope', 'bool', ['const char *name'])
	gen.bind_method(doc_reader, 'EnterScopeMultiple', 'bool', ['const char *name'])
	gen.bind_method(doc_reader, 'ExitScopeMultiple', 'bool', ['gs::uint count'])

	gen.bind_method(doc_reader, 'EnterFirstChild', 'bool', [])
	gen.bind_method(doc_reader, 'EnterSibling', 'bool', [])
	gen.bind_method(doc_reader, 'ExitScope', 'bool', [])

	gen.bind_method(doc_reader, 'Read', 'bool', ['const char *name', 'bool &v'], {'arg_out': ['v']}, 'ReadBool')
	gen.bind_method(doc_reader, 'Read', 'bool', ['const char *name', 'char &v'], {'arg_out': ['v']}, 'ReadInt8')
	gen.bind_method(doc_reader, 'Read', 'bool', ['const char *name', 'uint8_t &v'], {'arg_out': ['v']}, 'ReadUInt8')
	gen.bind_method(doc_reader, 'Read', 'bool', ['const char *name', 'short &v'], {'arg_out': ['v']}, 'ReadInt16')
	gen.bind_method(doc_reader, 'Read', 'bool', ['const char *name', 'uint16_t &v'], {'arg_out': ['v']}, 'ReadUInt16')
	gen.bind_method(doc_reader, 'Read', 'bool', ['const char *name', 'int32_t &v'], {'arg_out': ['v']}, 'ReadInt32')
	gen.bind_method(doc_reader, 'Read', 'bool', ['const char *name', 'uint32_t &v'], {'arg_out': ['v']}, 'ReadUInt32')
	gen.bind_method(doc_reader, 'Read', 'bool', ['const char *name', 'float &v'], {'arg_out': ['v']}, 'ReadFloat')
	gen.bind_method(doc_reader, 'Read', 'bool', ['const char *name', 'std::string &v'], {'arg_out': ['v']}, 'ReadString')

	gen.bind_method(doc_reader, 'HasBinarySupport', 'bool', [])
	#virtual bool Read(const char *, BinaryBlob &) { return false; }

	gen.bind_method(doc_reader, 'Load', 'bool', ['const char *path'])
	gen.end_class(doc_reader)

	#
	doc_writer = gen.begin_class('gs::IDocumentWriter', noncopyable=True)

	gen.bind_method(doc_writer, 'EnterScope', 'bool', ['const char *name'])
	gen.bind_method(doc_writer, 'EnterScopeMultiple', 'bool', ['const char *name'])
	gen.bind_method(doc_writer, 'ExitScopeMultiple', 'bool', ['gs::uint count'])
	gen.bind_method(doc_writer, 'ExitScope', 'bool', [])

	gen.bind_method(doc_writer, 'Write', 'bool', ['const char *name', 'bool v'], [], 'WriteBool')
	gen.bind_method(doc_writer, 'Write', 'bool', ['const char *name', 'char v'], [], 'WriteInt8')
	gen.bind_method(doc_writer, 'Write', 'bool', ['const char *name', 'uint8_t v'], [], 'WriteUInt8')
	gen.bind_method(doc_writer, 'Write', 'bool', ['const char *name', 'short v'], [], 'WriteInt16')
	gen.bind_method(doc_writer, 'Write', 'bool', ['const char *name', 'uint16_t v'], [], 'WriteUInt16')
	gen.bind_method(doc_writer, 'Write', 'bool', ['const char *name', 'int32_t v'], [], 'WriteInt32')
	gen.bind_method(doc_writer, 'Write', 'bool', ['const char *name', 'uint32_t v'], [], 'WriteUInt32')
	gen.bind_method(doc_writer, 'Write', 'bool', ['const char *name', 'float v'], [], 'WriteFloat')
	gen.bind_method(doc_writer, 'Write', 'bool', ['const char *name', 'const char *v'], [], 'WriteString')

	gen.bind_method(doc_writer, 'HasBinarySupport', 'bool', [])
	#virtual bool Write(const char *, const BinaryBlob &) { return false; }

	gen.bind_method(doc_writer, 'Save', 'bool', ['const char *path'])
	gen.end_class(doc_writer)

	#
	gen.bind_function('gs::GetDocumentReadFormat', 'gs::DocumentFormat', ['const char *path'])
	gen.bind_function('gs::GetDocumentWriteFormat', 'gs::DocumentFormat', ['const char *path'])

	gen.bind_function('gs::GetDocumentFormatFromString', 'gs::DocumentFormat', ['const std::string &document'])


def bind_math(gen):
	gen.begin_class('gs::Vector3')
	gen.begin_class('gs::Vector4')
	gen.begin_class('gs::Matrix3')
	gen.begin_class('gs::Matrix4')
	gen.begin_class('gs::Matrix44')
	gen.begin_class('gs::Quaternion')

	# math
	gen.add_include('foundation/rect.h')
	gen.add_include('foundation/math.h')

	gen.bind_named_enum('gs::math::RotationOrder', [
		'RotationOrderZYX',
		'RotationOrderYZX',
		'RotationOrderZXY',
		'RotationOrderXZY',
		'RotationOrderYXZ',
		'RotationOrderXYZ',
		'RotationOrderXY',
		'RotationOrder_Default'
		], storage_type='uint8_t')

	gen.bind_named_enum('gs::math::Axis', ['AxisX', 'AxisY', 'AxisZ', 'AxisNone'], storage_type='uint8_t')

	gen.bind_function('gs::math::LinearInterpolate<float>', 'float', ['float y0', 'float y1', 'float t'])
	gen.bind_function('gs::math::CosineInterpolate<float>', 'float', ['float y0', 'float y1', 'float t'])
	gen.bind_function('gs::math::CubicInterpolate<float>', 'float', ['float y0', 'float y1', 'float y2', 'float y3', 'float t'])
	gen.bind_function('gs::math::HermiteInterpolate<float>', 'float', ['float y0', 'float y1', 'float y2', 'float y3', 'float t', 'float tension', 'float bias'])

	gen.bind_function('gs::math::ReverseRotationOrder', 'gs::math::RotationOrder', ['gs::math::RotationOrder rotation_order'])

	# gs::MinMax
	gen.add_include('foundation/minmax.h')

	minmax = gen.begin_class('gs::MinMax')

	gen.bind_members(minmax, ['gs::Vector3 mn', 'gs::Vector3 mx'])
	gen.bind_constructor_overloads(minmax, [
		([], []),
		(['const gs::Vector3 &min', 'const gs::Vector3 &max'], [])
	])
	gen.bind_method(minmax, 'GetArea', 'float', [])
	gen.bind_method(minmax, 'GetCenter', 'gs::Vector3', [])

	gen.bind_arithmetic_op(minmax, '*', 'gs::MinMax', ['const gs::Matrix4 &m'])
	gen.bind_comparison_ops(minmax, ['==', '!='], ['const gs::MinMax &minmax'])

	gen.end_class(minmax)

	#void GetMinMaxVertices(const MinMax &minmax, Vector3 out[8]);
	gen.bind_function('gs::ComputeMinMaxBoundingSphere', 'void', ['const gs::MinMax &minmax', 'gs::Vector3 &origin', 'float &radius'], {'arg_out': ['origin', 'radius']})

	gen.bind_function_overloads('gs::Overlap', [
		('bool', ['const gs::MinMax &minmax_a', 'const gs::MinMax &minmax_b'], []),
		('bool', ['const gs::MinMax &minmax_a', 'const gs::MinMax &minmax_b', 'gs::math::Axis axis'], [])
	])
	gen.bind_function('gs::Contains', 'bool', ['const gs::MinMax &minmax', 'const gs::Vector3 &position'])

	gen.bind_function_overloads('gs::Union', [
		('gs::MinMax', ['const gs::MinMax &minmax_a', 'const gs::MinMax &minmax_b'], []),
		('gs::MinMax', ['const gs::MinMax &minmax', 'const gs::Vector3 &position'], [])
	])

	gen.bind_function('gs::IntersectRay', 'bool', ['const gs::MinMax &minmax', 'const gs::Vector3 &origin', 'const gs::Vector3 &direction', 'float &t_min', 'float &t_max'], {'arg_out': ['t_min', 't_max']})

	gen.bind_function('gs::ClassifyLine', 'bool', ['const gs::MinMax &minmax', 'const gs::Vector3 &position', 'const gs::Vector3 &direction', 'gs::Vector3 &intersection', 'gs::Vector3 *normal'], {'arg_out': ['intersection', 'normal']})
	gen.bind_function('gs::ClassifySegment', 'bool', ['const gs::MinMax &minmax', 'const gs::Vector3 &p0', 'const gs::Vector3 &p1', 'gs::Vector3 &intersection', 'gs::Vector3 *normal'], {'arg_out': ['intersection', 'normal']})

	gen.bind_function('MinMaxFromPositionSize', 'gs::MinMax', ['const gs::Vector3 &position', 'const gs::Vector3 &size'])

	# gs::Vector2<T>
	gen.add_include('foundation/vector2.h')

	def bind_vector2_T(T, bound_name):
		vector2 = gen.begin_class('gs::tVector2<%s>'%T, bound_name=bound_name)
		gen.bind_static_members(vector2, ['const gs::tVector2<%s> Zero'%T, 'const gs::tVector2<%s> One'%T])

		gen.bind_members(vector2, ['%s x'%T, '%s y'%T])

		gen.bind_constructor_overloads(vector2, [
			([], []),
			(['%s x'%T, '%s y'%T], []),
			(['const gs::tVector2<%s> &v'%T], []),
			(['const gs::Vector3 &v'], []),
			(['const gs::Vector4 &v'], [])
		])

		gen.bind_arithmetic_ops_overloads(vector2, ['+', '-', '/'], [
			('gs::tVector2<%s>'%T, ['const gs::tVector2<%s> &v'%T], []),
			('gs::tVector2<%s>'%T, ['const %s k'%T], [])
		])
		gen.bind_arithmetic_op_overloads(vector2, '*', [
			('gs::tVector2<%s>'%T, ['const gs::tVector2<%s> &v'%T], []),
			('gs::tVector2<%s>'%T, ['const %s k'%T], []),
			('gs::tVector2<%s>'%T, ['const gs::Matrix3 &m'], [])
		])
		gen.bind_inplace_arithmetic_ops_overloads(vector2, ['+=', '-=', '*=', '/='], [
			(['const gs::tVector2<%s> &v'%T], []),
			(['const %s k'%T], [])
		])

		gen.bind_method(vector2, 'Min', 'gs::tVector2<%s>'%T, ['const gs::tVector2<%s> &v'%T])
		gen.bind_method(vector2, 'Max', 'gs::tVector2<%s>'%T, ['const gs::tVector2<%s> &v'%T])

		gen.bind_method(vector2, 'Len2', T, [])
		gen.bind_method(vector2, 'Len', T, [])

		gen.bind_method(vector2, 'Dot', T, ['const gs::tVector2<%s> &v'%T])

		gen.bind_method(vector2, 'Normalize', 'void', [])
		gen.bind_method(vector2, 'Normalized', 'gs::tVector2<%s>'%T, [])

		gen.bind_method(vector2, 'Reversed', 'gs::tVector2<%s>'%T, [])

		gen.bind_static_method(vector2, 'Dist2', T, ['const gs::tVector2<%s> &a'%T, 'const gs::tVector2<%s> &b'%T])
		gen.bind_static_method(vector2, 'Dist', T, ['const gs::tVector2<%s> &a'%T, 'const gs::tVector2<%s> &b'%T])

		gen.insert_binding_code('static void _Vector2_%s_Set(gs::tVector2<%s> *v, %s x, %s y) { v->x = x; v->y = y; }'%(T, T, T, T))
		gen.bind_method(vector2, 'Set', 'void', ['%s x'%T, '%s y'%T], {'route': route_lambda('_Vector2_%s_Set'%T)})

		gen.end_class(vector2)
		return vector2

	vector2 = bind_vector2_T('float', 'Vector2')
	ivector2 = bind_vector2_T('int', 'IntVector2')

	# gs::Vector4
	gen.add_include('foundation/vector4.h')

	vector4 = gen.begin_class('gs::Vector4')
	vector4._inline = True
	gen.bind_members(vector4, ['float x', 'float y', 'float z', 'float w'])

	gen.bind_constructor_overloads(vector4, [
		([], []),
		(['float x', 'float y', 'float z', 'float w'], []),
		(['const gs::tVector2<float> &v'], []),
		(['const gs::tVector2<int> &v'], []),
		(['const gs::Vector3 &v'], []),
		(['const gs::Vector4 &v'], [])
	])

	gen.bind_arithmetic_ops_overloads(vector4, ['+', '-', '/'], [
		('gs::Vector4', ['gs::Vector4 &v'], []),
		('gs::Vector4', ['float k'], [])
	])
	gen.bind_arithmetic_ops_overloads(vector4, ['*'], [
		('gs::Vector4', ['gs::Vector4 &v'], []),
		('gs::Vector4', ['float k'], []),
		('gs::Vector4', ['const gs::Matrix4 &m'], [])
	])

	gen.bind_inplace_arithmetic_ops_overloads(vector4, ['+=', '-=', '*=', '/='], [
		(['gs::Vector4 &v'], []),
		(['float k'], [])
	])

	gen.bind_method(vector4, 'Abs', 'gs::Vector4', [])

	gen.bind_method(vector4, 'Normalized', 'gs::Vector4', [])

	gen.insert_binding_code('static void _Vector4_Set(gs::Vector4 *v, float x, float y, float z, float w = 1.f) { v->x = x; v->y = y; v->z = z; v->w = w; }')
	gen.bind_method(vector4, 'Set', 'void', ['float x', 'float y', 'float z', '?float w'], {'route': route_lambda('_Vector4_Set')})

	gen.end_class(vector4)

	# gs::Quaternion
	gen.add_include('foundation/quaternion.h')

	quaternion = gen.begin_class('gs::Quaternion')

	gen.bind_members(quaternion, ['float x', 'float y', 'float z', 'float w'])

	gen.bind_constructor_overloads(quaternion, [
		([], []),
		(['float x', 'float y', 'float z', 'float w'], []),
		(['const gs::Quaternion &q'], [])
	])

	#gen.bind_comparison_ops(quaternion, ['==', '!='], ['const gs::Quaternion &q'])
	gen.bind_arithmetic_ops_overloads(quaternion, ['+', '-', '*'], [
		('gs::Quaternion', ['float v'], []),
		('gs::Quaternion', ['gs::Quaternion &q'], [])
	])
	gen.bind_arithmetic_op(quaternion, '/', 'gs::Quaternion', ['float v'])
	gen.bind_inplace_arithmetic_ops_overloads(quaternion, ['+=', '-=', '*='], [
		(['float v'], []),
		(['const gs::Quaternion &q'], [])
	])
	gen.bind_inplace_arithmetic_op(quaternion, '/=', ['float v'])

	gen.bind_method(quaternion, 'Inversed', 'gs::Quaternion', [])
	gen.bind_method(quaternion, 'Normalized', 'gs::Quaternion', [])
	gen.bind_method(quaternion, 'ToMatrix3', 'gs::Matrix3', [])
	gen.bind_method(quaternion, 'ToEuler', 'gs::Vector3', ['?gs::math::RotationOrder rotation_order'])

	gen.bind_static_method(quaternion, 'Distance', 'float', ['const gs::Quaternion &a', 'const gs::Quaternion &b'])
	gen.bind_static_method(quaternion, 'Slerp', 'gs::Quaternion', ['float t', 'const gs::Quaternion &a', 'const gs::Quaternion &b'])

	gen.bind_static_method(quaternion, 'FromEuler', 'gs::Quaternion', ['float x', 'float y', 'float z', '?gs::math::RotationOrder rotation_order'])
	gen.bind_static_method(quaternion, 'LookAt', 'gs::Quaternion', ['const gs::Vector3 &at'])
	gen.bind_static_method(quaternion, 'FromMatrix3', 'gs::Quaternion', ['const gs::Matrix3 &m'])
	gen.bind_static_method(quaternion, 'FromAxisAngle', 'gs::Quaternion', ['float angle', 'const gs::Vector3 &axis'])

	gen.end_class(quaternion)

	# gs::Matrix3
	gen.add_include('foundation/matrix3.h')

	matrix3 = gen.begin_class('gs::Matrix3')
	gen.bind_static_members(matrix3, ['const gs::Matrix3 Zero', 'const gs::Matrix3 Identity'])

	gen.bind_constructor_overloads(matrix3, [
		([], []),
		(['const gs::Matrix4 &m'], []),
		(['const gs::Vector3 &x', 'const gs::Vector3 &y', 'const gs::Vector3 &z'], [])
	])

	gen.bind_comparison_ops(matrix3, ['==', '!='], ['const gs::Matrix3 &m'])

	gen.bind_arithmetic_ops(matrix3, ['+', '-'], 'gs::Matrix3', ['gs::Matrix3 &m'])
	gen.bind_arithmetic_op_overloads(matrix3, '*', [
		('gs::Matrix3', ['const float v'], []),
		('gs::tVector2<float>', ['const gs::tVector2<float> &v'], []),
		('gs::Vector3', ['const gs::Vector3 &v'], []),
		('gs::Vector4', ['const gs::Vector4 &v'], []),
		('gs::Matrix3', ['const gs::Matrix3 &m'], [])
	])
	gen.bind_inplace_arithmetic_ops(matrix3, ['+=', '-='], ['const gs::Matrix3 &m'])
	gen.bind_inplace_arithmetic_op_overloads(matrix3, '*=', [
		(['const float k'], []),
		(['const gs::Matrix3 &m'], [])
	])

	gen.bind_method(matrix3, 'Det', 'float', [])
	gen.bind_method(matrix3, 'Inverse', 'bool', ['gs::Matrix3 &I'], {'arg_out': ['I']})

	gen.bind_method(matrix3, 'Transposed', 'gs::Matrix3', [])

	gen.bind_method(matrix3, 'GetRow', 'gs::Vector3', ['gs::uint n'])
	gen.bind_method(matrix3, 'GetColumn', 'gs::Vector3', ['gs::uint n'])
	gen.bind_method(matrix3, 'SetRow', 'void', ['gs::uint n', 'const gs::Vector3 &row'])
	gen.bind_method(matrix3, 'SetColumn', 'void', ['gs::uint n', 'const gs::Vector3 &column'])

	gen.bind_method(matrix3, 'GetX', 'gs::Vector3', [])
	gen.bind_method(matrix3, 'GetY', 'gs::Vector3', [])
	gen.bind_method(matrix3, 'GetZ', 'gs::Vector3', [])
	gen.bind_method(matrix3, 'GetTranslation', 'gs::Vector3', [])
	gen.bind_method(matrix3, 'GetScale', 'gs::Vector3', [])

	gen.bind_method(matrix3, 'SetX', 'void', ['const gs::Vector3 &X'])
	gen.bind_method(matrix3, 'SetY', 'void', ['const gs::Vector3 &Y'])
	gen.bind_method(matrix3, 'SetZ', 'void', ['const gs::Vector3 &Z'])
	gen.bind_method(matrix3, 'SetTranslation', 'void', ['const gs::Vector3 &T'])
	gen.bind_method(matrix3, 'SetScale', 'void', ['const gs::Vector3 &S'])

	gen.bind_method(matrix3, 'Set', 'void', ['const gs::Vector3 &X', 'const gs::Vector3 &Y', 'const gs::Vector3 &Z'])

	gen.bind_method(matrix3, 'Normalized', 'gs::Matrix3', [])
	gen.bind_method(matrix3, 'Orthonormalized', 'gs::Matrix3', [])
	gen.bind_method_overloads(matrix3, 'ToEuler', [
		('gs::Vector3', [], []),
		('gs::Vector3', ['gs::math::RotationOrder rotation_order'], [])
	])

	gen.bind_static_method(matrix3, 'VectorMatrix', 'gs::Matrix3', ['const gs::Vector3 &V'])
	gen.bind_static_method_overloads(matrix3, 'TranslationMatrix', [
		('gs::Matrix3', ['const gs::tVector2<float> &T'], []),
		('gs::Matrix3', ['const gs::Vector3 &T'], [])
	])
	gen.bind_static_method_overloads(matrix3, 'ScaleMatrix', [
		('gs::Matrix3', ['const gs::tVector2<float> &S'], []),
		('gs::Matrix3', ['const gs::Vector3 &S'], [])
	])
	gen.bind_static_method(matrix3, 'CrossProductMatrix', 'gs::Matrix3', ['const gs::Vector3 &V'])

	gen.bind_static_method(matrix3, 'RotationMatrixXAxis', 'gs::Matrix3', ['float angle'])
	gen.bind_static_method(matrix3, 'RotationMatrixYAxis', 'gs::Matrix3', ['float angle'])
	gen.bind_static_method(matrix3, 'RotationMatrixZAxis', 'gs::Matrix3', ['float angle'])

	gen.bind_static_method(matrix3, 'RotationMatrix2D', 'gs::Matrix3', ['float angle', 'const gs::tVector2<float> &pivot'])

	gen.bind_static_method_overloads(matrix3, 'FromEuler', [
		('gs::Matrix3', ['float x', 'float y', 'float z'], []),
		('gs::Matrix3', ['float x', 'float y', 'float z', 'gs::math::RotationOrder rotation_order'], []),
		('gs::Matrix3', ['const gs::Vector3 &euler'], []),
		('gs::Matrix3', ['const gs::Vector3 &euler', 'gs::math::RotationOrder rotation_order'], [])
	])

	gen.bind_static_method_overloads(matrix3, 'LookAt', [
		('gs::Matrix3', ['const gs::Vector3 &front'], []),
		('gs::Matrix3', ['const gs::Vector3 &front', 'const gs::Vector3 *up'], [])
	])

	gen.end_class(matrix3)

	gen.bind_function('gs::RotationMatrixXZY', 'gs::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('gs::RotationMatrixZYX', 'gs::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('gs::RotationMatrixXYZ', 'gs::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('gs::RotationMatrixZXY', 'gs::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('gs::RotationMatrixYZX', 'gs::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('gs::RotationMatrixYXZ', 'gs::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('gs::RotationMatrixXY', 'gs::Matrix3', ['float x', 'float y'])

	# gs::Matrix4
	gen.add_include('foundation/matrix4.h')

	matrix4 = gen.begin_class('gs::Matrix4')
	gen.bind_static_members(matrix4, ['const gs::Matrix4 Zero', 'const gs::Matrix4 Identity'])

	gen.bind_constructor_overloads(matrix4, [
		([], []),
		(['const gs::Matrix3 &m'], [])
	])

	gen.bind_comparison_ops(matrix4, ['==', '!='], ['const gs::Matrix4 &m'])

	gen.bind_arithmetic_ops(matrix4, ['+', '-'], 'gs::Matrix4', ['gs::Matrix4 &m'])
	gen.bind_arithmetic_op_overloads(matrix4, '*', [
		('gs::Matrix4', ['const float v'], []),
		('gs::Matrix4', ['const gs::Matrix4 &m'], []),
		('gs::Vector3', ['const gs::Vector3 &v'], []),
		('gs::Vector4', ['const gs::Vector4 &v'], [])
	])

	gen.bind_method(matrix4, 'GetRow', 'gs::Vector3', ['gs::uint n'])
	gen.bind_method(matrix4, 'GetColumn', 'gs::Vector4', ['gs::uint n'])
	gen.bind_method(matrix4, 'SetRow', 'void', ['gs::uint n', 'const gs::Vector3 &v'])
	gen.bind_method(matrix4, 'SetColumn', 'void', ['gs::uint n', 'const gs::Vector4 &v'])

	gen.bind_method(matrix4, 'GetX', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetY', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetZ', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetT', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetTranslation', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetRotation', 'gs::Vector3', ['?gs::math::RotationOrder rotation_order'])
	gen.bind_method(matrix4, 'GetRotationMatrix', 'gs::Matrix3', [])
	gen.bind_method(matrix4, 'GetScale', 'gs::Vector3', [])

	gen.bind_method(matrix4, 'SetX', 'void', ['const gs::Vector3 &X'])
	gen.bind_method(matrix4, 'SetY', 'void', ['const gs::Vector3 &Y'])
	gen.bind_method(matrix4, 'SetZ', 'void', ['const gs::Vector3 &Z'])
	gen.bind_method(matrix4, 'SetTranslation', 'void', ['const gs::Vector3 &T'])
	gen.bind_method(matrix4, 'SetScale', 'void', ['const gs::Vector3 &scale'])

	gen.bind_method(matrix4, 'Inverse', 'bool', ['gs::Matrix4 &out'])
	gen.bind_method(matrix4, 'InversedFast', 'gs::Matrix4', [])

	gen.bind_method(matrix4, 'Orthonormalized', 'gs::Matrix4', [])

	gen.bind_static_method_overloads(matrix4, 'LerpAsOrthonormalBase', [
		('gs::Matrix4', ['const gs::Matrix4 &from', 'const gs::Matrix4 &to', 'float k'], []),
		('gs::Matrix4', ['const gs::Matrix4 &from', 'const gs::Matrix4 &to', 'float k', 'bool fast'], [])
	])

	#void Decompose(Vector3 *position, Vector3 *scale = nullptr, Matrix3 *rotation = nullptr) const;
	gen.bind_method(matrix4, 'Decompose', 'void', ['gs::Vector3 *position', 'gs::Vector3 *scale', 'gs::Vector3 *rotation', '?gs::math::RotationOrder rotation_order'], {'arg_out': ['position', 'scale', 'rotation']})

	gen.bind_method_overloads(matrix4, 'LookAt', [
		('gs::Matrix4', ['const gs::Vector3 &at'], []),
		('gs::Matrix4', ['const gs::Vector3 &at', 'const gs::Vector3 *up'], [])
	])

	gen.bind_static_method(matrix4, 'TranslationMatrix', 'gs::Matrix4', ['const gs::Vector3 &t'])
	gen.bind_static_method_overloads(matrix4, 'RotationMatrix', [
		('gs::Matrix4', ['const gs::Vector3 &euler'], []),
		('gs::Matrix4', ['const gs::Vector3 &euler', 'gs::math::RotationOrder order'], [])
	])
	gen.bind_static_method(matrix4, 'ScaleMatrix', 'gs::Matrix4', ['const gs::Vector3 &scale'])
	gen.bind_static_method_overloads(matrix4, 'TransformationMatrix', [
		('gs::Matrix4', ['const gs::Vector3 &position', 'const gs::Vector3 &rotation'], []),
		('gs::Matrix4', ['const gs::Vector3 &euler', 'const gs::Vector3 &rotation', 'const gs::Vector3 &scale'], []),
		('gs::Matrix4', ['const gs::Vector3 &position', 'const gs::Matrix3 &rotation'], []),
		('gs::Matrix4', ['const gs::Vector3 &euler', 'const gs::Matrix3 &rotation', 'const gs::Vector3 &scale'], [])
	])
	gen.bind_static_method_overloads(matrix4, 'LookToward', [
		('gs::Matrix4', ['const gs::Vector3 &position', 'const gs::Vector3 &direction'], []),
		('gs::Matrix4', ['const gs::Vector3 &position', 'const gs::Vector3 &direction', 'const gs::Vector3 &scale'], []),
		('gs::Matrix4', ['const gs::Vector3 &position', 'const gs::Vector3 &direction', 'const gs::Vector3 &scale', 'const gs::Vector3 *up'], [])
	])

	gen.end_class(matrix4)

	# gs::Matrix44
	gen.add_include('foundation/matrix44.h')

	matrix44 = gen.begin_class('gs::Matrix44')
	gen.bind_static_members(matrix44, ['const gs::Matrix44 Zero', 'const gs::Matrix44 Identity'])
	gen.end_class(matrix44)

	# gs::Vector3
	gen.add_include('foundation/vector3.h')
	gen.add_include('foundation/vector3_api.h')

	vector3 = gen.begin_class('gs::Vector3')
	vector3._inline = True

	gen.bind_static_members(vector3, ['const gs::Vector3 Zero', 'const gs::Vector3 One', 'const gs::Vector3 Left', 'const gs::Vector3 Right', 'const gs::Vector3 Up', 'const gs::Vector3 Down', 'const gs::Vector3 Front', 'const gs::Vector3 Back'])
	gen.bind_members(vector3, ['float x', 'float y', 'float z'])

	gen.bind_constructor_overloads(vector3, [
		([], []),
		(['float x', 'float y', 'float z'], []),
		(['const gs::tVector2<float> &v'], []),
		(['const gs::tVector2<int> &v'], []),
		(['const gs::Vector3 &v'], []),
		(['const gs::Vector4 &v'], [])
	])

	gen.bind_function('gs::Vector3FromVector4', 'gs::Vector3', ['const gs::Vector4 &v'])

	gen.bind_arithmetic_ops_overloads(vector3, ['+', '-', '/'], [('gs::Vector3', ['gs::Vector3 &v'], []), ('gs::Vector3', ['float k'], [])])
	gen.bind_arithmetic_ops_overloads(vector3, ['*'], [('gs::Vector3', ['gs::Vector3 &v'], []), ('gs::Vector3', ['float k'], []), ('gs::Vector3', ['gs::Matrix3 m'], []), ('gs::Vector3', ['gs::Matrix4 m'], [])])

	gen.bind_inplace_arithmetic_ops_overloads(vector3, ['+=', '-=', '*=', '/='], [
		(['gs::Vector3 &v'], []),
		(['float k'], [])
	])
	gen.bind_comparison_ops(vector3, ['==', '!='], ['const gs::Vector3 &v'])

	gen.bind_function('gs::Dot', 'float', ['const gs::Vector3 &u', 'const gs::Vector3 &v'])
	gen.bind_function('gs::Cross', 'gs::Vector3', ['const gs::Vector3 &u', 'const gs::Vector3 &v'])

	gen.bind_method(vector3, 'Reverse', 'void', [])
	gen.bind_method(vector3, 'Inverse', 'void', [])
	gen.bind_method(vector3, 'Normalize', 'void', [])
	gen.bind_method(vector3, 'Normalized', 'gs::Vector3', [])
	gen.bind_method_overloads(vector3, 'Clamped', [('gs::Vector3', ['float min', 'float max'], []), ('gs::Vector3', ['const gs::Vector3 &min', 'const gs::Vector3 &max'], [])])
	gen.bind_method(vector3, 'ClampedMagnitude', 'gs::Vector3', ['float min', 'float max'])
	gen.bind_method(vector3, 'Reversed', 'gs::Vector3', [])
	gen.bind_method(vector3, 'Inversed', 'gs::Vector3', [])
	gen.bind_method(vector3, 'Abs', 'gs::Vector3', [])
	gen.bind_method(vector3, 'Sign', 'gs::Vector3', [])
	gen.bind_method(vector3, 'Maximum', 'gs::Vector3', ['const gs::Vector3 &left', 'const gs::Vector3 &right'])
	gen.bind_method(vector3, 'Minimum', 'gs::Vector3', ['const gs::Vector3 &left', 'const gs::Vector3 &right'])

	gen.bind_function('gs::Reflect', 'gs::Vector3', ['const gs::Vector3 &v', 'const gs::Vector3 &normal'])
	gen.bind_function_overloads('gs::Refract', [
		('gs::Vector3', ['const gs::Vector3 &v', 'const gs::Vector3 &normal'], []),
		('gs::Vector3', ['const gs::Vector3 &v', 'const gs::Vector3 &normal', 'float index_of_refraction_in', 'float index_of_refraction_out'], [])
	])

	gen.bind_method(vector3, 'Len2', 'float', [])
	gen.bind_method(vector3, 'Len', 'float', [])
	gen.bind_method(vector3, 'Floor', 'gs::Vector3', [])
	gen.bind_method(vector3, 'Ceil', 'gs::Vector3', [])

	gen.insert_binding_code('static void _Vector3_Set(gs::Vector3 *v, float x, float y, float z) { v->x = x; v->y = y; v->z = z; }')
	gen.bind_method(vector3, 'Set', 'void', ['float x', 'float y', 'float z'], {'route': route_lambda('_Vector3_Set')})

	gen.end_class(vector3)

	# gs::Rect<T>
	def bind_rect_T(T, bound_name):
		rect = gen.begin_class('gs::Rect<%s>'%T, bound_name=bound_name)
		rect._inline = True

		gen.bind_members(rect, ['%s sx'%T, '%s sy'%T, '%s ex'%T, '%s ey'%T])

		gen.bind_constructor_overloads(rect, [
			([], []),
			(['%s usx'%T, '%s usy'%T], []),
			(['%s usx'%T, '%s usy'%T, '%s uex'%T, '%s uey'%T], []),
			(['const gs::Rect<%s> &rect'%T], [])
		])

		gen.bind_method(rect, 'GetX', T, [])
		gen.bind_method(rect, 'GetY', T, [])
		gen.bind_method(rect, 'SetX', 'void', ['%s x'%T])
		gen.bind_method(rect, 'SetY', 'void', ['%s y'%T])

		gen.bind_method(rect, 'GetWidth', T, [])
		gen.bind_method(rect, 'GetHeight', T, [])
		gen.bind_method(rect, 'SetWidth', 'void', ['%s width'%T])
		gen.bind_method(rect, 'SetHeight', 'void', ['%s height'%T])

		gen.bind_method(rect, 'GetSize', 'gs::tVector2<%s>'%T, [])

		gen.bind_method(rect, 'Inside', 'bool', ['%s x'%T, '%s y'%T])

		gen.bind_method(rect, 'FitsInside', 'bool', ['const gs::Rect<%s> &rect'%T])
		gen.bind_method(rect, 'Intersects', 'bool', ['const gs::Rect<%s> &rect'%T])

		gen.bind_method(rect, 'Intersection', 'gs::Rect<%s>'%T, ['const gs::Rect<%s> &rect'%T])

		gen.bind_method(rect, 'Grow', 'gs::Rect<%s>'%T, ['%s border'%T])

		gen.bind_method(rect, 'Offset', 'gs::Rect<%s>'%T, ['%s x'%T, '%s y'%T])
		gen.bind_method(rect, 'Cropped', 'gs::Rect<%s>'%T, ['%s osx'%T, '%s osy'%T, '%s oex'%T, '%s oey'%T])

		gen.bind_static_method(rect, 'FromWidthHeight', 'gs::Rect<%s>'%T, ['%s x'%T, '%s y'%T, '%s w'%T, '%s h'%T])

		gen.end_class(rect)

	bind_rect_T('float', 'Rect')
	bind_rect_T('int', 'IntRect')

	gen.bind_function('ToFloatRect', 'gs::Rect<float>', ['const gs::Rect<int> &rect'])
	gen.bind_function('ToIntRect', 'gs::Rect<int>', ['const gs::Rect<float> &rect'])

	# math futures
	lib.stl.bind_future_T(gen, 'gs::tVector2<float>', 'FutureVector2')
	lib.stl.bind_future_T(gen, 'gs::tVector2<int>', 'FutureIntVector2')
	lib.stl.bind_future_T(gen, 'gs::Vector3', 'FutureVector3')
	lib.stl.bind_future_T(gen, 'gs::Vector4', 'FutureVector4')
	lib.stl.bind_future_T(gen, 'gs::Matrix3', 'FutureMatrix3')
	lib.stl.bind_future_T(gen, 'gs::Matrix4', 'FutureMatrix4')
	lib.stl.bind_future_T(gen, 'gs::Matrix44', 'FutureMatrix44')
	lib.stl.bind_future_T(gen, 'gs::Rect<float>', 'FutureFloatRect')
	lib.stl.bind_future_T(gen, 'gs::Rect<int>', 'FutureIntRect')

	# math std::vector
	bind_std_vector(gen, vector2)
	bind_std_vector(gen, ivector2)
	bind_std_vector(gen, vector3)
	bind_std_vector(gen, vector4)
	bind_std_vector(gen, matrix3)
	bind_std_vector(gen, matrix4)
	bind_std_vector(gen, matrix44)

	# globals
	gen.bind_function_overloads('gs::Dist', [
		('float', ['const gs::Vector3 &a', 'const gs::Vector3 &b'], [])
	])
	gen.bind_function_overloads('gs::Dist2', [
		('float', ['const gs::Vector3 &a', 'const gs::Vector3 &b'], [])
	])


def bind_frustum(gen):
	gen.add_include('foundation/frustum.h')

	frustum_planes = gen.begin_class('gs::FrustumPlanes')
	gen.end_class(frustum_planes)


def bind_mixer(gen):
	gen.add_include('engine/mixer.h')

	# gs::AudioFormat
	gen.bind_named_enum('gs::AudioFormat::Encoding', ['PCM', 'WiiADPCM'], 'uint8_t', bound_name='AudioFormatEncoding', prefix='AudioFormat')
	gen.bind_named_enum('gs::AudioFormat::Type', ['Integer', 'Float'], 'uint8_t', bound_name='AudioFormatType', prefix='AudioType')

	audio_format = gen.begin_class('gs::AudioFormat')
	gen.bind_constructor_overloads(audio_format, [
			([], []),
			(['gs::AudioFormat::Encoding encoding'], []),
			(['gs::AudioFormat::Encoding encoding', 'uint8_t channels'], []),
			(['gs::AudioFormat::Encoding encoding', 'uint8_t channels', 'uint32_t frequency'], []),
			(['gs::AudioFormat::Encoding encoding', 'uint8_t channels', 'uint32_t frequency', 'uint8_t resolution'], []),
			(['gs::AudioFormat::Encoding encoding', 'uint8_t channels', 'uint32_t frequency', 'uint8_t resolution', 'gs::AudioFormat::Type type'], [])
		])
	gen.bind_members(audio_format, ['gs::AudioFormat::Encoding encoding', 'uint8_t channels', 'uint32_t frequency', 'uint8_t resolution', 'gs::AudioFormat::Type type'])
	gen.end_class(audio_format)

	# gs::AudioData
	gen.bind_named_enum('gs::AudioData::State', ['Ready', 'Ended', 'Disconnected'], bound_name='AudioDataState', prefix='AudioData')

	audio_data = gen.begin_class('gs::AudioData', bound_name='AudioData_nobind', noncopyable=True, nobind=True)
	gen.end_class(audio_data)

	shared_audio_data = gen.begin_class('std::shared_ptr<gs::AudioData>', bound_name='AudioData', features={'proxy': lib.stl.SharedPtrProxyFeature(audio_data)})

	gen.bind_method(shared_audio_data, 'GetFormat', 'gs::AudioFormat', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'Open', 'bool', ['const char *path'], ['proxy'])
	gen.bind_method(shared_audio_data, 'Close', 'void', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'GetState', 'gs::AudioData::State', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'Seek', 'bool', ['gs::time_ns t'], ['proxy'])

	gen.insert_binding_code('''\
static size_t AudioData_GetFrameToBinaryBlob(gs::AudioData *audio_data, gs::BinaryBlob &frame, gs::time_ns &frame_timestamp) {
	frame.Reset();
	frame.Grow(audio_data->GetFrameSize());
	size_t size = audio_data->GetFrame(frame.GetData(), frame_timestamp);
	frame.Commit(size);
	return size;
}
''', 'AudioData class extension')

	gen.bind_method(shared_audio_data, 'GetFrame', 'size_t', ['gs::BinaryBlob &frame', 'gs::time_ns &frame_timestamp'], {'proxy': None, 'arg_out': ['frame_timestamp'], 'route': lambda args: 'AudioData_GetFrameToBinaryBlob(%s);' % (', '.join(args))})
	gen.bind_method(shared_audio_data, 'GetFrameSize', 'size_t', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'SetTransform', 'void', ['const gs::Matrix4 &m'], ['proxy'])
	gen.bind_method(shared_audio_data, 'GetDataSize', 'size_t', [], ['proxy'])

	gen.end_class(shared_audio_data)

	# gs::AudioIO
	gen.add_include('engine/audio_io.h')

	audio_io = gen.begin_class('gs::AudioIO', noncopyable=True)
	gen.bind_method_overloads(audio_io, 'Open', [
		('std::shared_ptr<gs::AudioData>', ['const char *path'], []),
		('std::shared_ptr<gs::AudioData>', ['const char *path', 'const char *codec_name'], [])
	])
	gen.bind_method(audio_io, 'GetSupportedExt', 'std::string', [])
	gen.end_class(audio_io)

	gen.insert_binding_code('static gs::AudioIO &GetAudioIO() { return gs::g_audio_io.get(); }')
	gen.bind_function('GetAudioIO', 'gs::AudioIO &', [])

	# gs::audio
	gen.bind_named_enum('gs::audio::MixerLoopMode', ['MixerNoLoop', 'MixerRepeat', 'MixerLoopInvalidChannel'], 'uint8_t')
	gen.bind_named_enum('gs::audio::MixerPlayState', ['MixerStopped', 'MixerPlaying', 'MixerPaused', 'MixerStateInvalidChannel'], 'uint8_t')

	gen.typedef('gs::audio::MixerChannel', 'int32_t')
	gen.typedef('gs::audio::MixerPriority', 'uint8_t')

	#
	mixer_channel_state = gen.begin_class('gs::audio::MixerChannelState')
	gen.bind_constructor_overloads(mixer_channel_state, [
		([], []),
		(['float volume'], []),
		(['float volume', 'bool direct'], []),
		(['gs::audio::MixerPriority priority', '?float volume', '?gs::audio::MixerLoopMode loop_mode', '?float pitch', '?bool direct'], [])
	])
	gen.bind_members(mixer_channel_state, ['gs::audio::MixerPriority priority', 'gs::audio::MixerLoopMode loop_mode', 'float volume', 'float pitch', 'bool direct'])
	gen.end_class(mixer_channel_state)

	mixer_channel_location = gen.begin_class('gs::audio::MixerChannelLocation')
	gen.bind_constructor_overloads(mixer_channel_location, [
		([], []),
		(['const gs::Vector3 &pos'], [])
	])
	gen.bind_members(mixer_channel_location, ['gs::Vector3 position', 'gs::Vector3 velocity'])
	gen.end_class(mixer_channel_location)

	#
	sound = gen.begin_class('gs::audio::Sound', bound_name='Sound_nobind', noncopyable=True, nobind=True)
	gen.end_class(sound)

	shared_sound = gen.begin_class('std::shared_ptr<gs::audio::Sound>', bound_name='Sound', features={'proxy': lib.stl.SharedPtrProxyFeature(sound)})
	gen.bind_constructor_overloads(shared_sound, [
		([], ['proxy']),
		(['const char *name'], ['proxy'])
	])
	gen.bind_method(shared_sound, 'GetName', 'const char *', [], ['proxy'])
	gen.bind_method(shared_sound, 'IsReady', 'bool', [], ['proxy'])
	gen.bind_method(shared_sound, 'SetReady', 'void', [], ['proxy'])
	gen.bind_method(shared_sound, 'SetNotReady', 'void', [], ['proxy'])
	gen.end_class(shared_sound)

	# gs::audio::Mixer
	audio_mixer = gen.begin_class('gs::audio::Mixer', bound_name='Mixer_nobind', noncopyable=True, nobind=True)
	gen.end_class(audio_mixer)

	shared_audio_mixer = gen.begin_class('std::shared_ptr<gs::audio::Mixer>', bound_name='Mixer', features={'proxy': lib.stl.SharedPtrProxyFeature(audio_mixer)})

	gen.bind_static_members(shared_audio_mixer, [
		'const gs::audio::MixerChannelState DefaultState', 'const gs::audio::MixerChannelState RepeatState',
		'const gs::audio::MixerChannelLocation DefaultLocation', 'const gs::audio::MixerPriority DefaultPriority',
		'const gs::audio::MixerChannel ChannelError'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'Open', 'bool', [], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'Close', 'void', [], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetMasterVolume', 'float', [], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SetMasterVolume', 'void', ['float volume'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'EnableSpatialization', 'bool', ['bool enable'], ['proxy'])

	gen.bind_method_overloads(shared_audio_mixer, 'Start', [
		('gs::audio::MixerChannel', ['gs::audio::Sound &sound'], ['proxy']),
		('gs::audio::MixerChannel', ['gs::audio::Sound &sound', 'gs::audio::MixerChannelState state'], ['proxy']),
		('gs::audio::MixerChannel', ['gs::audio::Sound &sound', 'gs::audio::MixerChannelLocation location'], ['proxy']),
		('gs::audio::MixerChannel', ['gs::audio::Sound &sound', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state'], ['proxy'])
	])
	gen.bind_method_overloads(shared_audio_mixer, 'StreamData', [
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'bool paused'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'bool paused', 'gs::time_ns t_start'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelState state'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelState state', 'bool paused'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'bool paused'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'bool paused', 'gs::time_ns t_start'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused'], ['proxy']),
		('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], ['proxy'])
	])

	gen.bind_method(shared_audio_mixer, 'GetPlayState', 'gs::audio::MixerPlayState', ['gs::audio::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetChannelState', 'gs::audio::MixerChannelState', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SetChannelState', 'void', ['gs::audio::MixerChannel channel', 'gs::audio::MixerChannelState state'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetChannelLocation', 'gs::audio::MixerChannelLocation', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SetChannelLocation', 'void', ['gs::audio::MixerChannel channel', 'gs::audio::MixerChannelLocation location'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetChannelTimestamp', 'gs::time_ns', ['gs::audio::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'Stop', 'void', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'Pause', 'void', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'Resume', 'void', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'StopAll', 'void', [], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'SetStreamLoopPoint', 'void', ['gs::audio::MixerChannel channel', 'gs::time_ns t'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SeekStream', 'void', ['gs::audio::MixerChannel channel', 'gs::time_ns t'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'GetStreamBufferingPercentage', 'int', ['gs::audio::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'SetChannelStreamDataTransform', 'void', ['gs::audio::MixerChannel channel', 'const gs::Matrix4 &transform'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'FlushChannelBuffers', 'void', ['gs::audio::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetListener', 'gs::Matrix4', [], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SetListener', 'void', ['const gs::Matrix4 &transform'], ['proxy'])

	gen.bind_method_overloads(shared_audio_mixer, 'Stream', [
		('gs::audio::MixerChannel', ['const char *path'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'bool paused'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'bool paused', 'gs::time_ns t_start'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelState state'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelState state', 'bool paused'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'bool paused'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'bool paused', 'gs::time_ns t_start'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused'], ['proxy']),
		('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], ['proxy'])
	])

	gen.bind_method_overloads(shared_audio_mixer, 'LoadSoundData', [
		('std::shared_ptr<gs::audio::Sound>', ['std::shared_ptr<gs::AudioData> data'], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'LoadSoundData failed')}),
		('std::shared_ptr<gs::audio::Sound>', ['std::shared_ptr<gs::AudioData> data', 'const char *path'], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'LoadSoundData failed')})
	])

	gen.bind_method(shared_audio_mixer, 'LoadSound', 'std::shared_ptr<gs::audio::Sound>', ['const char *path'], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'LoadSound failed')})
	gen.bind_method(shared_audio_mixer, 'FreeSound', 'void', ['gs::audio::Sound &sound'], ['proxy'])

	gen.end_class(shared_audio_mixer)

	gen.insert_binding_code('''static std::shared_ptr<gs::audio::Mixer> CreateMixer(const char *name) { return gs::core::g_mixer_factory.get().Instantiate(name); }
static std::shared_ptr<gs::audio::Mixer> CreateMixer() { return gs::core::g_mixer_factory.get().Instantiate(); }
	''', 'Mixer custom API')

	gen.bind_function('CreateMixer', 'std::shared_ptr<gs::audio::Mixer>', ['?const char *name'], {'check_rval': check_rval_lambda(gen, 'CreateMixer failed, was LoadPlugins called succesfully?')})

	# gs::audio::MixerAsync
	mixer_async = gen.begin_class('gs::audio::MixerAsync', bound_name='MixerAsync_nobind', noncopyable=True, nobind=True)
	gen.end_class(mixer_async)

	shared_mixer_async = gen.begin_class('std::shared_ptr<gs::audio::MixerAsync>', bound_name='MixerAsync', features={'proxy': lib.stl.SharedPtrProxyFeature(mixer_async)})

	gen.bind_constructor(shared_mixer_async, ['std::shared_ptr<gs::audio::Mixer> mixer'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'Open', 'std::future<bool>', [], ['proxy'])
	gen.bind_method(shared_mixer_async, 'Close', 'std::future<void>', [], ['proxy'])

	gen.bind_method(shared_mixer_async, 'EnableSpatialization', 'std::future<bool>', ['bool enable'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetMasterVolume', 'std::future<float>', [], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SetMasterVolume', 'void', ['float volume'], ['proxy'])

	lib.stl.bind_future_T(gen, 'gs::audio::MixerChannel', 'FutureMixerChannel')
	lib.stl.bind_future_T(gen, 'gs::audio::MixerChannelState', 'FutureMixerChannelState')
	lib.stl.bind_future_T(gen, 'gs::audio::MixerChannelLocation', 'FutureMixerChannelLocation')
	lib.stl.bind_future_T(gen, 'gs::audio::MixerPlayState', 'FutureMixerPlayState')

	gen.bind_method_overloads(shared_mixer_async, 'Start', [
		('std::future<gs::audio::MixerChannel>', ['std::shared_ptr<gs::audio::Sound> sound'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['std::shared_ptr<gs::audio::Sound> sound', 'gs::audio::MixerChannelState state'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['std::shared_ptr<gs::audio::Sound> sound', 'gs::audio::MixerChannelLocation location'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['std::shared_ptr<gs::audio::Sound> sound', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state'], ['proxy'])
	])
	gen.bind_method_overloads(shared_mixer_async, 'Stream', [
		('std::future<gs::audio::MixerChannel>', ['const char *path'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'bool paused'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'bool paused', 'gs::time_ns t_start'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'gs::audio::MixerChannelState state'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'gs::audio::MixerChannelState state', 'bool paused'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'gs::audio::MixerChannelLocation location'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'gs::audio::MixerChannelLocation location', 'bool paused'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'gs::audio::MixerChannelLocation location', 'bool paused', 'gs::time_ns t_start'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused'], ['proxy']),
		('std::future<gs::audio::MixerChannel>', ['const char *path', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], ['proxy'])
	])

	gen.bind_method(shared_mixer_async, 'GetPlayState', 'std::future<gs::audio::MixerPlayState>', ['gs::audio::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetChannelState', 'std::future<gs::audio::MixerChannelState>', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SetChannelState', 'void', ['gs::audio::MixerChannel channel', 'gs::audio::MixerChannelState state'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetChannelLocation', 'std::future<gs::audio::MixerChannelLocation>', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SetChannelLocation', 'void', ['gs::audio::MixerChannel channel', 'gs::audio::MixerChannelLocation location'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetChannelTimestamp', 'std::future<gs::time_ns>', ['gs::audio::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'Stop', 'void', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'Pause', 'void', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'Resume', 'void', ['gs::audio::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'StopAll', 'void', [], ['proxy'])

	gen.bind_method(shared_mixer_async, 'SetStreamLoopPoint', 'void', ['gs::audio::MixerChannel channel', 'gs::time_ns t'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SeekStream', 'void', ['gs::audio::MixerChannel channel', 'gs::time_ns t'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'GetStreamBufferingPercentage', 'std::future<int>', ['gs::audio::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'SetChannelStreamDataTransform', 'void', ['gs::audio::MixerChannel channel', 'const gs::Matrix4 &transform'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'FlushChannelBuffers', 'void', ['gs::audio::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetListener', 'std::future<gs::Matrix4>', [], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SetListener', 'void', ['const gs::Matrix4 &transform'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'LoadSound', 'std::shared_ptr<gs::audio::Sound>', ['const char *path'], {'proxy': None, 'check_rval': check_rval_lambda(gen, 'LoadSound failed')})
	gen.bind_method(shared_mixer_async, 'FreeSound', 'void', ['const std::shared_ptr<gs::audio::Sound> &sound'], ['proxy'])

	gen.end_class(shared_mixer_async)


def bind_imgui(gen):
	gen.add_include('engine/imgui.h')

	imvec2 = gen.begin_class('ImVec2')
	gen.bind_constructor_overloads(imvec2, [
		([], []),
		(['float x', 'float y'], [])
	])
	gen.bind_members(imvec2, ['float x', 'float y'])
	gen.end_class(imvec2)

	imvec4 = gen.begin_class('ImVec4')
	gen.bind_constructor_overloads(imvec4, [
		([], []),
		(['float x', 'float y', 'float z', 'float w'], [])
	])
	gen.bind_members(imvec4, ['float x', 'float y', 'float z', 'float w'])
	gen.end_class(imvec4)

	gen.bind_named_enum('ImGuiWindowFlags', [
		'ImGuiWindowFlags_NoTitleBar', 'ImGuiWindowFlags_NoResize', 'ImGuiWindowFlags_NoMove', 'ImGuiWindowFlags_NoScrollbar', 'ImGuiWindowFlags_NoScrollWithMouse',
		'ImGuiWindowFlags_NoCollapse', 'ImGuiWindowFlags_AlwaysAutoResize', 'ImGuiWindowFlags_ShowBorders', 'ImGuiWindowFlags_NoSavedSettings', 'ImGuiWindowFlags_NoInputs',
		'ImGuiWindowFlags_MenuBar', 'ImGuiWindowFlags_HorizontalScrollbar', 'ImGuiWindowFlags_NoFocusOnAppearing', 'ImGuiWindowFlags_NoBringToFrontOnFocus',
		'ImGuiWindowFlags_AlwaysVerticalScrollbar', 'ImGuiWindowFlags_AlwaysHorizontalScrollbar', 'ImGuiWindowFlags_AlwaysUseWindowPadding'
	], 'int', namespace='')

	gen.bind_named_enum('ImGuiSetCond', ['ImGuiSetCond_Always', 'ImGuiSetCond_Once', 'ImGuiSetCond_FirstUseEver', 'ImGuiSetCond_Appearing'], 'int', namespace='')

	gen.bind_named_enum('ImGuiInputTextFlags', [
		'ImGuiInputTextFlags_CharsDecimal', 'ImGuiInputTextFlags_CharsHexadecimal', 'ImGuiInputTextFlags_CharsUppercase', 'ImGuiInputTextFlags_CharsNoBlank',
		'ImGuiInputTextFlags_AutoSelectAll', 'ImGuiInputTextFlags_EnterReturnsTrue', 'ImGuiInputTextFlags_CallbackCompletion', 'ImGuiInputTextFlags_CallbackHistory',
		'ImGuiInputTextFlags_CallbackAlways', 'ImGuiInputTextFlags_CallbackCharFilter', 'ImGuiInputTextFlags_AllowTabInput', 'ImGuiInputTextFlags_CtrlEnterForNewLine',
		'ImGuiInputTextFlags_NoHorizontalScroll', 'ImGuiInputTextFlags_AlwaysInsertMode', 'ImGuiInputTextFlags_ReadOnly', 'ImGuiInputTextFlags_Password'
	], 'int', namespace='')

	gen.bind_named_enum('ImGuiTreeNodeFlags', [
		'ImGuiTreeNodeFlags_Selected', 'ImGuiTreeNodeFlags_Framed', 'ImGuiTreeNodeFlags_AllowOverlapMode', 'ImGuiTreeNodeFlags_NoTreePushOnOpen',
		'ImGuiTreeNodeFlags_NoAutoOpenOnLog', 'ImGuiTreeNodeFlags_DefaultOpen', 'ImGuiTreeNodeFlags_OpenOnDoubleClick', 'ImGuiTreeNodeFlags_OpenOnArrow',
		'ImGuiTreeNodeFlags_Leaf', 'ImGuiTreeNodeFlags_Bullet', 'ImGuiTreeNodeFlags_CollapsingHeader'
	], 'int', namespace='')

	gen.bind_named_enum('ImGuiSelectableFlags', ['ImGuiSelectableFlags_DontClosePopups', 'ImGuiSelectableFlags_SpanAllColumns', 'ImGuiSelectableFlags_AllowDoubleClick'], 'int', namespace='')

	gen.bind_named_enum('ImGuiCol', [
		'ImGuiCol_Text', 'ImGuiCol_TextDisabled', 'ImGuiCol_WindowBg', 'ImGuiCol_ChildWindowBg', 'ImGuiCol_PopupBg', 'ImGuiCol_Border', 'ImGuiCol_BorderShadow',
		'ImGuiCol_FrameBg', 'ImGuiCol_FrameBgHovered', 'ImGuiCol_FrameBgActive', 'ImGuiCol_TitleBg', 'ImGuiCol_TitleBgCollapsed', 'ImGuiCol_TitleBgActive', 'ImGuiCol_MenuBarBg',
		'ImGuiCol_ScrollbarBg', 'ImGuiCol_ScrollbarGrab', 'ImGuiCol_ScrollbarGrabHovered', 'ImGuiCol_ScrollbarGrabActive', 'ImGuiCol_ComboBg', 'ImGuiCol_CheckMark',
		'ImGuiCol_SliderGrab', 'ImGuiCol_SliderGrabActive', 'ImGuiCol_Button', 'ImGuiCol_ButtonHovered', 'ImGuiCol_ButtonActive', 'ImGuiCol_Header', 'ImGuiCol_HeaderHovered',
		'ImGuiCol_HeaderActive', 'ImGuiCol_Column', 'ImGuiCol_ColumnHovered', 'ImGuiCol_ColumnActive', 'ImGuiCol_ResizeGrip', 'ImGuiCol_ResizeGripHovered', 'ImGuiCol_ResizeGripActive',
		'ImGuiCol_CloseButton', 'ImGuiCol_CloseButtonHovered', 'ImGuiCol_CloseButtonActive', 'ImGuiCol_PlotLines', 'ImGuiCol_PlotLinesHovered', 'ImGuiCol_PlotHistogram', 'ImGuiCol_PlotHistogramHovered',
		'ImGuiCol_TextSelectedBg', 'ImGuiCol_ModalWindowDarkening'
	], 'int', namespace='')

	gen.bind_named_enum('ImGuiStyleVar', [
		'ImGuiStyleVar_Alpha', 'ImGuiStyleVar_WindowPadding', 'ImGuiStyleVar_WindowRounding', 'ImGuiStyleVar_WindowMinSize', 'ImGuiStyleVar_ChildWindowRounding', 'ImGuiStyleVar_FramePadding',
		'ImGuiStyleVar_FrameRounding', 'ImGuiStyleVar_ItemSpacing', 'ImGuiStyleVar_ItemInnerSpacing', 'ImGuiStyleVar_IndentSpacing', 'ImGuiStyleVar_GrabMinSize', 'ImGuiStyleVar_ButtonTextAlign'
	], 'int', namespace='')

	#gen.bind_function('ImGui::GetIO', 'ImGuiIO &', [], bound_name='ImGuiGetIO')
	#gen.bind_function('ImGui::GetStyle', 'ImGuiStyle &', [], bound_name='ImGuiGetStyle')

	gen.bind_function('ImGui::NewFrame', 'void', [], bound_name='ImGuiNewFrame')
	gen.bind_function('ImGui::Render', 'void', [], bound_name='ImGuiRender')
	gen.bind_function('ImGui::Shutdown', 'void', [], bound_name='ImGuiShutdown')

	gen.bind_function_overloads('ImGui::Begin', [
		('bool', ['const char *name'], []),
		('bool', ['const char *name', 'bool *open', 'ImGuiWindowFlags flags'], {'arg_out': ['open']}),
		('bool', ['const char *name', 'bool *open', 'const gs::tVector2<float> &size_on_first_use', 'float background_alpha', 'ImGuiWindowFlags flags'], {'arg_out': ['open']})
	], bound_name='ImGuiBegin')
	gen.bind_function('ImGui::End', 'void', [], bound_name='ImGuiEnd')

	gen.bind_function('ImGui::BeginChild', 'bool', ['const char *id', '?const ImVec2 &size', '?bool border', '?ImGuiWindowFlags extra_flags'], bound_name='ImGuiBeginChild')
	gen.bind_function('ImGui::EndChild', 'void', [], bound_name='ImGuiEndChild')

	gen.bind_function('ImGui::GetContentRegionMax', 'gs::tVector2<float>', [], bound_name='ImGuiGetContentRegionMax')
	gen.bind_function('ImGui::GetContentRegionAvail', 'gs::tVector2<float>', [], bound_name='ImGuiGetContentRegionAvail')
	gen.bind_function('ImGui::GetContentRegionAvailWidth', 'float', [], bound_name='ImGuiGetContentRegionAvailWidth')
	gen.bind_function('ImGui::GetWindowContentRegionMin', 'gs::tVector2<float>', [], bound_name='ImGuiGetWindowContentRegionMin')
	gen.bind_function('ImGui::GetWindowContentRegionMax', 'gs::tVector2<float>', [], bound_name='ImGuiGetWindowContentRegionMax')
	gen.bind_function('ImGui::GetWindowContentRegionWidth', 'float', [], bound_name='ImGuiGetWindowContentRegionWidth')
	#IMGUI_API ImDrawList*   GetWindowDrawList();                                                // get rendering command-list if you want to append your own draw primitives
	gen.bind_function('ImGui::GetWindowPos', 'gs::tVector2<float>', [], bound_name='ImGuiGetWindowPos')
	gen.bind_function('ImGui::GetWindowSize', 'gs::tVector2<float>', [], bound_name='ImGuiGetWindowSize')
	gen.bind_function('ImGui::GetWindowWidth', 'float', [], bound_name='ImGuiGetWindowWidth')
	gen.bind_function('ImGui::GetWindowHeight', 'float', [], bound_name='ImGuiGetWindowHeight')
	gen.bind_function('ImGui::IsWindowCollapsed', 'bool', [], bound_name='ImGuiIsWindowCollapsed')
	gen.bind_function('ImGui::SetWindowFontScale', 'void', ['float scale'], bound_name='ImGuiSetWindowFontScale')

	gen.bind_function('ImGui::SetNextWindowPos', 'void', ['const gs::tVector2<float> &pos', '?ImGuiSetCond condition'], bound_name='ImGuiSetNextWindowPos')
	gen.bind_function('ImGui::SetNextWindowPosCenter', 'void', ['?ImGuiSetCond condition'], bound_name='ImGuiSetNextWindowPosCenter')
	gen.bind_function('ImGui::SetNextWindowSize', 'void', ['const gs::tVector2<float> &size', '?ImGuiSetCond condition'], bound_name='ImGuiSetNextWindowSize')
	gen.bind_function('ImGui::SetNextWindowContentSize', 'void', ['const gs::tVector2<float> &size'], bound_name='ImGuiSetNextWindowContentSize')
	gen.bind_function('ImGui::SetNextWindowContentWidth', 'void', ['float width'], bound_name='ImGuiSetNextWindowContentWidth')
	gen.bind_function('ImGui::SetNextWindowCollapsed', 'void', ['bool collapsed', 'ImGuiSetCond condition'], bound_name='ImGuiSetNextWindowCollapsed')
	gen.bind_function('ImGui::SetNextWindowFocus', 'void', [], bound_name='ImGuiSetNextWindowFocus')
	gen.bind_function('ImGui::SetWindowPos', 'void', ['const gs::tVector2<float> &pos', '?ImGuiSetCond condition'], bound_name='ImGuiSetWindowPos')
	gen.bind_function('ImGui::SetWindowSize', 'void', ['const gs::tVector2<float> &size', '?ImGuiSetCond condition'], bound_name='ImGuiSetWindowSize')
	gen.bind_function('ImGui::SetWindowCollapsed', 'void', ['bool collapsed', '?ImGuiSetCond condition'], bound_name='ImGuiSetWindowCollapsed')
	gen.bind_function('ImGui::SetWindowFocus', 'void', ['?const char *name'], bound_name='ImGuiSetWindowFocus')

	gen.bind_function('ImGui::GetScrollX', 'float', [], bound_name='ImGuiGetScrollX')
	gen.bind_function('ImGui::GetScrollY', 'float', [], bound_name='ImGuiGetScrollY')
	gen.bind_function('ImGui::GetScrollMaxX', 'float', [], bound_name='ImGuiGetScrollMaxX')
	gen.bind_function('ImGui::GetScrollMaxY', 'float', [], bound_name='ImGuiGetScrollMaxY')
	gen.bind_function('ImGui::SetScrollX', 'void', ['float scroll_x'], bound_name='ImGuiSetScrollX')
	gen.bind_function('ImGui::SetScrollY', 'void', ['float scroll_y'], bound_name='ImGuiSetScrollY')
	gen.bind_function('ImGui::SetScrollHere', 'void', ['?float center_y_ratio'], bound_name='ImGuiSetScrollHere')
	gen.bind_function('ImGui::SetScrollFromPosY', 'void', ['float pos_y', '?float center_y_ratio'], bound_name='ImGuiSetScrollFromPosY')
	gen.bind_function('ImGui::SetKeyboardFocusHere', 'void', ['?int offset'], bound_name='ImGuiSetKeyboardFocusHere')

	imfont = gen.begin_class('ImFont')
	gen.end_class(imfont)

	gen.bind_function('ImGui::PushFont', 'void', ['ImFont *font'], bound_name='ImGuiPushFont')
	gen.bind_function('ImGui::PopFont', 'void', [], bound_name='ImGuiPopFont')
	gen.bind_function('ImGui::PushStyleColor', 'void', ['ImGuiCol idx', 'const gs::Color &color'], bound_name='ImGuiPushStyleColor')
	gen.bind_function('ImGui::PopStyleColor', 'void', ['?int count'], bound_name='ImGuiPopStyleColor')
	gen.bind_function_overloads('ImGui::PushStyleVar', [
		('void', ['ImGuiStyleVar idx', 'float value'], []),
		('void', ['ImGuiStyleVar idx', 'const gs::tVector2<float> &value'], [])
	], bound_name='ImGuiPushStyleVar')
	gen.bind_function('ImGui::PopStyleVar', 'void', ['?int count'], bound_name='ImGuiPopStyleVar')
	gen.bind_function('ImGui::GetFont', 'ImFont *', [], bound_name='ImGuiGetFont')
	gen.bind_function('ImGui::GetFontSize', 'float', [], bound_name='ImGuiGetFontSize')
	gen.bind_function('ImGui::GetFontTexUvWhitePixel', 'gs::tVector2<float>', [], bound_name='ImGuiGetFontTexUvWhitePixel')
	gen.bind_function_overloads('ImGui::GetColorU32', [
		('uint32_t', ['ImGuiCol idx', '?float alpha_multiplier'], []),
		('uint32_t', ['const gs::Color &color'], [])
	], bound_name='ImGuiGetColorU32')

	gen.bind_function('ImGui::PushItemWidth', 'void', ['float item_width'], bound_name='ImGuiPushItemWidth')
	gen.bind_function('ImGui::PopItemWidth', 'void', [], bound_name='ImGuiPopItemWidth')
	gen.bind_function('ImGui::CalcItemWidth', 'float', [], bound_name='ImGuiCalcItemWidth')
	gen.bind_function('ImGui::PushTextWrapPos', 'void', ['?float wrap_pos_x'], bound_name='ImGuiPushTextWrapPos')
	gen.bind_function('ImGui::PopTextWrapPos', 'void', [], bound_name='ImGuiPopTextWrapPos')
	gen.bind_function('ImGui::PushAllowKeyboardFocus', 'void', ['bool v'], bound_name='ImGuiPushAllowKeyboardFocus')
	gen.bind_function('ImGui::PopAllowKeyboardFocus', 'void', [], bound_name='ImGuiPopAllowKeyboardFocus')
	gen.bind_function('ImGui::PushButtonRepeat', 'void', ['bool repeat'], bound_name='ImGuiPushButtonRepeat')
	gen.bind_function('ImGui::PopButtonRepeat', 'void', [], bound_name='ImGuiPopButtonRepeat')

	gen.bind_function('ImGui::Separator', 'void', [], bound_name='ImGuiSeparator')
	gen.bind_function('ImGui::SameLine', 'void', ['?float pos_x', '?float spacing_w'], bound_name='ImGuiSameLine')
	gen.bind_function('ImGui::NewLine', 'void', [], bound_name='ImGuiNewLine')
	gen.bind_function('ImGui::Spacing', 'void', [], bound_name='ImGuiSpacing')
	gen.bind_function('ImGui::Dummy', 'void', ['const gs::tVector2<float> &size'], bound_name='ImGuiDummy')
	gen.bind_function('ImGui::Indent', 'void', ['?float width'], bound_name='ImGuiIndent')
	gen.bind_function('ImGui::Unindent', 'void', ['?float width'], bound_name='ImGuiUnindent')
	gen.bind_function('ImGui::BeginGroup', 'void', [], bound_name='ImGuiBeginGroup')
	gen.bind_function('ImGui::EndGroup', 'void', [], bound_name='ImGuiEndGroup')
	gen.bind_function('ImGui::GetCursorPos', 'gs::tVector2<float>', [], bound_name='ImGuiGetCursorPos')
	gen.bind_function('ImGui::GetCursorPosX', 'float', [], bound_name='ImGuiGetCursorPosX')
	gen.bind_function('ImGui::GetCursorPosY', 'float', [], bound_name='ImGuiGetCursorPosY')
	gen.bind_function('ImGui::SetCursorPos', 'void', ['const gs::tVector2<float> &local_pos'], bound_name='ImGuiSetCursorPos')
	gen.bind_function('ImGui::SetCursorPosX', 'void', ['float x'], bound_name='ImGuiSetCursorPosX')
	gen.bind_function('ImGui::SetCursorPosY', 'void', ['float y'], bound_name='ImGuiSetCursorPosY')
	gen.bind_function('ImGui::GetCursorStartPos', 'gs::tVector2<float>', [], bound_name='ImGuiGetCursorStartPos')
	gen.bind_function('ImGui::GetCursorScreenPos', 'gs::tVector2<float>', [], bound_name='ImGuiGetCursorScreenPos')
	gen.bind_function('ImGui::SetCursorScreenPos', 'void', ['const gs::tVector2<float> &pos'], bound_name='ImGuiSetCursorScreenPos')
	gen.bind_function('ImGui::AlignFirstTextHeightToWidgets', 'void', [], bound_name='ImGuiAlignFirstTextHeightToWidgets')
	gen.bind_function('ImGui::GetTextLineHeight', 'float', [], bound_name='ImGuiGetTextLineHeight')
	gen.bind_function('ImGui::GetTextLineHeightWithSpacing', 'float', [], bound_name='ImGuiGetTextLineHeightWithSpacing')
	gen.bind_function('ImGui::GetItemsLineHeightWithSpacing', 'float', [], bound_name='ImGuiGetItemsLineHeightWithSpacing')

	gen.bind_function('ImGui::Columns', 'void', ['?int count', '?const char *id', '?bool with_border'], bound_name='ImGuiColumns')
	gen.bind_function('ImGui::NextColumn', 'void', [], bound_name='ImGuiNextColumn')
	gen.bind_function('ImGui::GetColumnIndex', 'int', [], bound_name='ImGuiGetColumnIndex')
	gen.bind_function('ImGui::GetColumnOffset', 'float', ['?int column_index'], bound_name='ImGuiGetColumnOffset')
	gen.bind_function('ImGui::SetColumnOffset', 'void', ['int column_index', 'float offset_x'], bound_name='ImGuiSetColumnOffset')
	gen.bind_function('ImGui::GetColumnWidth', 'float', ['?int column_index'], bound_name='ImGuiGetColumnWidth')
	gen.bind_function('ImGui::GetColumnsCount', 'int', [], bound_name='ImGuiGetColumnsCount')

	gen.typedef('ImGuiID', 'unsigned int')

	gen.bind_function_overloads('ImGui::PushID', [
		('void', ['const char *id'], []),
		('void', ['int id'], [])
	], bound_name='ImGuiPushID')
	gen.bind_function('ImGui::PopID', 'void', [], bound_name='ImGuiPopID')
	gen.bind_function('ImGui::GetID', 'ImGuiID', ['const char *id'], bound_name='ImGuiGetID')

	gen.bind_function('ImGui::Text', 'void', ['const char *text'], bound_name='ImGuiText')
	gen.bind_function('ImGui::TextColored', 'void', ['const gs::Color &color', 'const char *text'], bound_name='ImGuiTextColored')
	gen.bind_function('ImGui::TextDisabled', 'void', ['const char *text'], bound_name='ImGuiTextDisabled')
	gen.bind_function('ImGui::TextWrapped', 'void', ['const char *text'], bound_name='ImGuiTextWrapped')
	gen.bind_function('ImGui::TextUnformatted', 'void', ['const char *text'], bound_name='ImGuiTextUnformatted')
	gen.bind_function('ImGui::LabelText', 'void', ['const char *label', 'const char *text'], bound_name='ImGuiLabelText')
	gen.bind_function('ImGui::Bullet', 'void', [], bound_name='ImGuiBullet')
	gen.bind_function('ImGui::BulletText', 'void', ['const char *label'], bound_name='ImGuiBulletText')
	gen.bind_function('ImGui::Button', 'bool', ['const char *label', '?const gs::tVector2<float> &size'], bound_name='ImGuiButton')
	gen.bind_function('ImGui::SmallButton', 'bool', ['const char *label'], bound_name='ImGuiSmallButton')
	gen.bind_function('ImGui::InvisibleButton', 'bool', ['const char *text', 'const gs::tVector2<float> &size'], bound_name='ImGuiInvisibleButton')

	gen.bind_function('ImGui::Image', 'void', ['gs::gpu::Texture *texture', 'const gs::tVector2<float> &size', '?const gs::tVector2<float> &uv0', '?const gs::tVector2<float> &uv1', '?const gs::Color &tint_col', '?const gs::Color &border_col'], bound_name='ImGuiImage')
	gen.bind_function('ImGui::ImageButton', 'bool', ['gs::gpu::Texture *texture', 'const gs::tVector2<float> &size', '?const gs::tVector2<float> &uv0', '?const gs::tVector2<float> &uv1', '?int frame_padding', '?const gs::Color &bg_col', '?const gs::Color &tint_col'], bound_name='ImGuiImageButton')

	gen.bind_function('ImGui::Checkbox', 'bool', ['const char *label', 'bool *value'], {'arg_in_out': ['value']}, 'ImGuiCheckbox')
	#IMGUI_API bool          CheckboxFlags(const char* label, unsigned int* flags, unsigned int flags_value);
	gen.bind_function('ImGui::RadioButton', 'bool', ['const char *label', 'bool active'], bound_name='ImGuiRadioButton')

	gen.insert_binding_code('''\
static bool _ImGuiCombo(const char *label, int *current_item, const std::vector<std::string> &items, int height_in_items = -1) {
	auto item_cb = [](void *data, int idx, const char **out_text) -> bool {
		auto &items = *(const std::vector<std::string> *)data;
		if (size_t(idx) >= items.size())
			return false;
		*out_text = items[idx].c_str();
		return true;
	};
	return ImGui::Combo(label, current_item, item_cb, (void *)&items, items.size(), height_in_items);
}

static bool _ImGuiColorButton(gs::Color &color, bool small_height = false, bool outline_border = true) { return ImGui::ColorButton(*(ImVec4 *)&color, small_height, outline_border); }
static bool _ImGuiColorEdit(const char *label, gs::Color &color, bool show_alpha = true) { return ImGui::ColorEdit4(label, &color.r, show_alpha); }
static void _ImGuiProgressBar(float fraction, const gs::tVector2<float> &size = gs::tVector2<float>(-1, 0), const char *overlay = nullptr) { ImGui::ProgressBar(fraction, size, overlay); }
''')

	imgui_combo_protos = [('bool', ['const char *label', 'int *current_item', 'const std::vector<std::string> &items', '?int height_in_items'], {'arg_in_out': ['current_item']})]
	if gen.get_language() == "CPython":
		imgui_combo_protos += [('bool', ['const char *label', 'int *current_item', 'PySequenceOfString items', '?int height_in_items'], {'arg_in_out': ['current_item']})]
	gen.bind_function_overloads('_ImGuiCombo', imgui_combo_protos, bound_name='ImGuiCombo')

	gen.bind_function('_ImGuiColorButton', 'bool', ['gs::Color &color', '?bool small_height', '?bool outline_border'], {'arg_in_out': ['color']}, bound_name='ImGuiColorButton')
	gen.bind_function('_ImGuiColorEdit', 'bool', ['const char *label', 'gs::Color &color', '?bool show_alpha'], {'arg_in_out': ['color']}, bound_name='ImGuiColorEdit')
	gen.bind_function('_ImGuiProgressBar', 'void', ['float fraction', '?const gs::tVector2<float> &size', '?const char *overlay'], bound_name='ImGuiProgressBar')

	gen.insert_binding_code('''\
static bool _ImGuiDragiVector2(const char *label, gs::tVector2<int> &v, float v_speed = 1.f, int v_min = 0, int v_max = 0) { return ImGui::DragInt2(label, &v.x, v_speed, v_min, v_max); }

static bool _ImGuiDragVector2(const char *label, gs::tVector2<float> &v, float v_speed = 1.f, float v_min = 0.f, float v_max = 0.f) { return ImGui::DragFloat2(label, &v.x, v_speed, v_min, v_max); }
static bool _ImGuiDragVector3(const char *label, gs::Vector3 &v, float v_speed = 1.f, float v_min = 0.f, float v_max = 0.f) { return ImGui::DragFloat3(label, &v.x, v_speed, v_min, v_max); }
static bool _ImGuiDragVector4(const char *label, gs::Vector4 &v, float v_speed = 1.f, float v_min = 0.f, float v_max = 0.f) { return ImGui::DragFloat4(label, &v.x, v_speed, v_min, v_max); }
''')

	gen.bind_function_overloads('ImGui::DragFloat', [
		('bool', ['const char *label', 'float *v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float v_speed', 'float v_min', 'float v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragFloat')
	gen.bind_function_overloads('_ImGuiDragVector2', [
		('bool', ['const char *label', 'gs::tVector2<float> &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::tVector2<float> &v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::tVector2<float> &v', 'float v_speed', 'float v_min', 'float v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragVector2')
	gen.bind_function_overloads('_ImGuiDragVector3', [
		('bool', ['const char *label', 'gs::Vector3 &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::Vector3 &v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::Vector3 &v', 'float v_speed', 'float v_min', 'float v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragVector3')
	gen.bind_function_overloads('_ImGuiDragVector4', [
		('bool', ['const char *label', 'gs::Vector4 &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::Vector4 &v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::Vector4 &v', 'float v_speed', 'float v_min', 'float v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragVector4')

	gen.bind_function_overloads('_ImGuiDragiVector2', [
		('bool', ['const char *label', 'gs::tVector2<int> &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::tVector2<int> &v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::tVector2<int> &v', 'float v_speed', 'int v_min', 'int v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragIntVector2')

	#IMGUI_API bool InputText(const char* label, char* buf, size_t buf_size, ImGuiInputTextFlags flags = 0, ImGuiTextEditCallback callback = NULL, void* user_data = NULL);
	#IMGUI_API bool InputTextMultiline(const char* label, char* buf, size_t buf_size, const ImVec2& size = ImVec2(0,0), ImGuiInputTextFlags flags = 0, ImGuiTextEditCallback callback = NULL, void* user_data = NULL);

	gen.insert_binding_code('''\
static bool _ImGuiInputiVector2(const char *label, gs::tVector2<int> &v, ImGuiInputTextFlags extra_flags = 0) { return ImGui::InputInt2(label, &v.x, extra_flags); }

static bool _ImGuiInputVector2(const char *label, gs::tVector2<float> &v, int decimal_precision = -1, ImGuiInputTextFlags extra_flags = 0) { return ImGui::InputFloat2(label, &v.x, decimal_precision, extra_flags); }
static bool _ImGuiInputVector3(const char *label, gs::Vector3 &v, int decimal_precision = -1, ImGuiInputTextFlags extra_flags = 0) { return ImGui::InputFloat3(label, &v.x, decimal_precision, extra_flags); }
static bool _ImGuiInputVector4(const char *label, gs::Vector4 &v, int decimal_precision = -1, ImGuiInputTextFlags extra_flags = 0) { return ImGui::InputFloat4(label, &v.x, decimal_precision, extra_flags); }
''')

	gen.bind_function_overloads('ImGui::InputFloat', [
		('bool', ['const char *label', 'float *v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float step', 'float step_fast'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float step', 'float step_fast', 'int decimal_precision'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float step', 'float step_fast', 'int decimal_precision', 'ImGuiInputTextFlags extra_flags'], {'arg_in_out': ['v']})
	], bound_name='ImGuiInputFloat')
	gen.bind_function_overloads('_ImGuiInputVector2', [
		('bool', ['const char *label', 'gs::tVector2<float> &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::tVector2<float> &v', 'int decimal_precision'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::tVector2<float> &v', 'int decimal_precision', 'ImGuiInputTextFlags extra_flags'], {'arg_in_out': ['v']})
	], bound_name='ImGuiInputVector2')
	gen.bind_function_overloads('_ImGuiInputVector3', [
		('bool', ['const char *label', 'gs::Vector3 &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::Vector3 &v', 'int decimal_precision'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::Vector3 &v', 'int decimal_precision', 'ImGuiInputTextFlags extra_flags'], {'arg_in_out': ['v']})
	], bound_name='ImGuiInputVector3')
	gen.bind_function_overloads('_ImGuiInputVector4', [
		('bool', ['const char *label', 'gs::Vector4 &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::Vector4 &v', 'int decimal_precision'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'gs::Vector4 &v', 'int decimal_precision', 'ImGuiInputTextFlags extra_flags'], {'arg_in_out': ['v']})
	], bound_name='ImGuiInputVector4')

	gen.insert_binding_code('''\
static bool _ImGuiSlideriVector2(const char *label, gs::tVector2<int> &v, int v_min, int v_max) { return ImGui::SliderInt2(label, &v.x, v_min, v_max); }

static bool _ImGuiSliderVector2(const char *label, gs::tVector2<float> &v, float v_min, float v_max) { return ImGui::SliderFloat2(label, &v.x, v_min, v_max); }
static bool _ImGuiSliderVector3(const char *label, gs::Vector3 &v, float v_min, float v_max) { return ImGui::SliderFloat3(label, &v.x, v_min, v_max); }
static bool _ImGuiSliderVector4(const char *label, gs::Vector4 &v, float v_min, float v_max) { return ImGui::SliderFloat4(label, &v.x, v_min, v_max); }
''')

	gen.bind_function('_ImGuiSlideriVector2', 'bool', ['const char *label', 'gs::tVector2<int> &v', 'int v_min', 'int v_max'], {'arg_in_out': ['v']}, 'ImGuiSliderIntVector2')

	gen.bind_function('_ImGuiSliderVector2', 'bool', ['const char *label', 'gs::tVector2<float> &v', 'float v_min', 'float v_max'], {'arg_in_out': ['v']}, 'ImGuiSliderVector2')
	gen.bind_function('_ImGuiSliderVector3', 'bool', ['const char *label', 'gs::Vector3 &v', 'float v_min', 'float v_max'], {'arg_in_out': ['v']}, 'ImGuiSliderVector3')
	gen.bind_function('_ImGuiSliderVector4', 'bool', ['const char *label', 'gs::Vector4 &v', 'float v_min', 'float v_max'], {'arg_in_out': ['v']}, 'ImGuiSliderVector4')

	gen.bind_function('ImGui::TreeNode', 'bool', ['const char *label'], bound_name='ImGuiTreeNode')
	gen.bind_function('ImGui::TreeNodeEx', 'bool', ['const char *label', 'ImGuiTreeNodeFlags flags'], bound_name='ImGuiTreeNodeEx')
	gen.bind_function('ImGui::TreePush', 'void', ['const char *id'], bound_name='ImGuiTreePush')
	gen.bind_function('ImGui::TreePop', 'void', [], bound_name='ImGuiTreePop')
	gen.bind_function('ImGui::TreeAdvanceToLabelPos', 'void', [], bound_name='ImGuiTreeAdvanceToLabelPos')
	gen.bind_function('ImGui::GetTreeNodeToLabelSpacing', 'float', [], bound_name='ImGuiGetTreeNodeToLabelSpacing')
	gen.bind_function('ImGui::SetNextTreeNodeOpen', 'void', ['bool is_open', '?ImGuiSetCond condition'], bound_name='ImGuiSetNextTreeNodeOpen')
	gen.bind_function_overloads('ImGui::CollapsingHeader', [
		('bool', ['const char *label', '?ImGuiTreeNodeFlags flags'], []),
		('bool', ['const char *label', 'bool *p_open', '?ImGuiTreeNodeFlags flags'], {'arg_in_out': ['p_open']})
	], bound_name='ImGuiCollapsingHeader')

	gen.insert_binding_code('''\
static bool _ImGuiSelectable(const char *label, bool selected = false, ImGuiSelectableFlags flags = 0, const gs::tVector2<float> &size = gs::tVector2<float>(0.f, 0.f)) { return ImGui::Selectable(label, selected, flags, ImVec2(size)); }

static bool _ImGuiListBox(const char *label, int *current_item, const std::vector<std::string> &items, int height_in_items = -1) {
	auto cb = [](void *data, int idx, const char **out) -> bool {
		auto &items = *(const std::vector<std::string> *)data;
		if (size_t(idx) >= items.size())
			return false;
		*out = items[idx].c_str();
		return true;
	};
	return ImGui::ListBox(label, current_item, cb, (void *)&items, items.size(), height_in_items);
}
''')

	gen.bind_function('_ImGuiSelectable', 'bool', ['const char *label', '?bool selected', '?ImGuiSelectableFlags flags', '?const gs::tVector2<float> &size'], bound_name='ImGuiSelectable')
	gen.bind_function('_ImGuiListBox', 'bool', ['const char *label', 'int *current_item', 'const std::vector<std::string> &items', '?int height_in_items'], bound_name='ImGuiListBox')

	gen.bind_function('ImGui::SetTooltip', 'void', ['const char *text'], bound_name='ImGuiSetTooltip')
	gen.bind_function('ImGui::BeginTooltip', 'void', [], bound_name='ImGuiBeginTooltip')
	gen.bind_function('ImGui::EndTooltip', 'void', [], bound_name='ImGuiEndTooltip')

	gen.bind_function('ImGui::BeginMainMenuBar', 'bool', [], bound_name='ImGuiBeginMainMenuBar')
	gen.bind_function('ImGui::EndMainMenuBar', 'void', [], bound_name='ImGuiEndMainMenuBar')
	gen.bind_function('ImGui::BeginMenuBar', 'bool', [], bound_name='ImGuiBeginMenuBar')
	gen.bind_function('ImGui::EndMenuBar', 'void', [], bound_name='ImGuiEndMenuBar')
	gen.bind_function('ImGui::BeginMenu', 'bool', ['const char *label', '?bool enabled'], bound_name='ImGuiBeginMenu')
	gen.bind_function('ImGui::EndMenu', 'void', [], bound_name='ImGuiEndMenu')
	gen.bind_function('ImGui::MenuItem', 'bool', ['const char *label', '?const char *shortcut', '?bool selected', '?bool enabled'], bound_name='ImGuiMenuItem')

	gen.bind_function('ImGui::OpenPopup', 'void', ['const char *id'], bound_name='ImGuiOpenPopup')
	gen.bind_function('ImGui::BeginPopup', 'bool', ['const char *id'], bound_name='ImGuiBeginPopup')
	gen.bind_function('ImGui::BeginPopupModal', 'bool', ['const char *name', '?bool *open', '?ImGuiWindowFlags extra_flags'], bound_name='ImGuiBeginPopupModal')
	gen.bind_function('ImGui::BeginPopupContextItem', 'bool', ['const char *id', '?int mouse_button'], bound_name='ImGuiBeginPopupContextItem')
	gen.bind_function('ImGui::BeginPopupContextWindow', 'bool', ['?bool also_over_items', '?const char *id', '?int mouse_button'], bound_name='ImGuiBeginPopupContextWindow')
	gen.bind_function('ImGui::BeginPopupContextVoid', 'bool', ['?const char *id', '?int mouse_button'], bound_name='ImGuiBeginPopupContextVoid')
	gen.bind_function('ImGui::EndPopup', 'void', [], bound_name='ImGuiEndPopup')
	gen.bind_function('ImGui::CloseCurrentPopup', 'void', [], bound_name='ImGuiCloseCurrentPopup')

	gen.insert_binding_code('''\
static void _ImGuiPushClipRect(const gs::tVector2<float> &clip_rect_min, const gs::tVector2<float> &clip_rect_max, bool intersect_with_current_clip_rect) {
	ImGui::PushClipRect(ImVec2(clip_rect_min), ImVec2(clip_rect_max), intersect_with_current_clip_rect);
}

static gs::tVector2<float> _ImGuiGetItemRectMin() { return gs::tVector2<float>(ImGui::GetItemRectMin()); }
static gs::tVector2<float> _ImGuiGetItemRectMax() { return gs::tVector2<float>(ImGui::GetItemRectMax()); }
static gs::tVector2<float> _ImGuiGetItemRectSize() { return gs::tVector2<float>(ImGui::GetItemRectSize()); }

static bool _ImGuiIsRectVisible(const gs::tVector2<float> &size) { return ImGui::IsRectVisible(size); }
static bool _ImGuiIsRectVisible(const gs::tVector2<float> &min, const gs::tVector2<float> &max) { return ImGui::IsRectVisible(min, max); }
static bool _ImGuiIsPosHoveringAnyWindow(const gs::tVector2<float> &pos) { return ImGui::IsPosHoveringAnyWindow(pos); }

static gs::Vector2 _ImGuiCalcItemRectClosestPoint(const gs::Vector2 &pos, bool on_edge = false, float outward = 0.f) { return ImGui::CalcItemRectClosestPoint(pos, on_edge, outward); }
static gs::Vector2 _ImGuiCalcTextSize(const char *text, bool hide_text_after_double_dash = false, float wrap_width = -1.f) { return ImGui::CalcTextSize(text, NULL, hide_text_after_double_dash, wrap_width); }
''')
	gen.bind_function('_ImGuiPushClipRect', 'void', ['const gs::tVector2<float> &clip_rect_min', 'const gs::tVector2<float> &clip_rect_max', 'bool intersect_with_current_clip_rect'], bound_name='ImGuiPushClipRect')
	gen.bind_function('ImGui::PopClipRect', 'void', [], bound_name='ImGuiPopClipRect')

	gen.bind_function('ImGui::IsItemHovered', 'bool', [], bound_name='ImGuiIsItemHovered')
	gen.bind_function('ImGui::IsItemHoveredRect', 'bool', [], bound_name='ImGuiIsItemHoveredRect')
	gen.bind_function('ImGui::IsItemActive', 'bool', [], bound_name='ImGuiIsItemActive')
	gen.bind_function('ImGui::IsItemClicked', 'bool', ['?int mouse_button'], bound_name='ImGuiIsItemClicked')
	gen.bind_function('ImGui::IsItemVisible', 'bool', [], bound_name='ImGuiIsItemVisible')
	gen.bind_function('ImGui::IsAnyItemHovered', 'bool', [], bound_name='ImGuiIsAnyItemHovered')
	gen.bind_function('ImGui::IsAnyItemActive', 'bool', [], bound_name='ImGuiIsAnyItemActive')
	gen.bind_function('_ImGuiGetItemRectMin', 'gs::tVector2<float>', [], bound_name='ImGuiGetItemRectMin')
	gen.bind_function('_ImGuiGetItemRectMax', 'gs::tVector2<float>', [], bound_name='ImGuiGetItemRectMax')
	gen.bind_function('_ImGuiGetItemRectSize', 'gs::tVector2<float>', [], bound_name='ImGuiGetItemRectSize')
	gen.bind_function('ImGui::SetItemAllowOverlap', 'void', [], bound_name='ImGuiSetItemAllowOverlap')
	gen.bind_function('ImGui::IsWindowHovered', 'bool', [], bound_name='ImGuiIsWindowHovered')
	gen.bind_function('ImGui::IsWindowFocused', 'bool', [], bound_name='ImGuiIsWindowFocused')
	gen.bind_function('ImGui::IsRootWindowFocused', 'bool', [], bound_name='ImGuiIsRootWindowFocused')
	gen.bind_function('ImGui::IsRootWindowOrAnyChildFocused', 'bool', [], bound_name='ImGuiIsRootWindowOrAnyChildFocused')
	gen.bind_function('ImGui::IsRootWindowOrAnyChildHovered', 'bool', [], bound_name='ImGuiIsRootWindowOrAnyChildHovered')
	gen.bind_function_overloads('ImGui::IsRectVisible', [
		('bool', ['const gs::tVector2<float> &size'], []),
		('bool', ['const gs::tVector2<float> &rect_min', 'const gs::tVector2<float> &rect_max'], [])
	], bound_name='ImGuiIsRectVisible')
	gen.bind_function('ImGui::IsPosHoveringAnyWindow', 'bool', ['const gs::tVector2<float> &pos'], bound_name='ImGuiIsPosHoveringAnyWindow')
	gen.bind_function('ImGui::GetTime', 'float', [], bound_name='ImGuiGetTime')
	gen.bind_function('ImGui::GetFrameCount', 'int', [], bound_name='ImGuiGetFrameCount')
	#IMGUI_API const char*   GetStyleColName(ImGuiCol idx);
	gen.bind_function('_ImGuiCalcItemRectClosestPoint', 'gs::tVector2<float>', ['const gs::tVector2<float> &pos', '?bool on_edge', '?float outward'], bound_name='ImGuiCalcItemRectClosestPoint')
	gen.bind_function('_ImGuiCalcTextSize', 'gs::tVector2<float>', ['const char *text', '?bool hide_text_after_double_dash', '?float wrap_width'], bound_name='ImGuiCalcTextSize')

	#IMGUI_API bool          BeginChildFrame(ImGuiID id, const ImVec2& size, ImGuiWindowFlags extra_flags = 0);	// helper to create a child window / scrolling region that looks like a normal widget frame
	#IMGUI_API void          EndChildFrame();

	#gen.bind_function('ImGui::GetKeyIndex', 'int', [], bound_name='ImGuiGetKeyIndex')
	gen.bind_function('ImGui::IsKeyDown', 'bool', ['int key_index'], bound_name='ImGuiIsKeyDown')
	gen.bind_function('ImGui::IsKeyPressed', 'bool', ['int key_index', '?bool repeat'], bound_name='ImGuiIsKeyPressed')
	gen.bind_function('ImGui::IsKeyReleased', 'bool', ['int key_index'], bound_name='ImGuiIsKeyReleased')
	gen.bind_function('ImGui::IsMouseDown', 'bool', ['int button'], bound_name='ImGuiIsMouseDown')
	gen.bind_function('ImGui::IsMouseClicked', 'bool', ['int button', '?bool repeat'], bound_name='ImGuiIsMouseClicked')
	gen.bind_function('ImGui::IsMouseDoubleClicked', 'bool', ['int button'], bound_name='ImGuiIsMouseDoubleClicked')
	gen.bind_function('ImGui::IsMouseReleased', 'bool', ['int button'], bound_name='ImGuiIsMouseReleased')
	gen.bind_function('ImGui::IsMouseHoveringWindow', 'bool', [], bound_name='ImGuiIsMouseHoveringWindow')
	gen.bind_function('ImGui::IsMouseHoveringAnyWindow', 'bool', [], bound_name='ImGuiIsMouseHoveringAnyWindow')
	gen.bind_function('ImGui::IsMouseHoveringRect', 'bool', ['const gs::tVector2<float> &rect_min', 'const gs::tVector2<float> &rect_max', '?bool clip'], bound_name='ImGuiIsMouseHoveringRect')
	gen.bind_function('ImGui::IsMouseDragging', 'bool', ['?int button', '?float lock_threshold'], bound_name='ImGuiIsMouseDragging')
	gen.bind_function('ImGui::GetMousePos', 'gs::tVector2<float>', [], bound_name='ImGuiGetMousePos')
	gen.bind_function('ImGui::GetMousePosOnOpeningCurrentPopup', 'gs::tVector2<float>', [], bound_name='ImGuiGetMousePosOnOpeningCurrentPopup')
	gen.bind_function('ImGui::GetMouseDragDelta', 'gs::tVector2<float>', ['?int button', '?float lock_threshold'], bound_name='ImGuiGetMouseDragDelta')
	gen.bind_function('ImGui::ResetMouseDragDelta', 'void', ['?int button'], bound_name='ImGuiResetMouseDragDelta')
	#IMGUI_API ImGuiMouseCursor GetMouseCursor();                                                // get desired cursor type, reset in ImGui::NewFrame(), this updated during the frame. valid before Render(). If you use software rendering by setting io.MouseDrawCursor ImGui will render those for you
	#IMGUI_API void          SetMouseCursor(ImGuiMouseCursor type);                              // set desired cursor type
	gen.bind_function('ImGui::CaptureKeyboardFromApp', 'void', ['bool capture'], bound_name='ImGuiCaptureKeyboardFromApp')
	gen.bind_function('ImGui::CaptureMouseFromApp', 'void', ['bool capture'], bound_name='ImGuiCaptureMouseFromApp')

	gen.bind_function('gs::ImGuiSetOutputSurface', 'void', ['const gs::Surface &surface'], bound_name='ImGuiSetOutputSurface')

	gen.add_include('engine/imgui_renderer_hook.h')

	gen.bind_function('gs::ImGuiLock', 'void', [], {'exception': 'double lock from the same thread, check your program for a missing unlock'})
	gen.bind_function('gs::ImGuiUnlock', 'void', [])


def bind_extras(gen):
	gen.add_include('thread', True)

	gen.insert_binding_code('static void SleepThisThread(gs::time_ns duration) { std::this_thread::sleep_for(gs::time_to_chrono(duration)); }\n\n')
	gen.bind_function('SleepThisThread', 'void', ['gs::time_ns duration'], bound_name='Sleep')


def bind_gs(gen):
	gen.start('harfang')

	lib.bind_defaults(gen)

	gen.add_include('engine/engine.h')
	gen.add_include('engine/engine_plugins.h')
	gen.add_include('engine/engine_factories.h')

	if gen.get_language() == 'CPython':
		gen.insert_binding_code('''
// Add the Python interpreter module search paths to the engine default plugins search path
void InitializePluginsDefaultSearchPath() {
	if (PyObject *sys_path = PySys_GetObject("path")) {
		if (PyList_Check(sys_path)) {
			Py_ssize_t n = PyList_Size(sys_path);
			for (Py_ssize_t i = 0; i < n; ++i)
				if (PyObject *path = PyList_GetItem(sys_path, i))
					if (PyObject *tmp = PyUnicode_AsUTF8String(path))
						gs::core::plugins_default_search_paths.push_back(PyBytes_AsString(tmp));
		}
	}
}
\n''')
	elif gen.get_language() == 'Lua':
		gen.insert_code('''
#include "foundation/string.h"

// Add the Lua interpreter package.cpath to the engine default plugins search path
void InitializePluginsDefaultSearchPath(lua_State *L) {
	lua_getglobal(L, "package");
	lua_getfield(L, -1, "cpath");
	std::string package_cpath = lua_tostring(L, -1);
	lua_pop(L, 2);

	std::vector<std::string> paths = std::split(package_cpath, ";"), out;

	for (size_t i = 0; i < paths.size(); ++i) {
		std::string path = paths[i];
		std::replace(path.begin(), path.end(), '\\\\', '/');

		std::vector<std::string> elms = std::split(path, "/");
		path = "";
		for (auto &elm : elms)
			if (elm.find('?') == std::string::npos)
				path += elm + "/";

		if (path == "./")
			continue;
		if (std::ends_with(path, "loadall.dll/"))
			continue;

		out.push_back(path);
	}

	for (auto &path : out)
		gs::core::plugins_default_search_paths.push_back(path);
}
\n''')

	init_plugins_parm = ''
	if gen.get_language() == 'Lua':
		init_plugins_parm = 'L'

	gen.add_custom_init_code('''\
	gs::core::Init();
	InitializePluginsDefaultSearchPath(%s);
\n''' % init_plugins_parm)

	gen.add_custom_free_code('gs::core::Uninit();\n')

	float_ptr = gen.bind_ptr('float *', bound_name='FloatPointer')
	void_ptr = gen.bind_ptr('void *', bound_name='VoidPointer')

	gen.typedef('gs::uint', 'unsigned int')

	lib.stl.bind_future_T(gen, 'void', 'FutureVoid')
	lib.stl.bind_future_T(gen, 'bool', 'FutureBool')
	lib.stl.bind_future_T(gen, 'int', 'FutureInt')
	lib.stl.bind_future_T(gen, 'float', 'FutureFloat')

	lib.stl.bind_future_T(gen, 'gs::uint', 'FutureUInt')
	lib.stl.bind_future_T(gen, 'size_t', 'FutureSize')

	bind_std_vector(gen, gen.get_conv('int'))
	bind_std_vector(gen, gen.get_conv('gs::uint'))

	bind_std_vector(gen, gen.get_conv('int8_t'))
	bind_std_vector(gen, gen.get_conv('int16_t'))
	bind_std_vector(gen, gen.get_conv('int32_t'))
	bind_std_vector(gen, gen.get_conv('int64_t'))
	bind_std_vector(gen, gen.get_conv('uint8_t'))
	bind_std_vector(gen, gen.get_conv('uint16_t'))
	bind_std_vector(gen, gen.get_conv('uint32_t'))
	bind_std_vector(gen, gen.get_conv('uint64_t'))
	bind_std_vector(gen, gen.get_conv('float'))
	bind_std_vector(gen, gen.get_conv('double'))

	bind_std_vector(gen, gen.get_conv('std::string'))

	bind_log(gen)
	bind_binary_blob(gen)
	bind_time(gen)
	bind_task_system(gen)
	bind_math(gen)
	bind_frustum(gen)
	bind_window_system(gen)
	bind_color(gen)
	bind_font_engine(gen)
	bind_picture(gen)
	bind_document(gen)
	bind_engine(gen)
	bind_plugins(gen)
	bind_filesystem(gen)
	bind_type_value(gen)
	bind_core(gen)
	bind_create_geometry(gen)
	bind_gpu(gen)
	bind_render(gen)
	bind_iso_surface(gen)
	bind_frame_renderer(gen)
	bind_mixer(gen)
	bind_scene(gen)
	bind_input(gen)
	bind_plus(gen)
	bind_imgui(gen)
	bind_extras(gen)

	gen.finalize()
	return gen.get_output()


parser = argparse.ArgumentParser(description='Harfang API binding script')
parser.add_argument('--lua', help='Bind to Lua 5.2+', action="store_true")
parser.add_argument('--cpython', help='Bind to CPython', action="store_true")
parser.add_argument('--out', help='Path to output generated files', required=True)
args = parser.parse_args()


def output_binding(gen):
	hdr, src = bind_gs(gen)

	with open('%s/bind_harfang_%s.h' % (args.out, gen.get_language()), mode='w', encoding='utf-8') as f:
		f.write(hdr)
	with open('%s/bind_harfang_%s.cpp' % (args.out, gen.get_language()), mode='w', encoding='utf-8') as f:
		f.write(src)


if args.cpython:
	output_binding(lang.cpython.CPythonGenerator())

if args.lua:
	output_binding(lang.lua.LuaGenerator())
