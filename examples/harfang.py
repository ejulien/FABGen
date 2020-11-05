# This is the Harfang Fabgen script used to generate bindings for the CPython and Lua languages.

import lang.cpython

import lib.std
import lib.stl
import lib

import copy


def check_bool_rval_lambda(gen, msg):
	return lambda rvals, ctx: 'if (!%s) {\n%s}\n' % (rvals[0], gen.proxy_call_error(msg, ctx))


def route_lambda(name):
	return lambda args: '%s(%s);' % (name, ', '.join(args))


def bind_std_vector(gen, T_conv):
	if gen.get_language() == 'CPython':
		PySequence_T_type = 'PySequenceOf%s' % T_conv.bound_name.title()
		gen.bind_type(lib.cpython.stl.PySequenceToStdVectorConverter(PySequence_T_type, T_conv))
	elif gen.get_language() == 'Lua':
		LuaTable_T_type = 'LuaTableOf%s' % T_conv.bound_name.title()
		gen.bind_type(lib.lua.stl.LuaTableToStdVectorConverter(LuaTable_T_type, T_conv))
	
	conv = gen.begin_class('std::vector<%s>' % T_conv.ctype, bound_name='%sList' % T_conv.bound_name.title(), features={'sequence': lib.std.VectorSequenceFeature(T_conv)})
	if gen.get_language() == 'CPython':
		gen.bind_constructor(conv, ['?%s sequence' % PySequence_T_type])
	elif gen.get_language() == 'Lua':
		gen.bind_constructor(conv, ['?%s sequence' % LuaTable_T_type])

	gen.bind_method(conv, 'push_back', 'void', ['%s v' % T_conv.ctype])
	gen.bind_method(conv, 'size', 'size_t', [])
	gen.bind_method(conv, 'at', repr(T_conv.ctype), ['int idx'])

	gen.end_class(conv)
	return conv


def expand_std_vector_proto(gen, protos):
	prefix = {
		'CPython' : 'PySequenceOf',
		'Lua' : 'LuaTableOf'
	}
	name_prefix = {
		'CPython' : 'SequenceOf',
		'Lua' : 'TableOf',
		'Go' : 'SliceOf'
	}
	
	if gen.get_language() not in prefix:
		return protos

	expanded_protos = []
	for proto in protos:
		expanded = []
		add_expanded = False
		for arg in proto[1]:
			carg = gen.parse_named_ctype(arg)
			conv = gen.select_ctype_conv(carg.ctype)
			has_sequence = ('sequence' in conv._features) if conv is not None else False
			if has_sequence:
				add_expanded = True
				seq = conv._features['sequence']
				arg = '%s%s %s_%s' % (prefix[gen.get_language()], seq.wrapped_conv.bound_name, name_prefix[gen.get_language()], carg.name)
			else:	
				expanded.append(arg)
		if add_expanded:
			expanded_protos.append((proto[0], expanded, copy.deepcopy(proto[2])))

	return protos + expanded_protos


def bind_task_system(gen):
	gen.add_include('foundation/task_system.h')

	gen.insert_binding_code('''
static void _CreateWorkers() { hg::g_task_system.get().create_workers(); }
static void _DeleteWorkers() { hg::g_task_system.get().delete_workers(); }
''')

	gen.bind_function('CreateWorkers', 'void', {'route': route_lambda('_CreateWorkers')})
	gen.bind_function('DeleteWorkers', 'void', {'route': route_lambda('_DeleteWorkers')})


def bind_log(gen):
	gen.add_include('foundation/log.h')

	gen.bind_named_enum('hg::LogLevel', ['LogMessage', 'LogWarning', 'LogError', 'LogDebug', 'LogAll'], storage_type='uint32_t')

	gen.bind_function('hg::SetLogLevel', 'void', ['hg::LogLevel mask'])
	gen.bind_function('hg::SetLogIsDetailed', 'void', ['bool is_detailed'])

	gen.bind_function('hg::FlushLog', 'void', [])


def bind_binary_data(gen):
	gen.add_include('foundation/binary_data.h')

	binary_data = gen.begin_class('hg::BinaryData')

	gen.bind_constructor_overloads(binary_data, [
		([], []),
		(['const hg::BinaryData &data'], [])
	])

	gen.bind_method(binary_data, 'GetDataSize', 'size_t', [])

	gen.bind_method(binary_data, 'GetCursor', 'size_t', [])
	gen.bind_method(binary_data, 'SetCursor', 'void', ['size_t position'])

	gen.bind_method(binary_data, 'GetCursorPtr', 'const char *', [])
	gen.bind_method(binary_data, 'GetDataSizeAtCursor', 'size_t', [])

	gen.bind_method(binary_data, 'Reset', 'void', [])

	gen.bind_method(binary_data, 'Commit', 'void', ['size_t size'])
	gen.bind_method(binary_data, 'Grow', 'void', ['size_t size'])
	gen.bind_method(binary_data, 'Skip', 'void', ['size_t size'])

	def bind_write(type, alias):
		# unit write
		gen.bind_method(binary_data, 'Write<%s>' % type, 'void', ['const %s &v' % type], bound_name='Write%s' % alias)

		# batch write
		gen.insert_binding_code('''
static void _BinaryData_Write%ss(hg::BinaryData *data, const std::vector<%s> &vs) {
	for (auto &v : vs)
		data->Write<%s>(v);
}
''' % (alias, type, type))

		features = {'route': lambda args: '_BinaryData_Write%ss(%s);' % (alias, ', '.join(args))}

		protos = [('void', ['const std::vector<%s> &vs' % type], features)]
		gen.bind_method_overloads(binary_data, 'Write%ss' % alias, expand_std_vector_proto(gen, protos))

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
		gen.bind_method(binary_data, 'WriteAt<%s>' % type, 'void', ['const %s &v' % type, 'size_t position'], bound_name='Write%sAt' % alias)

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

	gen.bind_method(binary_data, 'Free', 'void', [])

	gen.end_class(binary_data)

	#
	gen.bind_function('BinaryDataBlur3d', 'void', ['hg::BinaryData &data', 'uint32_t width', 'uint32_t height', 'uint32_t depth'])


def bind_task_system(gen):
	gen.add_include('foundation/task.h')

	gen.typedef('hg::task_affinity', 'char')
	gen.typedef('hg::task_priority', 'char')


def bind_time(gen):
	gen.add_include('foundation/time.h')

	gen.typedef('hg::time_ns', 'int64_t')

	gen.bind_function('hg::time_to_sec_f', 'float', ['hg::time_ns t'])
	gen.bind_function('hg::time_to_ms_f', 'float', ['hg::time_ns t'])
	gen.bind_function('hg::time_to_us_f', 'float', ['hg::time_ns t'])

	gen.bind_function('hg::time_to_day', 'int64_t', ['hg::time_ns t'])
	gen.bind_function('hg::time_to_hour', 'int64_t', ['hg::time_ns t'])
	gen.bind_function('hg::time_to_min', 'int64_t', ['hg::time_ns t'])
	gen.bind_function('hg::time_to_sec', 'int64_t', ['hg::time_ns t'])
	gen.bind_function('hg::time_to_ms', 'int64_t', ['hg::time_ns t'])
	gen.bind_function('hg::time_to_us', 'int64_t', ['hg::time_ns t'])
	gen.bind_function('hg::time_to_ns', 'int64_t', ['hg::time_ns t'])

	gen.bind_function('hg::time_from_sec_f', 'hg::time_ns', ['float sec'])
	gen.bind_function('hg::time_from_ms_f', 'hg::time_ns', ['float ms'])
	gen.bind_function('hg::time_from_us_f', 'hg::time_ns', ['float us'])

	gen.bind_function('hg::time_from_day', 'hg::time_ns', ['int64_t day'])
	gen.bind_function('hg::time_from_hour', 'hg::time_ns', ['int64_t hour'])
	gen.bind_function('hg::time_from_min', 'hg::time_ns', ['int64_t min'])
	gen.bind_function('hg::time_from_sec', 'hg::time_ns', ['int64_t sec'])
	gen.bind_function('hg::time_from_ms', 'hg::time_ns', ['int64_t ms'])
	gen.bind_function('hg::time_from_us', 'hg::time_ns', ['int64_t us'])
	gen.bind_function('hg::time_from_ns', 'hg::time_ns', ['int64_t ns'])

	gen.bind_function('hg::time_now', 'hg::time_ns', [])

	gen.bind_function('hg::time_to_string', 'std::string', ['hg::time_ns t'])

	lib.stl.bind_future_T(gen, 'hg::time_ns', 'FutureTime')


def bind_input(gen):
	gen.add_include('platform/input_system.h')

	gen.bind_named_enum('hg::InputDeviceType', [
		'InputDeviceAny', 'InputDeviceKeyboard', 'InputDeviceMouse', 'InputDevicePad', 'InputDeviceTouch', 'InputDeviceHMD', 'InputDeviceController'
	])

	gen.bind_named_enum('hg::Key', [
		'KeyLShift', 'KeyRShift', 'KeyLCtrl', 'KeyRCtrl', 'KeyLAlt', 'KeyRAlt', 'KeyLWin', 'KeyRWin',
		'KeyTab', 'KeyCapsLock', 'KeySpace', 'KeyBackspace', 'KeyInsert', 'KeySuppr', 'KeyHome', 'KeyEnd', 'KeyPageUp', 'KeyPageDown',
		'KeyUp', 'KeyDown', 'KeyLeft', 'KeyRight',
		'KeyEscape',
		'KeyF1', 'KeyF2', 'KeyF3', 'KeyF4', 'KeyF5', 'KeyF6', 'KeyF7', 'KeyF8', 'KeyF9', 'KeyF10', 'KeyF11', 'KeyF12',
		'KeyPrintScreen', 'KeyScrollLock', 'KeyPause', 'KeyNumLock', 'KeyReturn',
		'Key0', 'Key1', 'Key2', 'Key3', 'Key4', 'Key5', 'Key6', 'Key7', 'Key8', 'Key9',
		'KeyNumpad0', 'KeyNumpad1', 'KeyNumpad2', 'KeyNumpad3', 'KeyNumpad4', 'KeyNumpad5', 'KeyNumpad6', 'KeyNumpad7', 'KeyNumpad8', 'KeyNumpad9',
		'KeyAdd', 'KeySub', 'KeyMul', 'KeyDiv', 'KeyEnter',
		'KeyA', 'KeyB', 'KeyC', 'KeyD', 'KeyE', 'KeyF', 'KeyG', 'KeyH', 'KeyI', 'KeyJ', 'KeyK', 'KeyL', 'KeyM', 'KeyN', 'KeyO', 'KeyP', 'KeyQ', 'KeyR', 'KeyS', 'KeyT', 'KeyU', 'KeyV', 'KeyW', 'KeyX', 'KeyY', 'KeyZ',
		'KeyLast'
	])

	gen.bind_named_enum('hg::Button', [
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

	gen.bind_named_enum('hg::AnalogInput', [
		'InputAxisX', 'InputAxisY', 'InputAxisZ', 'InputAxisS', 'InputAxisT', 'InputAxisR',
		'InputRotX', 'InputRotY', 'InputRotZ', 'InputRotS', 'InputRotT', 'InputRotR',
		'InputButton0', 'InputButton1', 'InputButton2', 'InputButton3', 'InputButton4', 'InputButton5', 'InputButton6', 'InputButton7', 'InputButton8', 'InputButton9', 'InputButton10', 'InputButton11', 'InputButton12', 'InputButton13', 'InputButton14', 'InputButton15',
		'InputLast'
	])

	gen.bind_named_enum('hg::InputDeviceEffect', ['InputDeviceVibrate', 'InputDeviceVibrateLeft', 'InputDeviceVibrateRight', 'InputDeviceConstantForce'])
	gen.bind_named_enum('hg::InputDeviceMatrix', ['InputDeviceMatrixHead'])

	# hg::InputDevice
	input_device = gen.begin_class('hg::InputDevice', bound_name='InputDevice_nobind', noncopyable=True, nobind=True)
	gen.end_class(input_device)

	shared_input_device = gen.begin_class('std::shared_ptr<hg::InputDevice>', bound_name='InputDevice', features={'proxy': lib.stl.SharedPtrProxyFeature(input_device)})

	gen.bind_method(shared_input_device, 'GetType', 'hg::InputDeviceType', [], ['proxy'])

	gen.bind_method(shared_input_device, 'Update', 'void', [], ['proxy'])

	gen.bind_method(shared_input_device, 'IsDown', 'bool', ['hg::Key key'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasDown', 'bool', ['hg::Key key'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasPressed', 'bool', ['hg::Key key'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasReleased', 'bool', ['hg::Key key'], ['proxy'])

	gen.bind_method(shared_input_device, 'IsButtonDown', 'bool', ['hg::Button button'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasButtonDown', 'bool', ['hg::Button button'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasButtonPressed', 'bool', ['hg::Button button'], ['proxy'])
	gen.bind_method(shared_input_device, 'WasButtonReleased', 'bool', ['hg::Button button'], ['proxy'])

	gen.bind_method(shared_input_device, 'GetValue', 'float', ['hg::AnalogInput input'], ['proxy'])
	gen.bind_method(shared_input_device, 'GetLastValue', 'float', ['hg::AnalogInput input'], ['proxy'])
	gen.bind_method(shared_input_device, 'GetValueRange', 'bool', ['hg::AnalogInput input', 'float &min', 'float &max'], {'proxy': None, 'arg_out': ['min', 'max']})
	gen.bind_method(shared_input_device, 'GetDelta', 'float', ['hg::AnalogInput input'], ['proxy'])

	gen.bind_method(shared_input_device, 'GetMatrix', 'hg::Matrix4', ['hg::InputDeviceMatrix mtx'], ['proxy'])

	gen.bind_method(shared_input_device, 'SetValue', 'bool', ['hg::AnalogInput input', 'float value'], ['proxy'])
	gen.bind_method(shared_input_device, 'SetEffect', 'bool', ['hg::InputDeviceEffect effect', 'float value'], ['proxy'])

	gen.bind_method(shared_input_device, 'IsConnected', 'bool', [], ['proxy'])

	gen.end_class(shared_input_device)

	# hg::InputSystem
	input_system = gen.begin_class('hg::InputSystem', noncopyable=True)

	gen.bind_method(input_system, 'Update', 'void', [])

	gen.bind_method(input_system, 'GetDevices', 'std::vector<std::string>', [])
	gen.bind_method(input_system, 'GetDevice', 'std::shared_ptr<hg::InputDevice>', ['const std::string &name'], {'check_rval': check_bool_rval_lambda(gen, 'Device not found')})

	gen.end_class(input_system)

	gen.insert_binding_code('static hg::InputSystem &GetInputSystem() { return hg::g_input_system.get(); }\n\n')
	gen.bind_function('GetInputSystem', 'hg::InputSystem &', [])


def bind_platform(gen):
	gen.add_include('platform/platform.h')
	
	gen.bind_function('hg::OpenFolderDialog', 'bool', ['const std::string &title', 'std::string &folder_name', '?const std::string &initial_dir'], {'arg_in_out': ['folder_name']})
	gen.bind_function('hg::OpenFileDialog', 'bool', ['const std::string &title', 'const std::string &filter', 'std::string &file_name', '?const std::string &initial_dir'], {'arg_in_out': ['file_name']})
	gen.bind_function('hg::SaveFileDialog', 'bool', ['const std::string &title', 'const std::string &filter', 'std::string &file_name', '?const std::string &initial_dir'], {'arg_in_out': ['file_name']})


def bind_engine(gen):
	gen.add_include('engine/init.h')
	gen.add_include('engine/engine.h')

	gen.bind_function('hg::GetExecutablePath', 'std::string', [])

	gen.bind_function('hg::EndFrame', 'void', [])

	gen.bind_function('hg::GetLastFrameDuration', 'hg::time_ns', [])
	gen.bind_function('hg::GetLastFrameDurationSec', 'float', [])
	gen.bind_function('hg::ResetLastFrameDuration', 'void', [])

	gen.bind_function('hg::_DebugHalt', 'void', [])

	gen.add_include('foundation/projection.h')

	gen.bind_function('hg::ZoomFactorToFov', 'float', ['float zoom_factor'])
	gen.bind_function('hg::FovToZoomFactor', 'float', ['float fov'])

	gen.bind_function('hg::ComputeOrthographicProjectionMatrix', 'hg::Matrix44', ['float znear', 'float zfar', 'float size', 'const hg::tVector2<float> &aspect_ratio'])
	gen.bind_function('hg::ComputePerspectiveProjectionMatrix', 'hg::Matrix44', ['float znear', 'float zfar', 'float zoom_factor', 'const hg::tVector2<float> &aspect_ratio'])


def bind_plugins(gen):
	gen.bind_function_overloads('hg::LoadPlugins', [('uint32_t', [], []), ('uint32_t', ['const std::string &path'], [])])
	gen.bind_function('hg::UnloadPlugins', 'void', [])


def bind_window_system(gen):
	gen.add_include('platform/window_system.h')

	# hg::Surface
	surface = gen.begin_class('hg::Surface')
	gen.end_class(surface)

	# hg::Monitor
	monitor = gen.begin_class('hg::Monitor')
	gen.end_class(monitor)
	bind_std_vector(gen, monitor)

	gen.bind_function('hg::GetMonitorRect', 'hg::Rect<int>', ['const hg::Monitor &monitor'])
	gen.bind_function('hg::IsPrimaryMonitor', 'bool', ['const hg::Monitor &monitor'])

	gen.bind_function('hg::GetMonitors', 'std::vector<hg::Monitor>', [])

	# hg::Window
	gen.bind_named_enum('hg::Window::Visibility', ['Windowed', 'Undecorated', 'Fullscreen', 'Hidden', 'FullscreenMonitor1', 'FullscreenMonitor2', 'FullscreenMonitor3'])

	window = gen.begin_class('hg::Window')
	gen.end_class(window)

	gen.bind_function_overloads('hg::NewWindow', [
		('hg::Window', ['int width', 'int height'], []),
		('hg::Window', ['int width', 'int height', 'int bpp'], []),
		('hg::Window', ['int width', 'int height', 'int bpp', 'hg::Window::Visibility visibility'], [])
	])
	gen.bind_function('hg::NewWindowFrom', 'hg::Window', ['void *handle'])

	gen.bind_function('hg::GetWindowHandle', 'void *', ['const hg::Window &window'])
	gen.bind_function('hg::UpdateWindow', 'bool', ['const hg::Window &window'])
	gen.bind_function('hg::DestroyWindow', 'bool', ['const hg::Window &window'])

	gen.bind_function('hg::GetWindowClientSize', 'bool', ['const hg::Window &window', 'int &width', 'int &height'], features={'arg_out': ['width', 'height']})
	gen.bind_function('hg::SetWindowClientSize', 'bool', ['const hg::Window &window', 'int width', 'int height'])

	gen.bind_function('hg::GetWindowTitle', 'bool', ['const hg::Window &window', 'std::string &title'], features={'arg_out': ['title']})
	gen.bind_function('hg::SetWindowTitle', 'bool', ['const hg::Window &window', 'const std::string &title'])

	gen.bind_function('hg::WindowHasFocus', 'bool', ['const hg::Window &window'])
	gen.bind_function('hg::GetWindowInFocus', 'hg::Window', [])

	gen.bind_function('hg::GetWindowPos', 'hg::tVector2<int>', ['const hg::Window &window'])
	gen.bind_function('hg::SetWindowPos', 'bool', ['const hg::Window &window', 'const hg::tVector2<int> position'])

	gen.bind_function('hg::IsWindowOpen', 'bool', ['const hg::Window &window'])

	lib.stl.bind_future_T(gen, 'hg::Window', 'FutureWindow')
	lib.stl.bind_future_T(gen, 'hg::Surface', 'FutureSurface')


def bind_type_value(gen):
	gen.add_include('foundation/reflection.h')
	gen.add_include('foundation/base_type_reflection.h')

	bool_conv = gen.get_conv('bool')
	int_conv = gen.get_conv('int')
	float_conv = gen.get_conv('float')
	string_conv = gen.get_conv('std::string')

	if gen.get_language() == 'CPython':
		class PythonTypeValueConverter(lang.cpython.PythonTypeConverterCommon):
			def get_type_glue(self, gen, module_name):
				check = '''\
bool %s(PyObject *o) {
	using namespace hg;
	return true;
}
''' % self.check_func

				to_c = '''\
void %s(PyObject *o, void *obj) {
	using namespace hg;

	TypeValue &value = *(TypeValue *)obj;

	if (%s(o)) {
		bool v;
		%s(o, &v);
		value = MakeTypeValue(v);
	} else if (%s(o)) {
		int v;
		%s(o, &v);
		value = MakeTypeValue(v);
	} else if (%s(o)) {
		float v;
		%s(o, &v);
		value = MakeTypeValue(v);
	} else if (%s(o)) {
		std::string v;
		%s(o, &v);
		value = MakeTypeValue(v);
	} else if (wrapped_Object *w = cast_to_wrapped_Object_safe(o)) {
		auto info = %s(w->type_tag);
		if (!info) {
			PyErr_SetString(PyExc_RuntimeError, "unsupported type (from CPython)");
			return;
		}

		auto obj_type = g_type_registry.get().GetType(info->c_type);
		if (!obj_type) {
			PyErr_SetString(PyExc_RuntimeError, "type unknown to reflection system (from CPython)");
			return;
		}

		void *obj;
		info->to_c(o, &obj);
		value.Set(obj_type, obj);
	}
}
''' % (	self.to_c_func,
		bool_conv.check_func, bool_conv.to_c_func,
		int_conv.check_func, int_conv.to_c_func,
		float_conv.check_func, float_conv.to_c_func,
		string_conv.check_func, string_conv.to_c_func,
		gen.apply_api_prefix('get_bound_type_info'))

				from_c = '''\
PyObject *%s(void *obj, OwnershipPolicy policy) {
	using namespace hg;

	TypeValue &value = *(TypeValue *)obj;

	static Type *bool_type = g_type_registry.get().GetType("Bool");
	static Type *int_type = g_type_registry.get().GetType("Int");
	static Type *float_type = g_type_registry.get().GetType("Float");
	static Type *string_type = g_type_registry.get().GetType("String");

	const Type *type = value.GetType();

	if (type == bool_type) {
		return %s(value.GetData(), policy);
	} else if (type == int_type) {
		return %s(value.GetData(), policy);
	} else if (type == float_type) {
		return %s(value.GetData(), policy);
	} else if (type == string_type) {
		return %s(value.GetData(), policy);
	} else if (auto info = %s(type->GetCppName().data())) {
		return info->from_c(value.GetData(), Copy);
	} else {
		PyErr_SetString(PyExc_RuntimeError, "unsupported type (to CPython)");
	}
	return NULL;
}
''' % (	self.from_c_func,
		bool_conv.from_c_func,
		int_conv.from_c_func,
		float_conv.from_c_func,
		string_conv.from_c_func,
		gen.apply_api_prefix('get_c_type_info'))

				return check + to_c + from_c

		type_value = gen.bind_type(PythonTypeValueConverter('hg::TypeValue'))
		
	elif gen.get_language() == 'Lua':
		class LuaTypeValueConverter(lang.lua.LuaTypeConverterCommon):
			def get_type_glue(self, gen, module_name):
				check = '''\
bool %s(lua_State *L, int idx) {
	using namespace hg;
	return true;
}
''' % self.check_func

				to_c = '''\
void %s(lua_State *L, int idx, void *obj) {
	using namespace hg;

	TypeValue &value = *(TypeValue *)obj;

	static Type
		*none_type = g_type_registry.get().GetType<none>(),
		*bool_type = g_type_registry.get().GetType<bool>(),
		*int_type = g_type_registry.get().GetType<int>(),
		*float_type = g_type_registry.get().GetType<float>(),	
		*string_type = g_type_registry.get().GetType<std::string>();

	if (lua_isnil(L, idx)) {
		none v;
		value.Set(none_type, &v);
	} else if (lua_isboolean(L, idx)) {
		bool v = lua_toboolean(L, idx);
		value.Set(bool_type, &v);
	} else if (lua_isinteger(L, idx)) {
		int v = (int)lua_tointeger(L, idx);
		value.Set(int_type, &v);
	} else if (lua_isnumber(L, idx)) {
		float v = (float)lua_tonumber(L, idx);
		value.Set(float_type, &v);
	} else if (lua_isstring(L, idx)) {
		std::string v(lua_tostring(L, idx));
		value.Set(string_type, &v);
	} else if (auto type_tag = %s(L, idx)) {
		auto info = %s(type_tag);
		if (!info) {
			luaL_error(L, "Unsupported type (from Lua)");
			return;
		}

		auto obj_type = g_type_registry.get().GetType(info->c_type);
		if (!obj_type) {
			luaL_error(L, "Type unknown to reflection system (from Lua)");
			return;
		}

		void *obj;
		info->to_c(L, idx, &obj);
		value.Set(obj_type, obj);
	} else {
		__ASSERT_ALWAYS__("Unsupported value type (from Lua)");
	}
}
''' % (self.to_c_func, gen.apply_api_prefix('get_wrapped_object_type_tag'), gen.apply_api_prefix('get_bound_type_info'))

				from_c = '''\
int %s(lua_State *L, void *obj, OwnershipPolicy) {
	using namespace hg;

	TypeValue &value = *(TypeValue *)obj;

	static Type
		*none_type = g_type_registry.get().GetType<none>(),
		*bool_type = g_type_registry.get().GetType<bool>(),
		*int_type = g_type_registry.get().GetType<int>(),
		*float_type = g_type_registry.get().GetType<float>(),	
		*string_type = g_type_registry.get().GetType<std::string>();

	const Type *type = value.GetType();

	if (type == nullptr) {
		return 0;
	} else if (type == none_type) {
		lua_pushnil(L);
	} else if (type == bool_type) {
		lua_pushboolean(L, value.Cast<bool>());
	} else if (type == int_type) {
		lua_pushinteger(L, value.Cast<int>());
	} else if (type == float_type) {
		lua_pushnumber(L, value.Cast<float>());
	} else if (type == string_type) {
		lua_pushstring(L, value.Cast<std::string>().data());
	} else if (auto info = %s(type->GetCppName().data())) {
		return info->from_c(L, value.GetData(), Copy);
	} else {
		__ASSERT_ALWAYS__("Unsupported value type (to Lua)");
		return 0;
	}
	return 1;
}
''' % (self.from_c_func, gen.apply_api_prefix('get_c_type_info'))

				return check + to_c + from_c

		type_value = gen.bind_type(LuaTypeValueConverter('hg::TypeValue'))
	else:
		type_value = gen.begin_class('hg::TypeValue')
		gen.end_class(type_value)

	bind_std_vector(gen, type_value)


def bind_core(gen):
	# hg::Shader
	gen.add_include('engine/shader.h')

	gen.bind_named_enum('hg::ShaderType', ['ShaderNoType', 'ShaderInt', 'ShaderUInt', 'ShaderFloat', 'ShaderVector2', 'ShaderVector3', 'ShaderVector4', 'ShaderMatrix3', 'ShaderMatrix4', 'ShaderTexture2D', 'ShaderTexture3D', 'ShaderTextureCube', 'ShaderTextureShadow', 'ShaderTextureExternal'], storage_type='uint8_t')
	gen.bind_named_enum('hg::ShaderTypePrecision', ['ShaderDefaultPrecision', 'ShaderLowPrecision', 'ShaderMediumPrecision', 'ShaderHighPrecision'], storage_type='uint8_t')

	gen.bind_named_enum('hg::VertexAttribute::Semantic', ['Position', 'Normal', 'UV0', 'UV1', 'UV2', 'UV3', 'Color0', 'Color1', 'Color2', 'Color3', 'Tangent', 'Bitangent', 'BoneIndex', 'BoneWeight', 'InstanceModelMatrix', 'InstancePreviousModelMatrix', 'InstancePickingId'], storage_type='uint8_t', prefix='Vertex', bound_name='VertexSemantic')

	gen.bind_named_enum('hg::TextureUV', ['TextureUVClamp', 'TextureUVRepeat', 'TextureUVMirror', 'TextureUVCount'], storage_type='uint8_t')
	gen.bind_named_enum('hg::TextureFilter', ['TextureFilterNearest', 'TextureFilterLinear', 'TextureFilterTrilinear', 'TextureFilterAnisotropic', 'TextureFilterCount'], storage_type='uint8_t')

	shader = gen.begin_class('hg::Shader', bound_name='Shader_nobind', noncopyable=True, nobind=True)
	gen.end_class(shader)

	shared_shader = gen.begin_class('std::shared_ptr<hg::Shader>', bound_name='Shader', features={'proxy': lib.stl.SharedPtrProxyFeature(shader)})
	gen.bind_members(shared_shader, ['std::string name', 'uint8_t surface_attributes', 'uint8_t surface_draw_state', 'uint8_t alpha_threshold'], ['proxy'])
	gen.end_class(shared_shader)

	gen.bind_named_enum('hg::ShaderVariable::Semantic', [
		'Clock', 'Viewport', 'TechniqueIsForward', 'FxScale', 'InverseInternalResolution', 'InverseViewportSize', 'AmbientColor', 'FogColor', 'FogState', 'DepthBuffer', 'FrameBuffer', 'GBuffer0', 'GBuffer1', 'GBuffer2', 'GBuffer3',
		'ViewVector', 'ViewPosition', 'ViewState',
		'ModelMatrix', 'InverseModelMatrix', 'NormalMatrix', 'PreviousModelMatrix', 'ViewMatrix', 'InverseViewMatrix', 'ModelViewMatrix', 'NormalViewMatrix', 'ProjectionMatrix', 'ViewProjectionMatrix', 'ModelViewProjectionMatrix', 'InverseViewProjectionMatrix', 'InverseViewProjectionMatrixAtOrigin',
		'LightState', 'LightDiffuseColor', 'LightSpecularColor', 'LightShadowColor', 'LightViewPosition', 'LightViewDirection', 'LightShadowMatrix', 'InverseShadowMapSize', 'LightShadowMap', 'LightPSSMSliceDistance', 'ViewToLightMatrix', 'LightProjectionMap',
		'BoneMatrix', 'PreviousBoneMatrix',
		'PickingId',
		'TerrainHeightmap', 'TerrainHeightmapSize', 'TerrainSize', 'TerrainPatchOrigin', 'TerrainPatchSize'
	], storage_type='uint8_t', prefix='Shader', bound_name='ShaderSemantic')

	shader_variable = gen.begin_class('hg::ShaderVariable')
	gen.bind_members(shader_variable, ['std::string name', 'std::string hint', 'hg::ShaderType type', 'hg::ShaderTypePrecision precision', 'uint8_t array_size'])
	gen.end_class(shader_variable)

	# hg::TextureUnitConfig
	tex_unit_cfg = gen.begin_class('hg::TextureUnitConfig')
	gen.bind_constructor_overloads(tex_unit_cfg, [
		([], []),
		(['hg::TextureUV wrap_u', 'hg::TextureUV wrap_v', 'hg::TextureFilter min_filter', 'hg::TextureFilter mag_filter'], []),
	])
	gen.bind_comparison_op(tex_unit_cfg, '==', ['const hg::TextureUnitConfig &config'])
	gen.bind_members(tex_unit_cfg, ['hg::TextureUV wrap_u:', 'hg::TextureUV wrap_v:', 'hg::TextureFilter min_filter:', 'hg::TextureFilter mag_filter:'])
	gen.end_class(tex_unit_cfg)

	# hg::ShaderValue
	shader_value = gen.begin_class('hg::ShaderValue')
	gen.bind_members(shader_value, ['std::string path', 'hg::TextureUnitConfig tex_unit_cfg'])

	gen.insert_binding_code('''
static float _ShaderValue_GetFloat(hg::ShaderValue *m) { return  m->fv[0]; }
static void _ShaderValue_SetFloat(hg::ShaderValue *m, float v) { m->fv[0] = v; }
static void _ShaderValue_GetFloat2(hg::ShaderValue *m, float &v0, float &v1) { v0 = m->fv[0]; v1 = m->fv[1]; }
static void _ShaderValue_SetFloat2(hg::ShaderValue *m, float v0, float v1) { m->fv[0] = v0; m->fv[1] = v1; }
static void _ShaderValue_GetFloat3(hg::ShaderValue *m, float &v0, float &v1, float &v2) { v0 = m->fv[0]; v1 = m->fv[1]; v2 = m->fv[2]; }
static void _ShaderValue_SetFloat3(hg::ShaderValue *m, float v0, float v1, float v2) { m->fv[0] = v0; m->fv[1] = v1; m->fv[2] = v2; }
static void _ShaderValue_GetFloat4(hg::ShaderValue *m, float &v0, float &v1, float &v2, float &v3) { v0 = m->fv[0]; v1 = m->fv[1]; v2 = m->fv[2]; v3 = m->fv[3]; }
static void _ShaderValue_SetFloat4(hg::ShaderValue *m, float v0, float v1, float v2, float v3) { m->fv[0] = v0; m->fv[1] = v1; m->fv[2] = v2; m->fv[3] = v3; }

static int32_t _ShaderValue_GetInt(hg::ShaderValue *m) { return  m->iv[0]; }
static void _ShaderValue_SetInt(hg::ShaderValue *m, int32_t v) { m->iv[0] = v; }
static void _ShaderValue_GetInt2(hg::ShaderValue *m, int32_t &v0, int32_t &v1) { v0 = m->iv[0]; v1 = m->iv[1]; }
static void _ShaderValue_SetInt2(hg::ShaderValue *m, int32_t v0, int32_t v1) { m->iv[0] = v0; m->iv[1] = v1; }
static void _ShaderValue_GetInt3(hg::ShaderValue *m, int32_t &v0, int32_t &v1, int32_t &v2) { v0 = m->iv[0]; v1 = m->iv[1]; v2 = m->iv[2]; }
static void _ShaderValue_SetInt3(hg::ShaderValue *m, int32_t v0, int32_t v1, int32_t v2) { m->iv[0] = v0; m->iv[1] = v1; m->iv[2] = v2; }
static void _ShaderValue_GetInt4(hg::ShaderValue *m, int32_t &v0, int32_t &v1, int32_t &v2, int32_t &v3) { v0 = m->iv[0]; v1 = m->iv[1]; v2 = m->iv[2]; v3 = m->iv[3]; }
static void _ShaderValue_SetInt4(hg::ShaderValue *m, int32_t v0, int32_t v1, int32_t v2, int32_t v3) { m->iv[0] = v0; m->iv[1] = v1; m->iv[2] = v2; m->iv[3] = v3; }

static uint32_t _ShaderValue_GetUnsigned(hg::ShaderValue *m) { return  m->uv[0]; }
static void _ShaderValue_SetUnsigned(hg::ShaderValue *m, uint32_t v) { m->uv[0] = v; }
static void _ShaderValue_GetUnsigned2(hg::ShaderValue *m, uint32_t &v0, uint32_t &v1) { v0 = m->uv[0]; v1 = m->uv[1]; }
static void _ShaderValue_SetUnsigned2(hg::ShaderValue *m, uint32_t v0, uint32_t v1) { m->uv[0] = v0; m->uv[1] = v1; }
static void _ShaderValue_GetUnsigned3(hg::ShaderValue *m, uint32_t &v0, uint32_t &v1, uint32_t &v2) { v0 = m->uv[0]; v1 = m->uv[1]; v2 = m->uv[2]; }
static void _ShaderValue_SetUnsigned3(hg::ShaderValue *m, uint32_t v0, uint32_t v1, uint32_t v2) { m->uv[0] = v0; m->uv[1] = v1; m->uv[2] = v2; }
static void _ShaderValue_GetUnsigned4(hg::ShaderValue *m, uint32_t &v0, uint32_t &v1, uint32_t &v2, uint32_t &v3) { v0 = m->uv[0]; v1 = m->uv[1]; v2 = m->uv[2]; v3 = m->uv[3]; }
static void _ShaderValue_SetUnsigned4(hg::ShaderValue *m, uint32_t v0, uint32_t v1, uint32_t v2, uint32_t v3) { m->uv[0] = v0; m->uv[1] = v1; m->uv[2] = v2; m->uv[3] = v3; }
''')

	gen.bind_method(shader_value, 'GetFloat', 'float', [], {'route': route_lambda('_ShaderValue_GetFloat')})
	gen.bind_method(shader_value, 'SetFloat', 'void', ['float v'], {'route': route_lambda('_ShaderValue_SetFloat')})
	gen.bind_method(shader_value, 'GetFloat2', 'void', ['float &v0', 'float &v1'], {'arg_out': ['v0', 'v1'], 'route':  route_lambda('_ShaderValue_GetFloat2')})
	gen.bind_method(shader_value, 'SetFloat2', 'void', ['float v0', 'float v1'], {'route': route_lambda('_ShaderValue_SetFloat2')})
	gen.bind_method(shader_value, 'GetFloat3', 'void', ['float &v0', 'float &v1', 'float &v2'], {'arg_out': ['v0', 'v1', 'v2'], 'route':  route_lambda('_ShaderValue_GetFloat3')})
	gen.bind_method(shader_value, 'SetFloat3', 'void', ['float v0', 'float v1', 'float v2'], {'route': route_lambda('_ShaderValue_SetFloat3')})
	gen.bind_method(shader_value, 'GetFloat4', 'void', ['float &v0', 'float &v1', 'float &v2', 'float &v3'], {'arg_out': ['v0', 'v1', 'v2', 'v3'], 'route':  route_lambda('_ShaderValue_GetFloat4')})
	gen.bind_method(shader_value, 'SetFloat4', 'void', ['float v0', 'float v1', 'float v2', 'float v3'], {'route': route_lambda('_ShaderValue_SetFloat4')})

	gen.bind_method(shader_value, 'GetInt', 'int32_t', [], {'route': route_lambda('_ShaderValue_GetInt')})
	gen.bind_method(shader_value, 'SetInt', 'void', ['int32_t v'], {'route': route_lambda('_ShaderValue_SetInt')})
	gen.bind_method(shader_value, 'GetInt2', 'void', ['int32_t &v0', 'int32_t &v1'], {'arg_out': ['v0', 'v1'], 'route':  route_lambda('_ShaderValue_GetInt2')})
	gen.bind_method(shader_value, 'SetInt2', 'void', ['int32_t v0', 'int32_t v1'], {'route': route_lambda('_ShaderValue_SetInt2')})
	gen.bind_method(shader_value, 'GetInt3', 'void', ['int32_t &v0', 'int32_t &v1', 'int32_t &v2'], {'arg_out': ['v0', 'v1', 'v2'], 'route':  route_lambda('_ShaderValue_GetInt3')})
	gen.bind_method(shader_value, 'SetInt3', 'void', ['int32_t v0', 'int32_t v1', 'int32_t v2'], {'route': route_lambda('_ShaderValue_SetInt3')})
	gen.bind_method(shader_value, 'GetInt4', 'void', ['int32_t &v0', 'int32_t &v1', 'int32_t &v2', 'int32_t &v3'], {'arg_out': ['v0', 'v1', 'v2', 'v3'], 'route':  route_lambda('_ShaderValue_GetInt4')})
	gen.bind_method(shader_value, 'SetInt4', 'void', ['int32_t v0', 'int32_t v1', 'int32_t v2', 'int32_t v3'], {'route': route_lambda('_ShaderValue_SetInt4')})

	gen.bind_method(shader_value, 'GetUnsigned', 'uint32_t', [], {'route': route_lambda('_ShaderValue_GetUnsigned')})
	gen.bind_method(shader_value, 'SetUnsigned', 'void', ['uint32_t v'], {'route': route_lambda('_ShaderValue_SetUnsigned')})
	gen.bind_method(shader_value, 'GetUnsigned2', 'void', ['uint32_t &v0', 'uint32_t &v1'], {'arg_out': ['v0', 'v1'], 'route':  route_lambda('_ShaderValue_GetUnsigned2')})
	gen.bind_method(shader_value, 'SetUnsigned2', 'void', ['uint32_t v0', 'uint32_t v1'], {'route': route_lambda('_ShaderValue_SetUnsigned2')})
	gen.bind_method(shader_value, 'GetUnsigned3', 'void', ['uint32_t &v0', 'uint32_t &v1', 'uint32_t &v2'], {'arg_out': ['v0', 'v1', 'v2'], 'route':  route_lambda('_ShaderValue_GetUnsigned3')})
	gen.bind_method(shader_value, 'SetUnsigned3', 'void', ['uint32_t v0', 'uint32_t v1', 'uint32_t v2'], {'route': route_lambda('_ShaderValue_SetUnsigned3')})
	gen.bind_method(shader_value, 'GetUnsigned4', 'void', ['uint32_t &v0', 'uint32_t &v1', 'uint32_t &v2', 'uint32_t &v3'], {'arg_out': ['v0', 'v1', 'v2', 'v3'], 'route':  route_lambda('_ShaderValue_GetUnsigned4')})
	gen.bind_method(shader_value, 'SetUnsigned4', 'void', ['uint32_t v0', 'uint32_t v1', 'uint32_t v2', 'uint32_t v3'], {'route': route_lambda('_ShaderValue_SetUnsigned4')})

	gen.end_class(shader_value)

	# hg::MaterialValue
	gen.add_include('engine/material.h')

	material_value = gen.begin_class('hg::MaterialValue')
	gen.bind_members(material_value, ['std::string name', 'hg::ShaderType type', 'std::string path', 'hg::TextureUnitConfig tex_unit_cfg'])
	gen.add_base(material_value, shader_value)
	gen.end_class(material_value)

	# hg::Material
	material = gen.begin_class('hg::Material', bound_name='Material_nobind', noncopyable=True, nobind=True)
	gen.end_class(material)

	shared_material = gen.begin_class('std::shared_ptr<hg::Material>', bound_name='Material', features={'proxy': lib.stl.SharedPtrProxyFeature(material)})
	gen.bind_constructor(shared_material, [], ['proxy'])
	gen.bind_members(shared_material, ['std::string name', 'std::string shader'], ['proxy'])
	gen.bind_method(shared_material, 'GetValue', 'hg::MaterialValue *', ['const std::string &name'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Value not found')})
	gen.bind_method(shared_material, 'AddValue', 'hg::MaterialValue *', ['const std::string &name', 'hg::ShaderType type'], ['proxy'])
	gen.end_class(shared_material)
	
	#
	gen.add_include('engine/material_serialization.h')
	gen.bind_function('hg::LoadMaterial', 'bool', ['hg::Material &mat', 'const std::string &path'])
	gen.bind_function('hg::SaveMaterial', 'bool', ['const std::shared_ptr<hg::Material> &material', 'const std::string &path', '?hg::DocumentFormat format'])
	
	# hg::Geometry
	gen.add_include('engine/geometry.h')

	geometry = gen.begin_class('hg::Geometry', bound_name='Geometry_nobind', noncopyable=True, nobind=True)
	gen.end_class(geometry)

	shared_geometry = gen.begin_class('std::shared_ptr<hg::Geometry>', bound_name='Geometry', features={'proxy': lib.stl.SharedPtrProxyFeature(geometry)})
	gen.bind_constructor(shared_geometry, [], ['proxy'])

	gen.bind_members(shared_geometry, ['std::string lod_proxy', 'float lod_distance', 'std::string shadow_proxy'], ['proxy'])

	gen.bind_method(shared_geometry, 'SetName', 'void', ['const std::string &name'], ['proxy'])
	gen.insert_binding_code('static std::string _Geometry_GetName(hg::Geometry *geometry) { return geometry->name; }')
	gen.bind_method(shared_geometry, 'GetName', 'const std::string &', [], {'proxy':None, 'route': route_lambda('_Geometry_GetName')})
	
	gen.bind_method(shared_geometry, 'GetTriangleCount', 'size_t', [], ['proxy'])

	gen.bind_method(shared_geometry, 'ComputeLocalMinMax', 'hg::MinMax', [], ['proxy'])
	#gen.bind_method(shared_geometry, 'ComputeLocalBoneMinMax', 'bool', [''], ['proxy'])

	gen.bind_method(shared_geometry, 'AllocateVertex', 'void', ['uint32_t count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocatePolygon', 'void', ['uint32_t count'], ['proxy'])

	gen.bind_method(shared_geometry, 'AllocatePolygonBinding', 'bool', [], ['proxy'])
	gen.bind_method(shared_geometry, 'ComputePolygonBindingCount', 'size_t', [], ['proxy'])

	gen.bind_method(shared_geometry, 'AllocateVertexNormal', 'void', ['uint32_t count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocateVertexTangent', 'void', ['uint32_t count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocateRgb', 'void', ['uint32_t count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocateMaterialTable', 'void', ['uint32_t count'], ['proxy'])
	gen.bind_method(shared_geometry, 'AllocateUVChannels', 'bool', ['uint32_t channel_count', 'uint32_t uv_per_channel'], ['proxy'])

	gen.bind_method(shared_geometry, 'GetVertexCount', 'size_t', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetPolygonCount', 'size_t', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetVertexNormalCount', 'size_t', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetVertexTangentCount', 'size_t', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetRgbCount', 'size_t', [], ['proxy'])
	gen.bind_method(shared_geometry, 'GetUVCount', 'int', [], ['proxy'])

	gen.bind_method(shared_geometry, 'GetVertex', 'hg::Vector3', ['uint32_t index'], ['proxy'])
	gen.bind_method(shared_geometry, 'SetVertex', 'bool', ['uint32_t index', 'const hg::Vector3 &vertex'], ['proxy'])
	gen.bind_method(shared_geometry, 'GetVertexNormal', 'hg::Vector3', ['uint32_t index'], ['proxy'])
	gen.bind_method(shared_geometry, 'SetVertexNormal', 'bool', ['uint32_t index', 'const hg::Vector3 &vertex'], ['proxy'])

	gen.bind_method(shared_geometry, 'GetRgb', 'hg::Color', ['uint32_t index'], ['proxy'])
	protos = [('bool', ['uint32_t poly_index', 'const std::vector<hg::Color> &colors'], ['proxy'])]
	gen.bind_method_overloads(shared_geometry, 'SetRgb', expand_std_vector_proto(gen, protos))

	gen.bind_method(shared_geometry, 'GetUV', 'hg::tVector2<float>', ['uint32_t channel', 'uint32_t index'], ['proxy'])
	protos = [('bool', ['uint32_t channel', 'uint32_t poly_index', 'const std::vector<hg::tVector2<float>> &uvs'], ['proxy'])]
	gen.bind_method_overloads(shared_geometry, 'SetUV', expand_std_vector_proto(gen, protos))

	gen.bind_method(shared_geometry, 'SetPolygonVertexCount', 'bool', ['uint32_t index', 'uint8_t vtx_count'], ['proxy'])
	gen.bind_method(shared_geometry, 'SetPolygonMaterialIndex', 'bool', ['uint32_t index', 'uint8_t material'], ['proxy'])
	gen.bind_method(shared_geometry, 'SetPolygon', 'bool', ['uint32_t index', 'uint8_t vtx_count', 'uint8_t material'], ['proxy'])
	gen.bind_method(shared_geometry, 'GetPolygonVertexCount', 'int', ['uint32_t index'], ['proxy'])
	gen.bind_method(shared_geometry, 'GetPolygonMaterialIndex', 'int', ['uint32_t index'], ['proxy'])

	protos = [('bool', ['uint32_t index', 'const std::vector<int> &idx'], ['proxy'])]
	gen.bind_method_overloads(shared_geometry, 'SetPolygonBinding', expand_std_vector_proto(gen, protos))

	gen.bind_method(shared_geometry, 'ComputePolygonArea', 'float', ['uint32_t index'], ['proxy'])
	gen.bind_method(shared_geometry, 'Validate', 'bool', [], ['proxy'])

	gen.bind_method(shared_geometry, 'ComputePolygonNormal', 'bool', ['?bool force'], ['proxy'])
	gen.bind_method(shared_geometry, 'ComputePolygonTangent', 'bool', ['?uint32_t uv_index', '?bool force'], ['proxy'])

	gen.bind_method(shared_geometry, 'ComputeVertexNormal', 'bool', ['?float max_smoothing_angle', '?bool force'], ['proxy'])
	gen.bind_method(shared_geometry, 'ComputeVertexTangent', 'bool', ['?bool reverse_T', '?bool reverse_B', '?bool force'], ['proxy'])

	gen.bind_method(shared_geometry, 'ReverseTangentFrame', 'void', ['bool reverse_T', 'bool reverse_B'], ['proxy'])
	gen.bind_method(shared_geometry, 'SmoothRGB', 'void', ['uint32_t pass_count', 'float max_smoothing_angle'], ['proxy'])

	gen.bind_method(shared_geometry, 'MergeDuplicateMaterials', 'size_t', [], ['proxy'])

	gen.insert_binding_code('''
static bool _Geometry_SetMaterial(hg::Geometry *geo, size_t idx, const std::string &path) {
	if (idx >= geo->materials.size())
		return false;
	geo->materials[idx] = path;
	return true;
}
''')
	gen.bind_method(shared_geometry, 'SetMaterial', 'bool', ['size_t index', 'const std::string &path'], {'proxy': None, 'route': route_lambda('_Geometry_SetMaterial')})

	gen.insert_binding_code('''static std::string _Geometry_GetMaterial(hg::Geometry *geo, size_t idx) { 
	if (idx < 0 || idx >= geo->materials.size())
		return "";
	return geo->materials[idx];
}
''')
	gen.bind_method(shared_geometry, 'GetMaterial', 'const std::string &', ['size_t index'], {'proxy':None, 'route': route_lambda('_Geometry_GetMaterial')})

	gen.insert_binding_code('''static size_t _Geometry_GetMaterialCount(hg::Geometry *geo) { return geo->materials.size(); }''')
	gen.bind_method(shared_geometry, 'GetMaterialCount', 'size_t', [], {'proxy':None, 'route': route_lambda('_Geometry_GetMaterialCount')})

	gen.end_class(shared_geometry)
	
	#
	gen.add_include('engine/geometry_serialization.h')	
	gen.bind_function('hg::LoadGeometry', 'bool', ['hg::Geometry &geo', 'const std::string &path'])
	gen.bind_function('hg::SaveGeometry', 'bool', ['const std::shared_ptr<hg::Geometry> &geo', 'const std::string &path', '?hg::DocumentFormat format'])

	# hg::VertexLayout
	gen.add_include('engine/vertex_layout.h')
	
	gen.bind_named_enum('hg::IndexType', ['IndexUByte', 'IndexUShort', 'IndexUInt'], storage_type='uint8_t')
	gen.bind_named_enum('hg::VertexType', ['VertexByte', 'VertexUByte', 'VertexShort', 'VertexUShort', 'VertexInt', 'VertexUInt', 'VertexFloat', 'VertexHalfFloat'], storage_type='uint8_t')

	gen.insert_binding_code('''
static hg::VertexAttribute::Semantic _VertexLayoutAttribute_GetSemantic(hg::VertexLayout::Attribute *vtxLayoutAttr) { return vtxLayoutAttr->semantic; }
static void _VertexLayoutAttribute_SetSemantic(hg::VertexLayout::Attribute *vtxLayoutAttr, hg::VertexAttribute::Semantic semantic) { vtxLayoutAttr->semantic = semantic; }
static uint8_t _VertexLayoutAttribute_GetCount(hg::VertexLayout::Attribute *vtxLayoutAttr) { return vtxLayoutAttr->count; }
static void _VertexLayoutAttribute_SetCount(hg::VertexLayout::Attribute *vtxLayoutAttr, uint8_t count) { vtxLayoutAttr->count = count; }
static hg::VertexType _VertexLayoutAttribute_GetType(hg::VertexLayout::Attribute *vtxLayoutAttr) { return vtxLayoutAttr->type; }
static void _VertexLayoutAttribute_SetType(hg::VertexLayout::Attribute *vtxLayoutAttr, hg::VertexType type) { vtxLayoutAttr->type = type; }
static bool _VertexLayoutAttribute_GetIsNormalized(hg::VertexLayout::Attribute *vtxLayoutAttr) { return vtxLayoutAttr->is_normalized; }
static void _VertexLayoutAttribute_SetIsNormalized(hg::VertexLayout::Attribute *vtxLayoutAttr, bool is_normalized) { vtxLayoutAttr->is_normalized = is_normalized; }
''')
	vtx_layout_attr = gen.begin_class('hg::VertexLayout::Attribute', bound_name='VertexLayoutAttribute')
	gen.bind_constructor(vtx_layout_attr, [])
	gen.bind_method(vtx_layout_attr, 'GetSemantic', 'hg::VertexAttribute::Semantic', [], {'route': route_lambda('_VertexLayoutAttribute_GetSemantic')})
	gen.bind_method(vtx_layout_attr, 'SetSemantic', 'void', ['hg::VertexAttribute::Semantic semantic'], {'route': route_lambda('_VertexLayoutAttribute_SetSemantic')})
	gen.bind_method(vtx_layout_attr, 'GetCount', 'uint8_t', [], {'route': route_lambda('_VertexLayoutAttribute_GetCount')})
	gen.bind_method(vtx_layout_attr, 'SetCount', 'void', ['uint8_t count'], {'route': route_lambda('_VertexLayoutAttribute_SetCount')})
	gen.bind_method(vtx_layout_attr, 'GetType', 'hg::VertexType', [], {'route': route_lambda('_VertexLayoutAttribute_GetType')})
	gen.bind_method(vtx_layout_attr, 'SetType', 'void', ['hg::VertexType type'], {'route': route_lambda('_VertexLayoutAttribute_SetType')})
	gen.bind_method_overloads(vtx_layout_attr, 'IsNormalized', [
		('bool', [], {'route': route_lambda('_VertexLayoutAttribute_GetIsNormalized')}),
		('void', ['bool is_normalized'], {'route': route_lambda('_VertexLayoutAttribute_SetIsNormalized')})
	])
	gen.end_class(vtx_layout_attr)

	vtx_layout = gen.begin_class('hg::VertexLayout')
	gen.bind_constructor(vtx_layout, [])
	gen.typedef('hg::VertexLayout::Stride', 'uint8_t')
	gen.bind_member(vtx_layout, 'hg::VertexLayout::Stride stride')
	gen.bind_static_member(vtx_layout, 'const int max_attribute')
	gen.bind_method(vtx_layout, 'Clear', 'void', [])
	gen.bind_method(vtx_layout, 'AddAttribute', 'bool', ['hg::VertexAttribute::Semantic semantic', 'uint8_t count', 'hg::VertexType type', '?bool is_normalized'])
	gen.bind_method(vtx_layout, 'End', 'void', [])
	gen.bind_method(vtx_layout, 'GetAttribute', 'const hg::VertexLayout::Attribute*', ['hg::VertexAttribute::Semantic semantic'], {'check_rval': check_bool_rval_lambda(gen, 'GetAttribute failed')})
	gen.bind_comparison_ops(vtx_layout, ['==', '!='], ['const hg::VertexLayout &layout'])
	gen.end_class(vtx_layout)


def bind_create_geometry(gen):
	gen.add_include('engine/create_geometry.h')

	gen.bind_function_overloads('hg::CreateCapsule', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float radius'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y', 'const std::string &material_path'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y', 'const std::string &material_path', 'const std::string &name'], [])
	])
	gen.bind_function_overloads('hg::CreateCone', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float radius'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const std::string &material_path'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const std::string &material_path', 'const std::string &name'], [])
	])
	gen.bind_function_overloads('hg::CreateCube', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float width'], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float height'], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float height', 'float length'], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float height', 'float length', 'const std::string &material_path'], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float height', 'float length', 'const std::string &material_path', 'const std::string &name'], [])
	])
	gen.bind_function_overloads('hg::CreateCylinder', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float radius'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const std::string &material_path'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'const std::string &material_path', 'const std::string &name'], [])
	])
	gen.bind_function_overloads('hg::CreatePlane', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float width'], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float length'], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float length', 'int subdiv_x'], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float length', 'int subdiv_x', 'const std::string &material_path'], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float length', 'int subdiv_x', 'const std::string &material_path', 'const std::string &name'], [])
	])
	gen.bind_function_overloads('hg::CreateSphere', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float radius'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y', 'const std::string &material_path'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y', 'const std::string &material_path', 'const std::string &name'], [])
	])


def bind_frame_renderer(gen):
	frame_renderer = gen.begin_class('hg::FrameRenderer', bound_name='FrameRenderer_nobind', noncopyable=True, nobind=True)
	gen.end_class(frame_renderer)

	shared_frame_renderer = gen.begin_class('std::shared_ptr<hg::FrameRenderer>', bound_name='FrameRenderer', features={'proxy': lib.stl.SharedPtrProxyFeature(frame_renderer)})
	
	gen.bind_method(shared_frame_renderer, 'Initialize', 'bool', ["hg::RenderSystem &render_system"], ['proxy'])
	gen.bind_method(shared_frame_renderer, 'Shutdown', 'void', ["hg::RenderSystem &render_system"], ['proxy'])

	gen.end_class(shared_frame_renderer)

	#
	gen.insert_binding_code('static const std::shared_ptr<hg::FrameRenderer> NullFrameRenderer;\n')
	gen.bind_variable('const std::shared_ptr<hg::FrameRenderer> NullFrameRenderer')

	#
	gen.insert_binding_code('''static std::shared_ptr<hg::FrameRenderer> CreateFrameRenderer(const std::string &name) { return hg::g_frame_renderer_factory.get().Instantiate(name); }
static std::shared_ptr<hg::FrameRenderer> CreateFrameRenderer() { return hg::g_frame_renderer_factory.get().Instantiate(); }
	''', 'Frame renderer custom API')

	gen.bind_function('CreateFrameRenderer', 'std::shared_ptr<hg::FrameRenderer>', ['?const std::string &name'], {'check_rval': check_bool_rval_lambda(gen, 'CreateFrameRenderer failed')}, 'GetFrameRenderer')


def bind_scene(gen):
	gen.add_include('engine/scene.h')
	gen.add_include('engine/scene_reflection.h')
	gen.add_include('engine/node.h')

	# forward declarations
	node = gen.begin_class('hg::Node', bound_name='Node_nobind', noncopyable=True, nobind=True)
	gen.end_class(node)

	shared_node = gen.begin_class('std::shared_ptr<hg::Node>', bound_name='Node', features={'proxy': lib.stl.SharedPtrProxyFeature(node)})

	scene = gen.begin_class('hg::Scene', bound_name='Scene_nobind', noncopyable=True, nobind=True)
	gen.end_class(scene)

	shared_scene = gen.begin_class('std::shared_ptr<hg::Scene>', bound_name='Scene', features={'proxy': lib.stl.SharedPtrProxyFeature(scene)})

	scene_system = gen.begin_class('hg::SceneSystem', bound_name='SceneSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(scene_system)

	shared_scene_system = gen.begin_class('std::shared_ptr<hg::SceneSystem>', bound_name='SceneSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(scene_system)})

	gen.bind_named_enum('hg::ComponentState', ['NotReady', 'Ready', 'Failed'], storage_type='uint8_t')

	#
	gen.insert_binding_code('static const std::shared_ptr<hg::Node> NullNode;\n')
	gen.bind_variable('const std::shared_ptr<hg::Node> NullNode')

	#
	def decl_get_set_method(conv, type, method_suffix, var_name, features=[]):
		gen.bind_method(conv, 'Get' + method_suffix, 'const %s' % type, [], features)
		gen.bind_method(conv, 'Set' + method_suffix, 'void', ['const %s &%s' % (type, var_name)], features)

	def decl_comp_get_set_method(conv, comp_type, comp_var_name, type, method_suffix, var_name, features=[]):
		gen.bind_method(conv, 'Get' + method_suffix, 'const %s &' % type, ['const %s *%s' % (comp_type, comp_var_name)], features)
		gen.bind_method(conv, 'Set' + method_suffix, 'void', ['%s *%s' % (comp_type, comp_var_name), 'const %s &%s' % (type, var_name)], features)

	# hg::Component
	gen.add_include('engine/component.h')

	gen.bind_named_enum('hg::ComponentState', ['NotReady', 'Ready', 'Failed'], storage_type='uint8_t')

	component = gen.begin_class('hg::Component', bound_name='Component_nobind', noncopyable=True, nobind=True)
	gen.end_class(component)

	shared_component = gen.begin_class('std::shared_ptr<hg::Component>', bound_name='Component', features={'proxy': lib.stl.SharedPtrProxyFeature(component)})

	gen.bind_method(shared_component, 'GetSceneSystem', 'std::shared_ptr<hg::SceneSystem>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Component is not registered in a SceneSystem')})
	gen.bind_method(shared_component, 'GetScene', 'std::shared_ptr<hg::Scene>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Component is not registered in a Scene')})
	gen.bind_method(shared_component, 'GetNode', 'std::shared_ptr<hg::Node>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Component is not registered in a Node')})

	gen.bind_method(shared_component, 'IsAssigned', 'bool', [], ['proxy'])

	gen.bind_method(shared_component, 'GetEnabled', 'bool', [], ['proxy'])
	gen.bind_method(shared_component, 'SetEnabled', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_component, 'GetState', 'hg::ComponentState', [], ['proxy'])

	gen.bind_method(shared_component, 'GetAspect', 'const std::string &', [], ['proxy'])

	gen.bind_method(shared_component, 'GetDoNotSerialize', 'bool', [], ['proxy'])
	gen.bind_method(shared_component, 'SetDoNotSerialize', 'void', ['bool do_not_serialize'], ['proxy'])

	gen.bind_method(shared_component, 'GetShowInEditor', 'bool', [], ['proxy'])
	gen.bind_method(shared_component, 'SetShowInEditor', 'void', ['bool shown_in_editor'], ['proxy'])

	gen.bind_method(shared_component, 'GetRegisteredInScene', 'std::shared_ptr<hg::Scene>', [], ['proxy'])

	gen.end_class(shared_component)

	bind_std_vector(gen, shared_component)

	# hg::Instance
	gen.add_include('engine/instance.h')

	instance = gen.begin_class('hg::Instance', bound_name='Instance_nobind', noncopyable=True, nobind=True)
	gen.end_class(instance)

	shared_instance = gen.begin_class('std::shared_ptr<hg::Instance>', bound_name='Instance', features={'proxy': lib.stl.SharedPtrProxyFeature(instance)})
	gen.add_base(shared_instance, shared_component)

	gen.bind_constructor(shared_instance, [], ['proxy'])
	decl_get_set_method(shared_instance, 'std::string', 'Path', 'path', ['proxy'])
	gen.bind_method(shared_instance, 'GetState', 'hg::ComponentState', [], ['proxy'])

	gen.end_class(shared_instance)

	# hg::Target
	gen.add_include('engine/target.h')

	target = gen.begin_class('hg::Target', bound_name='Target_nobind', noncopyable=True, nobind=True)
	gen.end_class(target)

	shared_target = gen.begin_class('std::shared_ptr<hg::Target>', bound_name='Target', features={'proxy': lib.stl.SharedPtrProxyFeature(target)})
	gen.add_base(shared_target, shared_component)

	gen.bind_constructor(shared_target, [], ['proxy'])
	decl_get_set_method(shared_target, 'std::shared_ptr<hg::Node>', 'Target', 'target', ['proxy'])

	gen.end_class(shared_target)

	# hg::Environment
	gen.add_include('engine/environment.h')

	environment = gen.begin_class('hg::Environment', bound_name='Environment_nobind', noncopyable=True, nobind=True)
	gen.end_class(environment)

	shared_environment = gen.begin_class('std::shared_ptr<hg::Environment>', bound_name='Environment', features={'proxy': lib.stl.SharedPtrProxyFeature(environment)})
	gen.add_base(shared_environment, shared_component)

	gen.bind_constructor(shared_environment, [], ['proxy'])

	decl_get_set_method(shared_environment, 'float', 'TimeOfDay', 'time_of_day', ['proxy'])

	decl_get_set_method(shared_environment, 'bool', 'ClearBackgroundColor', 'clear_bg_color', ['proxy'])
	decl_get_set_method(shared_environment, 'bool', 'ClearBackgroundDepth', 'clear_bg_depth', ['proxy'])
	decl_get_set_method(shared_environment, 'hg::Color', 'BackgroundColor', 'background_color', ['proxy'])

	decl_get_set_method(shared_environment, 'float', 'AmbientIntensity', 'ambient_intensity', ['proxy'])
	decl_get_set_method(shared_environment, 'hg::Color', 'AmbientColor', 'ambient_color', ['proxy'])

	decl_get_set_method(shared_environment, 'hg::Color', 'FogColor', 'fog_color', ['proxy'])
	decl_get_set_method(shared_environment, 'float', 'FogNear', 'fog_near', ['proxy'])
	decl_get_set_method(shared_environment, 'float', 'FogFar', 'fog_far', ['proxy'])

	gen.end_class(shared_environment)

	# hg::SimpleGraphicSceneOverlay
	gen.add_include('engine/simple_graphic_scene_overlay.h')

	simple_graphic_scene_overlay = gen.begin_class('hg::SimpleGraphicSceneOverlay', bound_name='SimpleGraphicSceneOverlay_nobind', noncopyable=True, nobind=True)
	gen.end_class(simple_graphic_scene_overlay)

	shared_simple_graphic_scene_overlay = gen.begin_class('std::shared_ptr<hg::SimpleGraphicSceneOverlay>', bound_name='SimpleGraphicSceneOverlay', features={'proxy': lib.stl.SharedPtrProxyFeature(simple_graphic_scene_overlay)})
	gen.add_base(shared_simple_graphic_scene_overlay, shared_component)

	gen.bind_constructor_overloads(shared_simple_graphic_scene_overlay, [
		([], ['proxy']),
		(['bool is_2d_overlay'], ['proxy'])
	])

	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetSnapGlyphToGrid', 'void', ['bool snap'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetSnapGlyphToGrid', 'bool', [], ['proxy'])

	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetBlendMode', 'void', ['hg::BlendMode mode'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetBlendMode', 'hg::BlendMode', [], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetCullMode', 'void', ['hg::CullMode mode'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetCullMode', 'hg::CullMode', [], ['proxy'])

	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetDepthWrite', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetDepthWrite', 'bool', [], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'SetDepthTest', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'GetDepthTest', 'bool', [], ['proxy'])

	gen.bind_method(shared_simple_graphic_scene_overlay, 'Line', 'void', ['float sx', 'float sy', 'float sz', 'float ex', 'float ey', 'float ez', 'const hg::Color &start_color', 'const hg::Color &end_color'], ['proxy'])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'Triangle', 'void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'const hg::Color &a_color', 'const hg::Color &b_color', 'const hg::Color &c_color'], ['proxy'])
	gen.bind_method_overloads(shared_simple_graphic_scene_overlay, 'Text', [
		('void', ['float x', 'float y', 'float z', 'const std::string &text', 'const hg::Color &color', 'std::shared_ptr<hg::RasterFont> font', 'float scale'], ['proxy']),
		('void', ['const hg::Matrix4 &mat', 'const std::string &text', 'const hg::Color &color', 'std::shared_ptr<hg::RasterFont> font', 'float scale'], ['proxy'])
	])

	gen.insert_binding_code('''
static void _SimpleGraphicSceneOverlay_Quad(hg::SimpleGraphicSceneOverlay *overlay, float ax, float ay, float az, float bx, float by, float bz, float cx, float cy, float cz, float dx, float dy, float dz, const hg::Color &a_color, const hg::Color &b_color, const hg::Color &c_color, const hg::Color &d_color) {
	overlay->Quad(ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz, 0, 0, 1, 1, nullptr, a_color, b_color, c_color, d_color);
}
''')
	gen.bind_method_overloads(shared_simple_graphic_scene_overlay, 'Quad', [
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'const hg::Color &a_color', 'const hg::Color &b_color', 'const hg::Color &c_color', 'const hg::Color &d_color'], {'proxy': None, 'route': route_lambda('_SimpleGraphicSceneOverlay_Quad')}),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'float uv_sx', 'float uv_sy', 'float uv_ex', 'float uv_ey', 'std::shared_ptr<hg::Texture> texture', 'const hg::Color &a_color', 'const hg::Color &b_color', 'const hg::Color &c_color', 'const hg::Color &d_color'], ['proxy'])
	])
	gen.bind_method(shared_simple_graphic_scene_overlay, 'Geometry', 'void', ['float x', 'float y', 'float z', 'float ex', 'float ey', 'float ez', 'float sx', 'float sy', 'float sz', 'std::shared_ptr<hg::RenderGeometry> geometry'], ['proxy'])

	gen.end_class(shared_simple_graphic_scene_overlay)

	# hg::Transform
	gen.add_include('engine/transform.h')

	transform = gen.begin_class('hg::Transform', bound_name='Transform_nobind', noncopyable=True, nobind=True)
	gen.end_class(transform)

	shared_transform = gen.begin_class('std::shared_ptr<hg::Transform>', bound_name='Transform', features={'proxy': lib.stl.SharedPtrProxyFeature(transform)})
	gen.add_base(shared_transform, shared_component)

	gen.bind_constructor_overloads(shared_transform, [
		([], ['proxy']),
		(['const hg::Vector3 &pos', '?const hg::Vector3 &rot', '?const hg::Vector3 &scl'], ['proxy'])
	])

	gen.bind_method(shared_transform, 'GetParent', 'std::shared_ptr<hg::Node>', [], ['proxy'])
	gen.bind_method(shared_transform, 'SetParent', 'void', ['std::shared_ptr<hg::Node> parent'], ['proxy'])

	gen.bind_method(shared_transform, 'GetPreviousWorld', 'hg::Matrix4', [], ['proxy'])
	gen.bind_method(shared_transform, 'GetWorld', 'hg::Matrix4', [], ['proxy'])

	decl_get_set_method(shared_transform, 'hg::Vector3', 'Position', 'position', ['proxy'])
	decl_get_set_method(shared_transform, 'hg::Vector3', 'Rotation', 'rotation', ['proxy'])
	decl_get_set_method(shared_transform, 'hg::Vector3', 'Scale', 'scale', ['proxy'])

	gen.bind_method(shared_transform, 'SetRotationMatrix', 'void', ['const hg::Matrix3 &rotation'], ['proxy'])

	gen.bind_method(shared_transform, 'SetLocal', 'void', ['hg::Matrix4 &local'], ['proxy'])
	gen.bind_method(shared_transform, 'SetWorld', 'void', ['hg::Matrix4 &world'], ['proxy'])
	gen.bind_method(shared_transform, 'OffsetWorld', 'void', ['hg::Matrix4 &offset'], ['proxy'])

	gen.bind_method(shared_transform, 'TransformLocalPoint', 'hg::Vector3', ['const hg::Vector3 &local_point'], ['proxy'])
	gen.end_class(shared_transform)

	# hg::Camera
	gen.add_include('engine/camera.h')

	cam = gen.begin_class('hg::Camera', bound_name='Camera_nobind', noncopyable=True, nobind=True)
	gen.end_class(cam)

	shared_cam = gen.begin_class('std::shared_ptr<hg::Camera>', bound_name='Camera', features={'proxy': lib.stl.SharedPtrProxyFeature(cam)})
	gen.add_base(shared_cam, shared_component)

	gen.bind_constructor(shared_cam, [], ['proxy'])

	decl_get_set_method(shared_cam, 'float', 'ZoomFactor', 'zoom_factor', ['proxy'])
	decl_get_set_method(shared_cam, 'float', 'ZNear', 'z_near', ['proxy'])
	decl_get_set_method(shared_cam, 'float', 'ZFar', 'z_far', ['proxy'])

	decl_get_set_method(shared_cam, 'bool', 'Orthographic', 'is_orthographic', ['proxy'])
	decl_get_set_method(shared_cam, 'float', 'OrthographicSize', 'orthographic_size', ['proxy'])

	gen.bind_method(shared_cam, 'GetProjectionMatrix', 'hg::Matrix44', ['const hg::tVector2<float> &aspect_ratio'], ['proxy'])
	gen.end_class(shared_cam)

	gen.bind_function('hg::Project', 'bool', ['const hg::Matrix4 &camera_world', 'float zoom_factor', 'const hg::tVector2<float> &aspect_ratio', 'const hg::Vector3 &position', 'hg::Vector3 &out'], {'arg_out': ['out']})
	gen.bind_function('hg::Unproject', 'bool', ['const hg::Matrix4 &camera_world', 'float zoom_factor', 'const hg::tVector2<float> &aspect_ratio', 'const hg::Vector3 &position', 'hg::Vector3 &out'], {'arg_out': ['out']})

	gen.bind_function('hg::ExtractZoomFactorFromProjectionMatrix', 'float', ['const hg::Matrix44 &projection_matrix'])
	gen.bind_function('hg::ExtractZRangeFromProjectionMatrix', 'void', ['const hg::Matrix44 &projection_matrix', 'float &znear', 'float &zfar'], {'arg_out': ['znear', 'zfar']})

	# hg::Object
	gen.add_include('engine/object.h')

	obj = gen.begin_class('hg::Object', bound_name='Object_nobind', noncopyable=True, nobind=True)
	gen.end_class(obj)

	shared_obj = gen.begin_class('std::shared_ptr<hg::Object>', bound_name='Object', features={'proxy': lib.stl.SharedPtrProxyFeature(obj)})
	gen.add_base(shared_obj, shared_component)

	gen.bind_constructor(shared_obj, [], ['proxy'])

	gen.bind_method(shared_obj, 'GetState', 'hg::ComponentState', [], ['proxy'])

	decl_get_set_method(shared_obj, 'std::shared_ptr<hg::RenderGeometry>', 'Geometry', 'geometry', ['proxy'])

	gen.bind_method(shared_obj, 'GetLocalMinMax', 'hg::MinMax', [], ['proxy'])

	gen.bind_method(shared_obj, 'GetBindMatrix', 'bool', ['uint32_t index', 'hg::Matrix4 &bind_matrix'], ['proxy'])
	gen.bind_method(shared_obj, 'HasSkeleton', 'bool', [], ['proxy'])
	gen.bind_method(shared_obj, 'IsSkinBound', 'bool', [], ['proxy'])

	gen.bind_method(shared_obj, 'GetBoneCount', 'uint32_t', [], ['proxy'])
	gen.bind_method(shared_obj, 'GetBone', 'const std::shared_ptr<hg::Node> &', ['uint32_t index'], ['proxy'])
	gen.end_class(shared_obj)

	# hg::Light
	gen.add_include('engine/light.h')

	gen.bind_named_enum('hg::Light::Model', ['ModelPoint', 'ModelLinear', 'ModelSpot', 'ModelLast'], prefix='Light')
	gen.bind_named_enum('hg::Light::Shadow', ['ShadowNone', 'ShadowProjectionMap', 'ShadowMap'], prefix='Light')

	light = gen.begin_class('hg::Light', bound_name='Light_nobind', noncopyable=True, nobind=True)
	gen.end_class(light)

	shared_light = gen.begin_class('std::shared_ptr<hg::Light>', bound_name='Light', features={'proxy': lib.stl.SharedPtrProxyFeature(light)})
	gen.add_base(shared_light, shared_component)

	gen.bind_constructor(shared_light, [], ['proxy'])

	decl_get_set_method(shared_light, 'hg::Light::Model', 'Model', ' model', ['proxy'])
	decl_get_set_method(shared_light, 'hg::Light::Shadow', 'Shadow', ' shadow', ['proxy'])
	decl_get_set_method(shared_light, 'bool', 'ShadowCastAll', ' shadow_cast_all', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ShadowRange', ' shadow_range', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ShadowBias', ' shadow_bias', ['proxy'])
	decl_get_set_method(shared_light, 'hg::Vector4', 'ShadowSplit', ' shadow_split', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ZNear', ' z_near', ['proxy'])

	decl_get_set_method(shared_light, 'float', 'Range', ' range', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ClipDistance', ' clip_distance', ['proxy'])

	decl_get_set_method(shared_light, 'hg::Color', 'DiffuseColor', ' diffuse_color', ['proxy'])
	decl_get_set_method(shared_light, 'hg::Color', 'SpecularColor', ' specular_color', ['proxy'])
	decl_get_set_method(shared_light, 'hg::Color', 'ShadowColor', ' shadow_color', ['proxy'])

	decl_get_set_method(shared_light, 'float', 'DiffuseIntensity', ' diffuse_intensity', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'SpecularIntensity', ' specular_intensity', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'ConeAngle', ' cone_angle', ['proxy'])
	decl_get_set_method(shared_light, 'float', 'EdgeAngle', ' edge_angle', ['proxy'])

	decl_get_set_method(shared_light, 'std::shared_ptr<hg::Texture>', 'ProjectionTexture', ' projection_texture', ['proxy'])

	gen.end_class(shared_light)

	# hg::RigidBody
	gen.add_include('engine/rigid_body.h')

	gen.bind_named_enum('hg::RigidBodyType', ['RigidBodyDynamic', 'RigidBodyKinematic', 'RigidBodyStatic'])

	rigid_body = gen.begin_class('hg::RigidBody', bound_name='RigidBody_nobind', noncopyable=True, nobind=True)
	gen.end_class(rigid_body)

	shared_rigid_body = gen.begin_class('std::shared_ptr<hg::RigidBody>', bound_name='RigidBody', features={'proxy': lib.stl.SharedPtrProxyFeature(rigid_body)})
	gen.add_base(shared_rigid_body, shared_component)

	gen.bind_constructor(shared_rigid_body, [], ['proxy'])

	decl_get_set_method(shared_rigid_body, 'bool', 'IsSleeping', 'is_sleeping', ['proxy'])

	gen.bind_method(shared_rigid_body, 'GetVelocity', 'const hg::Vector3', ['const hg::Vector3 &position'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'SetVelocity', 'void', ['const hg::Vector3 &V', 'const hg::Vector3 &position'], ['proxy'])

	decl_get_set_method(shared_rigid_body, 'hg::Vector3', 'LinearVelocity', 'V', ['proxy'])
	decl_get_set_method(shared_rigid_body, 'hg::Vector3', 'AngularVelocity', 'W', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'float', 'LinearDamping', 'damping', ['proxy'])
	decl_get_set_method(shared_rigid_body, 'float', 'AngularDamping', 'damping', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'float', 'StaticFriction', 'sF', ['proxy'])
	decl_get_set_method(shared_rigid_body, 'float', 'DynamicFriction', 'dF', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'float', 'Restitution', 'restitution', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'hg::RigidBodyType', 'Type', 'type', ['proxy'])

	decl_get_set_method(shared_rigid_body, 'int', 'AxisLock', 'axis_lock', ['proxy'])
	decl_get_set_method(shared_rigid_body, 'int', 'CollisionLayer', 'layer', ['proxy'])

	gen.bind_method(shared_rigid_body, 'ApplyLinearImpulse', 'void', ['const hg::Vector3 &I'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'ApplyLinearForce', 'void', ['const hg::Vector3 &F'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'ApplyImpulse', 'void', ['const hg::Vector3 &I', 'const hg::Vector3 &position'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'ApplyForce', 'void', ['const hg::Vector3 &F', 'const hg::Vector3 &position'], ['proxy'])
	gen.bind_method(shared_rigid_body, 'ApplyTorque', 'void', ['const hg::Vector3 &T'], ['proxy'])

	gen.bind_method(shared_rigid_body, 'ResetWorld', 'void', ['const hg::Matrix4 &m'], ['proxy'])

	gen.end_class(shared_rigid_body)

	# hg::Collision
	gen.add_include('engine/collision.h')

	collision = gen.begin_class('hg::Collision', bound_name='Collision_nobind', noncopyable=True, nobind=True)
	gen.end_class(collision)

	shared_collision = gen.begin_class('std::shared_ptr<hg::Collision>', bound_name='Collision', features={'proxy': lib.stl.SharedPtrProxyFeature(collision)})
	gen.add_base(shared_collision, shared_component)
	decl_get_set_method(shared_collision, 'float', 'Mass', 'mass', ['proxy'])
	decl_get_set_method(shared_collision, 'hg::Matrix4', 'Matrix', 'matrix', ['proxy'])
	gen.end_class(shared_collision)	

	# hg::BoxCollision
	gen.add_include('engine/box_collision.h')

	box_collision = gen.begin_class('hg::BoxCollision', bound_name='BoxCollision_nobind', noncopyable=True, nobind=True)
	gen.end_class(box_collision)

	shared_box_collision = gen.begin_class('std::shared_ptr<hg::BoxCollision>', bound_name='BoxCollision', features={'proxy': lib.stl.SharedPtrProxyFeature(box_collision)})
	gen.add_bases(shared_box_collision, [shared_component, shared_collision])
	gen.bind_constructor(shared_box_collision, [], ['proxy'])
	decl_get_set_method(shared_box_collision, 'hg::Vector3', 'Dimensions', 'dimensions', ['proxy'])
	gen.end_class(shared_box_collision)	

	# hg::MeshCollision
	gen.add_include('engine/mesh_collision.h')

	mesh_collision = gen.begin_class('hg::MeshCollision', bound_name='MeshCollision_nobind', noncopyable=True, nobind=True)
	gen.end_class(mesh_collision)

	shared_mesh_collision = gen.begin_class('std::shared_ptr<hg::MeshCollision>', bound_name='MeshCollision', features={'proxy': lib.stl.SharedPtrProxyFeature(mesh_collision)})
	gen.add_bases(shared_mesh_collision, [shared_component, shared_collision])
	gen.bind_constructor(shared_mesh_collision, [], ['proxy'])
	decl_get_set_method(shared_mesh_collision, 'std::shared_ptr<hg::Geometry>', 'Geometry', 'geometry', ['proxy'])
	gen.end_class(shared_mesh_collision)	

	# hg::SphereCollision
	gen.add_include('engine/sphere_collision.h')

	sphere_collision = gen.begin_class('hg::SphereCollision', bound_name='SphereCollision_nobind', noncopyable=True, nobind=True)
	gen.end_class(sphere_collision)

	shared_sphere_collision = gen.begin_class('std::shared_ptr<hg::SphereCollision>', bound_name='SphereCollision', features={'proxy': lib.stl.SharedPtrProxyFeature(sphere_collision)})
	gen.add_bases(shared_sphere_collision, [shared_component, shared_collision])
	gen.bind_constructor(shared_sphere_collision, [], ['proxy'])
	decl_get_set_method(shared_sphere_collision, 'float', 'Radius', 'radius', ['proxy'])
	gen.end_class(shared_sphere_collision)	

	# hg::CapsuleCollision
	gen.add_include('engine/capsule_collision.h')

	capsule_collision = gen.begin_class('hg::CapsuleCollision', bound_name='CapsuleCollision_nobind', noncopyable=True, nobind=True)
	gen.end_class(capsule_collision)

	shared_capsule_collision = gen.begin_class('std::shared_ptr<hg::CapsuleCollision>', bound_name='CapsuleCollision', features={'proxy': lib.stl.SharedPtrProxyFeature(capsule_collision)})
	gen.add_bases(shared_capsule_collision, [shared_component, shared_collision])
	gen.bind_constructor(shared_capsule_collision, [], ['proxy'])
	decl_get_set_method(shared_capsule_collision, 'float', 'Length', 'length', ['proxy'])
	decl_get_set_method(shared_capsule_collision, 'float', 'Radius', 'radius', ['proxy'])
	gen.end_class(shared_capsule_collision)	

	# hg::ConvexCollision
	gen.add_include('engine/convex_collision.h')

	convex_collision = gen.begin_class('hg::ConvexCollision', bound_name='ConvexCollision_nobind', noncopyable=True, nobind=True)
	gen.end_class(convex_collision)

	shared_convex_collision = gen.begin_class('std::shared_ptr<hg::ConvexCollision>', bound_name='ConvexCollision', features={'proxy': lib.stl.SharedPtrProxyFeature(convex_collision)})
	gen.add_bases(shared_convex_collision, [shared_component, shared_collision])
	gen.bind_constructor(shared_convex_collision, [], ['proxy'])
	decl_get_set_method(shared_convex_collision, 'std::shared_ptr<hg::Geometry>', 'Geometry', 'geometry', ['proxy'])
	gen.end_class(shared_convex_collision)	
	
	# hg::JointLimit
	gen.add_include('engine/joint.h')

	join_limit = gen.begin_class('hg::JointLimit')
	gen.bind_constructor_overloads(join_limit, [
		([], []),
		(['float smin', 'float smax'], [])
	])
	gen.bind_comparison_op(join_limit, '==', ['const hg::JointLimit &o'])
	gen.bind_members(join_limit, ['float min', 'float max'])
	gen.end_class(join_limit)

	# hg::Joint
	joint = gen.begin_class('hg::Joint', bound_name='Joint_nobind', noncopyable=True, nobind=True)
	gen.end_class(joint)

	shared_joint = gen.begin_class('std::shared_ptr<hg::Joint>', bound_name='Joint', features={'proxy': lib.stl.SharedPtrProxyFeature(joint)})
	gen.add_bases(shared_joint, [shared_component])
	decl_get_set_method(shared_joint, 'hg::Vector3', 'Pivot', 'pivot', ['proxy'])
	decl_get_set_method(shared_joint, 'std::shared_ptr<hg::Node>', 'OtherBody', 'other_body', ['proxy'])
	decl_get_set_method(shared_joint, 'hg::Vector3', 'OtherPivot', 'other_pivot', ['proxy'])
	gen.end_class(shared_joint)

	#hg::SphericalJoint
	gen.add_include('engine/spherical_joint.h')
	
	spherical_joint = gen.begin_class('hg::SphericalJoint', bound_name='SphericalJoint_nobind', noncopyable=True, nobind=True)
	gen.end_class(spherical_joint)

	shared_spherical_joint = gen.begin_class('std::shared_ptr<hg::SphericalJoint>', bound_name='SphericalJoint', features={'proxy': lib.stl.SharedPtrProxyFeature(spherical_joint)})
	gen.add_bases(shared_spherical_joint, [shared_component, shared_joint])
	gen.bind_constructor(shared_spherical_joint, [], ['proxy'])
	gen.end_class(shared_spherical_joint)

	#hg::D6Joint
	gen.add_include('engine/d6_joint.h')
	
	d6_joint = gen.begin_class('hg::D6Joint', bound_name='D6Joint_nobind', noncopyable=True, nobind=True)
	gen.end_class(d6_joint)

	shared_d6_joint = gen.begin_class('std::shared_ptr<hg::D6Joint>', bound_name='D6Joint', features={'proxy': lib.stl.SharedPtrProxyFeature(d6_joint)})
	gen.add_bases(shared_d6_joint, [shared_component, shared_joint])
	gen.bind_constructor(shared_d6_joint, [], ['proxy'])
	decl_get_set_method(shared_d6_joint, 'uint8_t', 'AxisLock', 'axis_lock', ['proxy'])
	decl_get_set_method(shared_d6_joint, 'hg::JointLimit', 'XAxisLimit', 'x_axis_limit', ['proxy'])
	decl_get_set_method(shared_d6_joint, 'hg::JointLimit', 'YAxisLimit', 'y_axis_limit', ['proxy'])
	decl_get_set_method(shared_d6_joint, 'hg::JointLimit', 'ZAxisLimit', 'z_axis_limit', ['proxy'])
	decl_get_set_method(shared_d6_joint, 'hg::JointLimit', 'RotXAxisLimit', 'rot_x_axis_limit', ['proxy'])
	decl_get_set_method(shared_d6_joint, 'hg::JointLimit', 'RotYAxisLimit', 'rot_y_axis_limit', ['proxy'])
	decl_get_set_method(shared_d6_joint, 'hg::JointLimit', 'RotZAxisLimit', 'rot_z_axis_limit', ['proxy'])
	gen.end_class(shared_d6_joint)

	# hg::Terrain
	gen.add_include('engine/terrain.h')

	terrain = gen.begin_class('hg::Terrain', bound_name='Terrain_nobind', noncopyable=True, nobind=True)
	gen.end_class(terrain)

	shared_terrain = gen.begin_class('std::shared_ptr<hg::Terrain>', bound_name='Terrain', features={'proxy': lib.stl.SharedPtrProxyFeature(terrain)})
	gen.add_base(shared_terrain, shared_component)

	gen.bind_constructor(shared_terrain, [], ['proxy'])

	decl_get_set_method(shared_terrain, 'std::string', 'Heightmap', 'heightmap', ['proxy'])
	decl_get_set_method(shared_terrain, 'hg::tVector2<int>', 'HeightmapResolution', 'heightmap_resolution', ['proxy'])
	decl_get_set_method(shared_terrain, 'uint32_t', 'HeightmapBpp', 'heightmap_bpp', ['proxy'])

	decl_get_set_method(shared_terrain, 'hg::Vector3', 'Size', 'size', ['proxy'])

	decl_get_set_method(shared_terrain, 'std::string', 'SurfaceShader', 'surface_shader', ['proxy'])

	decl_get_set_method(shared_terrain, 'int', 'PatchSubdivisionThreshold', 'patch_subdv_threshold', ['proxy'])
	decl_get_set_method(shared_terrain, 'int', 'MaxRecursion', 'max_recursion', ['proxy'])
	decl_get_set_method(shared_terrain, 'float', 'MinPrecision', 'min_precision', ['proxy'])

	decl_get_set_method(shared_terrain, 'bool', 'Wireframe', 'wireframe', ['proxy'])

	gen.end_class(shared_terrain)

	# hg::ScriptEngineEnv
	gen.add_include('engine/script_system.h')

	script_env = gen.begin_class('hg::ScriptEngineEnv', bound_name='ScriptEnv_nobind', noncopyable=True, nobind=True)
	gen.end_class(script_env)

	shared_script_env = gen.begin_class('std::shared_ptr<hg::ScriptEngineEnv>', bound_name='ScriptEnv', features={'proxy': lib.stl.SharedPtrProxyFeature(script_env)})
	gen.bind_constructor(shared_script_env, ['std::shared_ptr<hg::RenderSystemAsync> render_system_async', 'std::shared_ptr<hg::RendererAsync> renderer_async', 'std::shared_ptr<hg::MixerAsync> mixer'], ['proxy'])
	gen.bind_member(shared_script_env, 'float dt', ['proxy'])
	gen.end_class(shared_script_env)

	# hg::ScriptObject
	if gen.get_language() == 'CPython':
		# unsupported (no CPython embedded)
		pass
	elif gen.get_language() == 'Lua':
		gen.add_include('engine/lua_vm.h')

		class LuaScriptObjectConverter(lang.lua.LuaTypeConverterCommon):
			def get_type_glue(self, gen, module_name):
				check = '''\
bool %s(lua_State *L, int idx) {
	using namespace hg;
	return true;
}
''' % self.check_func

				to_c = '''\
void %s(lua_State *L, int idx, void *obj) {
	reinterpret_cast<hg::ScriptObject *>(obj)->impl = std::make_shared<hg::LuaObjectImpl>(L, luaL_ref(L, LUA_REGISTRYINDEX));
}
''' % self.to_c_func

				from_c = '''\
int %s(lua_State *L, void *obj, OwnershipPolicy) {
	lua_rawgeti(L, LUA_REGISTRYINDEX, static_cast<const hg::LuaObjectImpl *>(reinterpret_cast<hg::ScriptObject *>(obj)->impl.get())->Get());
	return 1;
}
''' % self.from_c_func
				return check + to_c + from_c

		type_value = gen.bind_type(LuaScriptObjectConverter('hg::ScriptObject'))

	# hg::Script
	gen.bind_named_enum('hg::ScriptExecutionMode', ['ScriptExecutionStandalone', 'ScriptExecutionEditor', 'ScriptExecutionAll'])

	script = gen.begin_class('hg::Script', bound_name='Script_nobind', noncopyable=True, nobind=True)
	gen.end_class(script)

	shared_script = gen.begin_class('std::shared_ptr<hg::Script>', bound_name='Script', features={'proxy': lib.stl.SharedPtrProxyFeature(script)})
	gen.add_base(shared_script, shared_component)

	gen.bind_method(shared_script, 'BlockingGet', 'hg::TypeValue', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_script, 'Get', 'hg::TypeValue', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_script, 'Set', 'void', ['const std::string &name', 'const hg::TypeValue &value'], ['proxy'])

	gen.bind_method(shared_script, 'Expose', 'void', ['const std::string &name', 'const hg::TypeValue &value'], ['proxy'])
	gen.bind_method(shared_script, 'Call', 'void', ['const std::string &name', 'const std::vector<hg::TypeValue> &parms'], ['proxy'])

	if gen.get_language() == 'Lua':
		gen.bind_method(shared_script, 'GetEnv', 'hg::ScriptObject', [], ['proxy'])

	gen.end_class(shared_script)

	# hg::RenderScript
	render_script = gen.begin_class('hg::RenderScript', bound_name='RenderScript_nobind', noncopyable=True, nobind=True)
	gen.end_class(render_script)

	shared_render_script = gen.begin_class('std::shared_ptr<hg::RenderScript>', bound_name='RenderScript', features={'proxy': lib.stl.SharedPtrProxyFeature(render_script)})
	gen.add_base(shared_render_script, shared_script)
	gen.bind_constructor(shared_render_script, ['?const std::string &path'], ['proxy'])
	gen.end_class(shared_render_script)

	# hg::LogicScript
	logic_script = gen.begin_class('hg::LogicScript', bound_name='LogicScript_nobind', noncopyable=True, nobind=True)
	gen.end_class(logic_script)

	shared_logic_script = gen.begin_class('std::shared_ptr<hg::LogicScript>', bound_name='LogicScript', features={'proxy': lib.stl.SharedPtrProxyFeature(logic_script)})
	gen.add_base(shared_logic_script, shared_script)
	gen.bind_constructor(shared_logic_script, ['?const std::string &path'], ['proxy'])
	gen.end_class(shared_logic_script)

	# hg::ScriptSystem
	script_system = gen.begin_class('hg::ScriptSystem', bound_name='ScriptSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(script_system)

	shared_script_system = gen.begin_class('std::shared_ptr<hg::ScriptSystem>', bound_name='ScriptSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(script_system)})
	gen.add_base(shared_script_system, shared_scene_system)

	gen.bind_method(shared_script_system, 'GetExecutionMode', 'hg::ScriptExecutionMode', [], ['proxy'])
	gen.bind_method(shared_script_system, 'SetExecutionMode', 'void', ['hg::ScriptExecutionMode mode'], ['proxy'])

	gen.bind_method(shared_script_system, 'TestScriptIsReady', 'bool', ['const hg::Script &script'], ['proxy'])

	gen.bind_method(shared_script_system, 'GetImplementationName', 'const std::string &', [], ['proxy'])

	gen.bind_method(shared_script_system, 'Open', 'bool', [], ['proxy'])
	gen.bind_method(shared_script_system, 'Close', 'void', [], ['proxy'])

	gen.bind_method(shared_script_system, 'Reset', 'void', [], ['proxy'])

	gen.end_class(shared_script_system)

	# hg::LuaSystem
	gen.add_include('engine/lua_system.h')

	lua_system = gen.begin_class('hg::LuaSystem', bound_name='LuaSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(lua_system)

	shared_lua_system = gen.begin_class('std::shared_ptr<hg::LuaSystem>', bound_name='LuaSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(lua_system)})
	gen.add_base(shared_lua_system, shared_script_system)
	gen.bind_constructor(shared_lua_system, ['?std::shared_ptr<hg::ScriptEngineEnv> environment'], ['proxy'])
	gen.end_class(shared_lua_system)

	# hg::Node
	gen.bind_constructor_overloads(shared_node, [
		([], ['proxy']),
		(['const std::string &name'], ['proxy'])
	])

	gen.bind_method(shared_node, 'GetScene', 'std::shared_ptr<hg::Scene>', [], ['proxy'])
	gen.bind_method(shared_node, 'GetUid', 'uint32_t', [], ['proxy'])

	gen.bind_method(shared_node, 'GetName', 'const std::string &', [], ['proxy'])
	gen.bind_method(shared_node, 'SetName', 'void', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_node, 'AddComponent', 'void', ['std::shared_ptr<hg::Component> component'], ['proxy'])
	gen.bind_method(shared_node, 'RemoveComponent', 'void', ['const std::shared_ptr<hg::Component> &component'], ['proxy'])

	gen.bind_method_overloads(shared_node, 'GetComponents', [
		('const std::vector<std::shared_ptr<hg::Component>> &', [], ['proxy']),
		('std::vector<std::shared_ptr<hg::Component>>', ['const std::string &aspect'], ['proxy'])
	])

	gen.bind_method(shared_node, 'GetComponent<hg::Transform>', 'std::shared_ptr<hg::Transform>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetTransform failed, node has no Transform component')}, bound_name='GetTransform')
	gen.bind_method(shared_node, 'GetComponent<hg::Camera>', 'std::shared_ptr<hg::Camera>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetCamera failed, node has no Camera component')}, bound_name='GetCamera')
	gen.bind_method(shared_node, 'GetComponent<hg::Object>', 'std::shared_ptr<hg::Object>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetObject failed, node has no Object component')}, bound_name='GetObject')
	gen.bind_method(shared_node, 'GetComponent<hg::Light>', 'std::shared_ptr<hg::Light>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetLight failed, node has no Light component')}, bound_name='GetLight')
	gen.bind_method(shared_node, 'GetComponent<hg::Instance>', 'std::shared_ptr<hg::Instance>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetInstance failed, node has no Instance component')}, bound_name='GetInstance')
	gen.bind_method(shared_node, 'GetComponent<hg::Target>', 'std::shared_ptr<hg::Target>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetTarget failed, node has no Target component')}, bound_name='GetTarget')
	gen.bind_method(shared_node, 'GetComponent<hg::RigidBody>', 'std::shared_ptr<hg::RigidBody>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetRigidBody failed, node has no RigidBody component')}, bound_name='GetRigidBody')
	gen.bind_method(shared_node, 'GetComponent<hg::BoxCollision>', 'std::shared_ptr<hg::BoxCollision>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetBoxCollision failed, node has no BoxCollision component')}, bound_name='GetBoxCollision')
	gen.bind_method(shared_node, 'GetComponent<hg::SphereCollision>', 'std::shared_ptr<hg::SphereCollision>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetSphereCollision failed, node has no SphereCollision component')}, bound_name='GetSphereCollision')
	gen.bind_method(shared_node, 'GetComponent<hg::MeshCollision>', 'std::shared_ptr<hg::MeshCollision>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetMeshCollision failed, node has no MeshCollision component')}, bound_name='GetMeshCollision')
	gen.bind_method(shared_node, 'GetComponent<hg::CapsuleCollision>', 'std::shared_ptr<hg::CapsuleCollision>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetCapsuleCollision failed, node has no CapsuleCollision component')}, bound_name='GetCapsuleCollision')
	gen.bind_method(shared_node, 'GetComponent<hg::ConvexCollision>', 'std::shared_ptr<hg::ConvexCollision>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetConvexCollision failed, node has no ConvexCollision component')}, bound_name='GetConvexCollision')
	gen.bind_method(shared_node, 'GetComponent<hg::SphericalJoint>', 'std::shared_ptr<hg::SphericalJoint>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetSphericalJoint failed, node has no SphericalJoint component')}, bound_name='GetSphericalJoint')
	gen.bind_method(shared_node, 'GetComponent<hg::D6Joint>', 'std::shared_ptr<hg::D6Joint>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetD6Joint failed, node has no D6Joint component')}, bound_name='GetD6Joint')
	gen.bind_method(shared_node, 'GetComponent<hg::RenderScript>', 'std::shared_ptr<hg::RenderScript>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetRenderScript failed, node has no RenderScript component')}, bound_name='GetRenderScript')
	gen.bind_method(shared_node, 'GetComponent<hg::LogicScript>', 'std::shared_ptr<hg::LogicScript>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetLogicScript failed, node has no LogicScript component')}, bound_name='GetLogicScript')

	gen.bind_method(shared_node, 'HasAspect', 'bool', ['const std::string &aspect'], ['proxy'])
	gen.bind_method(shared_node, 'IsReady', 'bool', [], ['proxy'])

	gen.bind_method(shared_node, 'IsInstantiated', 'bool', [], ['proxy'])

	decl_get_set_method(shared_node, 'bool', 'Enabled', 'enable', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'IsStatic', 'is_static', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'DoNotSerialize', 'do_not_serialize', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'DoNotInstantiate', 'do_not_instantiate', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'UseForNavigation', 'use_for_navigation', features=['proxy'])

	gen.bind_method_overloads(shared_node, 'GetNode', [
		('std::shared_ptr<hg::Node>', ['uint32_t uid'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Node not found')}),
		('std::shared_ptr<hg::Node>', ['const std::string &name', '?const std::shared_ptr<hg::Node> &node'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Node not found')})
	])

	gen.end_class(shared_node)

	bind_std_vector(gen, shared_node)

	# hg::SceneSystem
	gen.bind_method(shared_scene_system, 'GetAspect', 'const std::string &', [], ['proxy'])

	#inline Type *GetConcreteType() const { return concrete_type; }

	gen.bind_method(shared_scene_system, 'Update', 'void', ['hg::time_ns dt'], ['proxy'])
	gen.bind_method_overloads(shared_scene_system, 'WaitUpdate', [
		('bool', [], ['proxy']),
		('bool', ['bool blocking'], ['proxy'])
	])
	gen.bind_method(shared_scene_system, 'Commit', 'void', [], ['proxy'])
	gen.bind_method_overloads(shared_scene_system, 'WaitCommit', [
		('bool', [], ['proxy']),
		('bool', ['bool blocking'], ['proxy'])
	])

	gen.bind_method(shared_scene_system, 'AddComponent', 'void', ['std::shared_ptr<hg::Component> component'], ['proxy'])
	gen.bind_method(shared_scene_system, 'RemoveComponent', 'void', ['const std::shared_ptr<hg::Component> &component'], ['proxy'])

	gen.bind_method(shared_scene_system, 'Cleanup', 'void', [], ['proxy'])

	gen.bind_method(shared_scene_system, 'SetDebugVisuals', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_scene_system, 'GetDebugVisuals', 'bool', [], ['proxy'])

	gen.bind_method(shared_scene_system, 'DrawDebugPanel', 'void', ['hg::RenderSystem &render_system'], ['proxy'])
	gen.bind_method(shared_scene_system, 'DrawDebugVisuals', 'void', ['hg::RenderSystem &render_system'], ['proxy'])

	gen.end_class(shared_scene_system)

	# hg::RenderableSystem
	gen.add_include('engine/renderable_system.h')

	renderable_system = gen.begin_class('hg::RenderableSystem', bound_name='RenderableSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(renderable_system)

	shared_renderable_system = gen.begin_class('std::shared_ptr<hg::RenderableSystem>', bound_name='RenderableSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(renderable_system)})
	gen.add_base(shared_renderable_system, shared_scene_system)

	gen.bind_constructor_overloads(shared_renderable_system, [
		(['std::shared_ptr<hg::RenderSystem> render_system'], ['proxy']),
		(['std::shared_ptr<hg::RenderSystem> render_system', 'bool async'], ['proxy'])
	])
	
	gen.bind_method(shared_renderable_system, 'SetFrameRenderer', 'void', ['std::shared_ptr<hg::FrameRenderer> renderer'], ['proxy'])
	gen.bind_method(shared_renderable_system, 'DrawGeometry', 'void', ['std::shared_ptr<hg::RenderGeometry> geometry', 'const hg::Matrix4 &world'], ['proxy'])
	gen.bind_method(shared_renderable_system, 'SetUseCameraView', 'void', ['bool use_camera_view'], ['proxy'])

	gen.end_class(shared_renderable_system)

	# hg::TransformSystem
	gen.add_include('engine/transform_system.h')

	transform_system = gen.begin_class('hg::TransformSystem', bound_name='TransformSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(transform_system)

	shared_transform_system = gen.begin_class('std::shared_ptr<hg::TransformSystem>', bound_name='TransformSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(transform_system)})
	gen.add_base(shared_transform_system, shared_scene_system)
	gen.bind_constructor(shared_transform_system, [], ['proxy'])

	gen.bind_method(shared_transform_system, 'ComputeTransform', 'void', ['hg::Transform &transform'], {'proxy': None, 'arg_out': ['transform']})
	gen.bind_method(shared_transform_system, 'CommitTransform', 'void', ['hg::Transform &transform'], ['proxy'])
	gen.bind_method(shared_transform_system, 'ResetWorldMatrix', 'void', ['const std::shared_ptr<hg::Transform> &transform', 'const hg::Matrix4 &m'], ['proxy'])
	gen.end_class(shared_transform_system)

	# hg::PhysicTrace
	gen.add_include('engine/physic_system.h')

	physic_trace = gen.begin_class('hg::PhysicTrace')
	gen.insert_binding_code('''\
static hg::Vector3 PhysicTraceGetPosition(hg::PhysicTrace *trace) { return trace->p; }
static hg::Vector3 PhysicTraceGetNormal(hg::PhysicTrace *trace) { return trace->n; }
static std::shared_ptr<hg::Node> PhysicTraceGetNode(hg::PhysicTrace *trace) { return trace->i->shared_from_this(); }
\n''', 'PhysicTrace extension')
	gen.bind_method(physic_trace, 'GetPosition', 'hg::Vector3', [], {'route': route_lambda('PhysicTraceGetPosition')})
	gen.bind_method(physic_trace, 'GetNormal', 'hg::Vector3', [], {'route': route_lambda('PhysicTraceGetNormal')})
	gen.bind_method(physic_trace, 'GetNode', 'std::shared_ptr<hg::Node>', [], {'route': route_lambda('PhysicTraceGetNode')})
	gen.end_class(physic_trace)

	# hg::PhysicSystem
	physic_system = gen.begin_class('hg::PhysicSystem', bound_name='PhysicSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(physic_system)

	shared_physic_system = gen.begin_class('std::shared_ptr<hg::PhysicSystem>', bound_name='PhysicSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(physic_system)})
	gen.add_base(shared_physic_system, shared_scene_system)

	gen.bind_method(shared_physic_system, 'GetImplementationName', 'const std::string &', [], ['proxy'])

	decl_get_set_method(shared_physic_system, 'float', 'Timestep', 'timestep', ['proxy'])
	decl_get_set_method(shared_physic_system, 'bool', 'ForceRigidBodyToSleepOnCreation', 'force_sleep_body', ['proxy'])
	decl_get_set_method(shared_physic_system, 'uint32_t', 'ForceRigidBodyAxisLockOnCreation', 'force_axis_lock', ['proxy'])

	decl_get_set_method(shared_physic_system, 'hg::Vector3', 'Gravity', 'G', ['proxy'])

	gen.bind_method_overloads(shared_physic_system, 'Raycast', [
		('bool', ['const hg::Vector3 &start', 'const hg::Vector3 &direction', 'hg::PhysicTrace &hit'], {'proxy': None, 'arg_out': ['hit']}),
		('bool', ['const hg::Vector3 &start', 'const hg::Vector3 &direction', 'hg::PhysicTrace &hit', 'uint8_t collision_layer_mask'], {'proxy': None, 'arg_out': ['hit']}),
		('bool', ['const hg::Vector3 &start', 'const hg::Vector3 &direction', 'hg::PhysicTrace &hit', 'uint8_t collision_layer_mask', 'float max_distance'], {'proxy': None, 'arg_out': ['hit']})
	])

	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'bool', 'RigidBodyIsSleeping', 'sleeping', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'hg::Vector3', 'RigidBodyAngularVelocity', 'W', ['proxy'])
	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'hg::Vector3', 'RigidBodyLinearVelocity', 'V', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'float', 'RigidBodyLinearDamping', 'k', ['proxy'])
	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'float', 'RigidBodyAngularDamping', 'k', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'float', 'RigidBodyStaticFriction', 'static_friction', ['proxy'])
	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'float', 'RigidBodyDynamicFriction', 'dynamic_friction', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'float', 'RigidBodyRestitution', 'restitution', ['proxy'])

	#decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'hg::RigidBodyType', 'RigidBodyType', 'type', ['proxy'])

	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'uint8_t', 'RigidBodyAxisLock', 'axis_lock', ['proxy'])
	decl_comp_get_set_method(shared_physic_system, 'hg::RigidBody', 'rigid_body', 'uint8_t', 'RigidBodyCollisionLayer', 'layer', ['proxy'])

	gen.bind_method(shared_physic_system, 'GetRigidBodyVelocity', 'hg::Vector3', ['const hg::RigidBody *body', 'const hg::Vector3 &p'], ['proxy'])
	gen.bind_method(shared_physic_system, 'SetRigidBodyVelocity', 'void', ['hg::RigidBody *body', 'const hg::Vector3 &V', 'const hg::Vector3 &p'], ['proxy'])

	gen.bind_method(shared_physic_system, 'RigidBodyApplyLinearImpulse', 'void', ['hg::RigidBody *body', 'const hg::Vector3 &I'], ['proxy'])
	gen.bind_method(shared_physic_system, 'RigidBodyApplyLinearForce', 'void', ['hg::RigidBody *body', 'const hg::Vector3 &F'], ['proxy'])
	gen.bind_method(shared_physic_system, 'RigidBodyApplyTorque', 'void', ['hg::RigidBody *body', 'const hg::Vector3 &T'], ['proxy'])

	gen.bind_method(shared_physic_system, 'RigidBodyApplyImpulse', 'void', ['hg::RigidBody *body', 'const hg::Vector3 &I', 'const hg::Vector3 &p'], ['proxy'])
	gen.bind_method(shared_physic_system, 'RigidBodyApplyForce', 'void', ['hg::RigidBody *body', 'const hg::Vector3 &F', 'const hg::Vector3 &p'], ['proxy'])

	gen.bind_method(shared_physic_system, 'RigidBodyResetWorld', 'void', ['hg::RigidBody *body', 'const hg::Matrix4 &M'], ['proxy'])

	# hg::CollisionPair
	gen.insert_binding_code('''\
static std::shared_ptr<hg::Node> _CollisionPair_GetNodeA(hg::CollisionPair *pair) { return pair->a; }
static std::shared_ptr<hg::Node> _CollisionPair_GetNodeB(hg::CollisionPair *pair) { return pair->b; }

static uint8_t _CollisionPair_GetContactCount(hg::CollisionPair *pair) { return pair->contact_count; }
static hg::Vector3 _CollisionPair_GetContactPosition(hg::CollisionPair *pair, uint32_t idx) { return idx < pair->contact_count ? pair->contact[idx].p : hg::Vector3::Zero; }
static hg::Vector3 _CollisionPair_GetContactNormal(hg::CollisionPair *pair, uint32_t idx) { return idx < pair->contact_count ? pair->contact[idx].n : hg::Vector3::Zero; }
	''')

	collision_pair = gen.begin_class('hg::CollisionPair')
	gen.bind_method(collision_pair, 'GetNodeA', 'std::shared_ptr<hg::Node>', [], {'route': route_lambda('_CollisionPair_GetNodeA')})
	gen.bind_method(collision_pair, 'GetNodeB', 'std::shared_ptr<hg::Node>', [], {'route': route_lambda('_CollisionPair_GetNodeB')})
	gen.bind_method(collision_pair, 'GetContactCount', 'uint8_t', [], {'route': route_lambda('_CollisionPair_GetContactCount')})
	gen.bind_method(collision_pair, 'GetContactPosition', 'hg::Vector3', ['uint32_t idx'], {'route': route_lambda('_CollisionPair_GetContactPosition')})
	gen.bind_method(collision_pair, 'GetContactNormal', 'hg::Vector3', ['uint32_t idx'], {'route': route_lambda('_CollisionPair_GetContactNormal')})
	gen.end_class(collision_pair)

	bind_std_vector(gen, collision_pair)

	gen.bind_method_overloads(shared_physic_system, 'GetCollisionPairs', [
		('const std::vector<hg::CollisionPair> &', [], ['proxy']),
		('std::vector<hg::CollisionPair>', ['const std::shared_ptr<hg::Node> &node'], ['proxy'])
	])

	gen.bind_method_overloads(shared_physic_system, 'HasCollided', [
		('bool', ['const std::shared_ptr<hg::Node> &node'], ['proxy']),
		('bool', ['const std::shared_ptr<hg::Node> &node_a', 'const std::shared_ptr<hg::Node> &node_b'], ['proxy'])
	])

	gen.bind_method(shared_physic_system, 'SetCollisionLayerPairState', 'void', ['uint16_t layer_a', 'uint16_t layer_b', 'bool enable_collision'], ['proxy'])
	gen.bind_method(shared_physic_system, 'GetCollisionLayerPairState', 'bool', ['uint16_t layer_a', 'uint16_t layer_b'], ['proxy'])

	gen.end_class(shared_physic_system)

	gen.insert_binding_code('''static std::shared_ptr<hg::PhysicSystem> CreatePhysicSystem(const std::string &name) { return hg::g_physic_system_factory.get().Instantiate(name); }
static std::shared_ptr<hg::PhysicSystem> CreatePhysicSystem() { return hg::g_physic_system_factory.get().Instantiate(); }
	''', 'Physic system custom API')

	gen.bind_function('CreatePhysicSystem', 'std::shared_ptr<hg::PhysicSystem>', ['?const std::string &name'], {'check_rval': check_bool_rval_lambda(gen, 'CreatePhysicSystem failed, was LoadPlugins called succesfully?')})

	# hg::NavigationPath
	gen.add_include('engine/navigation_system.h')

	navigation_path = gen.begin_class('hg::NavigationPath')
	gen.bind_member(navigation_path, 'const std::vector<hg::Vector3> point')
	gen.end_class(navigation_path)

	# hg::NavigationLayer
	navigation_layer = gen.begin_class('hg::NavigationLayer')
	gen.bind_members(navigation_layer, ['float radius', 'float height', 'float slope'])
	gen.bind_comparison_ops(navigation_layer, ['==', '!='], ['const hg::NavigationLayer &layer'])
	gen.end_class(navigation_layer)

	bind_std_vector(gen, navigation_layer)

	# hg::NavigationConfig
	navigation_config = gen.begin_class('hg::NavigationConfig')
	gen.bind_member(navigation_config, 'std::vector<hg::NavigationLayer> layers')
	gen.end_class(navigation_config)

	# hg::NavigationSystem
	navigation_system = gen.begin_class('hg::NavigationSystem', bound_name='NavigationSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(navigation_system)

	shared_navigation_system = gen.begin_class('std::shared_ptr<hg::NavigationSystem>', bound_name='NavigationSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(navigation_system)})
	gen.add_base(shared_navigation_system, shared_scene_system)

	gen.bind_constructor(shared_navigation_system, [], ['proxy'])
	gen.bind_method_overloads(shared_navigation_system, 'FindPathTo', [
		('bool', ['const hg::Vector3 &from', 'const hg::Vector3 &to', 'hg::NavigationPath &path'], ['proxy']),
		('bool', ['const hg::Vector3 &from', 'const hg::Vector3 &to', 'hg::NavigationPath &path', 'uint32_t layer_index'], ['proxy'])
	])
	gen.bind_method(shared_navigation_system, 'GetConfig', 'const hg::NavigationConfig &', [], ['proxy'])
	gen.end_class(shared_navigation_system)

	# hg::NavigationGeometry
	navigation_geometry = gen.begin_class('hg::NavigationGeometry', bound_name='NavigationGeometry_nobind', noncopyable=True, nobind=True)
	gen.end_class(navigation_geometry)

	shared_navigation_geometry = gen.begin_class('std::shared_ptr<hg::NavigationGeometry>', bound_name='NavigationGeometry', features={'proxy': lib.stl.SharedPtrProxyFeature(navigation_geometry)})
	gen.bind_method(shared_navigation_geometry, 'GetConfig', 'const hg::NavigationConfig &', [], ['proxy'])
	gen.bind_method(shared_navigation_geometry, 'GetMinMax', 'const hg::MinMax &',  [], ['proxy'])
#	gen.bind_method(navigation_geometry, 'GetLayers', 'const std::vector<Layer> &', [])
	gen.end_class(shared_navigation_geometry)

	gen.bind_function('hg::CreateNavigationGeometry', 'std::shared_ptr<hg::NavigationGeometry>', ['const hg::Geometry &geo', 'const hg::NavigationConfig &cfg'])

	# hg::Navigation
	gen.add_include('engine/navigation.h')
	navigation = gen.begin_class('hg::Navigation', bound_name='Navigation_nobind', noncopyable=True, nobind=True)
	gen.end_class(navigation)

	shared_navigation = gen.begin_class('std::shared_ptr<hg::Navigation>', bound_name='Navigation', features={'proxy': lib.stl.SharedPtrProxyFeature(navigation)})
	gen.add_base(shared_navigation, shared_component)
	gen.bind_constructor(shared_navigation, [], ['proxy'])
	decl_get_set_method(shared_navigation, 'std::shared_ptr<hg::NavigationGeometry>', 'Geometry', 'geometry', ['proxy'])
	gen.bind_method(shared_navigation, 'FindPathTo', 'bool', ['const hg::Vector3 &from', 'const hg::Vector3 &to', 'hg::NavigationPath &path', '?uint32_t layer_index'],  {'proxy': None, 'arg_out': ['path']})
	gen.end_class(shared_navigation)

	# hg::Group
	gen.add_include('engine/group.h')

	group = gen.begin_class('hg::Group', bound_name='Group_nobind', noncopyable=True, nobind=True)
	gen.end_class(group)

	shared_group = gen.begin_class('std::shared_ptr<hg::Group>', bound_name='Group', features={'proxy': lib.stl.SharedPtrProxyFeature(group)})

	std_vector_shared_group = gen.begin_class('std::vector<std::shared_ptr<hg::Group>>', bound_name='GroupList', features={'sequence': lib.std.VectorSequenceFeature(shared_group)})
	gen.end_class(std_vector_shared_group)

	gen.bind_method(shared_group, 'GetNodes', 'const std::vector<std::shared_ptr<hg::Node>> &', [], ['proxy'])
	gen.bind_method(shared_group, 'GetGroups', 'const std::vector<std::shared_ptr<hg::Group>> &', [], ['proxy'])

	gen.bind_method(shared_group, 'AddNode', 'void', ['std::shared_ptr<hg::Node> node'], ['proxy'])
	gen.bind_method(shared_group, 'RemoveNode', 'void', ['const std::shared_ptr<hg::Node> &node'], ['proxy'])
	gen.bind_method_overloads(shared_group, 'IsMember', [
		('bool', ['const std::shared_ptr<hg::Node> &node'], ['proxy']),
		('bool', ['const std::shared_ptr<hg::Group> &group'], ['proxy'])
	])

	gen.bind_method(shared_group, 'IsReady', 'bool', [], ['proxy'])

	gen.bind_method_overloads(shared_group, 'GetNode', [
		('std::shared_ptr<hg::Node>', ['uint32_t uid'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Node not found')}),
		('std::shared_ptr<hg::Node>', ['const std::string &name', '?const std::shared_ptr<hg::Node> &parent'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Node not found')})
	])

	gen.bind_method(shared_group, 'AddGroup', 'void', ['std::shared_ptr<hg::Group> group'], ['proxy'])
	gen.bind_method(shared_group, 'RemoveGroup', 'void', ['const std::shared_ptr<hg::Group> &group'], ['proxy'])

	gen.bind_method(shared_group, 'GetGroup', 'std::shared_ptr<hg::Group>', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_group, 'AppendGroup', 'void', ['const hg::Group &group'], ['proxy'])

	gen.bind_method(shared_group, 'GetName', 'const std::string &', [], ['proxy'])
	gen.bind_method(shared_group, 'SetName', 'void', ['const std::string &name'], ['proxy'])

	gen.end_class(shared_group)

	# hg::Scene
	gen.bind_constructor(shared_scene, [], ['proxy'])

	gen.bind_method(shared_scene, 'GetCurrentCamera', 'const std::shared_ptr<hg::Node> &', [], ['proxy'])
	gen.bind_method(shared_scene, 'SetCurrentCamera', 'void', ['std::shared_ptr<hg::Node> node'], ['proxy'])

	gen.bind_method(shared_scene, 'AddGroup', 'void', ['std::shared_ptr<hg::Group> group'], ['proxy'])
	gen.bind_method(shared_scene, 'RemoveGroup', 'void', ['const std::shared_ptr<hg::Group> &group'], ['proxy'])
	gen.bind_method(shared_scene, 'FindGroup', 'std::shared_ptr<hg::Group>', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_scene, 'GetNodeGroupList', 'std::vector<std::shared_ptr<hg::Group>>', ['const std::shared_ptr<hg::Node> &node'], ['proxy'])
	gen.bind_method(shared_scene, 'UnregisterNodeFromGroups', 'void', ['const std::shared_ptr<hg::Node> &node'], ['proxy'])
	gen.bind_method(shared_scene, 'GetGroups', 'const std::vector<std::shared_ptr<hg::Group>> &', [], ['proxy'])

	gen.bind_method(shared_scene, 'GroupMembersSetActive', 'void', ['const hg::Group &group', 'bool active'], ['proxy'])
	gen.bind_method(shared_scene, 'DeleteGroupAndMembers', 'void', ['const std::shared_ptr<hg::Group> &group'], ['proxy'])

	gen.bind_method(shared_scene, 'Clear', 'void', [], ['proxy'])
	gen.bind_method(shared_scene, 'Dispose', 'void', [], ['proxy'])
	gen.bind_method(shared_scene, 'IsReady', 'bool', [], ['proxy'])

	gen.bind_method(shared_scene, 'AddSystem', 'void', ['std::shared_ptr<hg::SceneSystem> system'], ['proxy'])
	#gen.bind_method(shared_scene, 'GetSystem', 'std::shared_ptr<hg::SceneSystem>', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_scene, 'GetSystem<hg::RenderableSystem>', 'std::shared_ptr<hg::RenderableSystem>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'No renderable system in scene')}, bound_name='GetRenderableSystem')
	gen.bind_method(shared_scene, 'GetSystem<hg::PhysicSystem>', 'std::shared_ptr<hg::PhysicSystem>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'No physic system in scene')}, bound_name='GetPhysicSystem')

	#const std::vector<std::shared_ptr<SceneSystem>> &GetSystems() const { return systems; }

	gen.bind_method(shared_scene, 'AddNode', 'void', ['std::shared_ptr<hg::Node> node'], ['proxy'])
	gen.bind_method(shared_scene, 'RemoveNode', 'void', ['const std::shared_ptr<hg::Node> &node'], ['proxy'])

	gen.bind_method(shared_scene, 'AddComponentToSystems', 'void', ['std::shared_ptr<hg::Component> node'], ['proxy'])
	gen.bind_method(shared_scene, 'RemoveComponentFromSystems', 'void', ['const std::shared_ptr<hg::Component> &component'], ['proxy'])

	gen.bind_method_overloads(shared_scene, 'GetNode', [
		('std::shared_ptr<hg::Node>', ['uint32_t uid'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Node not found')}),
		('std::shared_ptr<hg::Node>', ['const std::string &name', '?const std::shared_ptr<hg::Node> &parent'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Node not found')})
	])

	gen.bind_method_overloads(shared_scene, 'GetNodes', [
		('const std::vector<std::shared_ptr<hg::Node>> &', [], ['proxy']),
		('std::vector<std::shared_ptr<hg::Node>>', ['const std::string &filter'], ['proxy'])
	])
	gen.bind_method(shared_scene, 'GetNodeChildren', 'std::vector<std::shared_ptr<hg::Node>>', ['const hg::Node &node'], ['proxy'])
	gen.bind_method(shared_scene, 'GetNodesWithAspect', 'std::vector<std::shared_ptr<hg::Node>>', ['const std::string &aspect'], ['proxy'])

	gen.insert_binding_code('static bool _Scene_Load(hg::Scene *scene, const std::string &path, std::shared_ptr<hg::RenderSystem> &render_system, std::vector<std::shared_ptr<hg::Node>> *nodes) { return hg::LoadScene(*scene, path, render_system, nodes); }')
	gen.bind_method(shared_scene, 'Load', 'bool', ['const std::string &path', 'std::shared_ptr<hg::RenderSystem> &render_system', 'std::vector<std::shared_ptr<hg::Node>> *nodes'], {'proxy': None, 'route': route_lambda('_Scene_Load'), 'arg_out': ['nodes']})
	gen.insert_binding_code('static bool _Scene_Save(hg::Scene *scene, const std::string &path, std::shared_ptr<hg::RenderSystem> &render_system) { return hg::SaveScene(*scene, path, render_system); }')
	gen.bind_method(shared_scene, 'Save', 'bool', ['const std::string &path', 'std::shared_ptr<hg::RenderSystem> &render_system'], {'proxy': None, 'route': route_lambda('_Scene_Save')})

	gen.bind_method_overloads(shared_scene, 'Update', [
		('void', [], ['proxy']),
		('void', ['hg::time_ns dt'], ['proxy'])
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
		('void', ['hg::time_ns dt'], ['proxy'])
	])

	#const Signal<void(SceneSerializationState &)> &GetSerializationSignal() const { return serialization_signal; }
	#Signal<void(SceneSerializationState &)> &GetSerializationSignal() { return serialization_signal; }

	#const Signal<void(SceneDeserializationState &)> &GetDeserializationSignal() const { return deserialization_signal; }
	#Signal<void(SceneDeserializationState &)> &GetDeserializationSignal() { return deserialization_signal; }

	gen.bind_method(shared_scene, 'AddComponent', 'void', ['std::shared_ptr<hg::Component> component'], ['proxy'])
	gen.bind_method(shared_scene, 'RemoveComponent', 'void', ['const std::shared_ptr<hg::Component> &component'], ['proxy'])

	gen.bind_method_overloads(shared_scene, 'GetComponents', [
		('const std::vector<std::shared_ptr<hg::Component>> &', [], ['proxy']),
		('std::vector<std::shared_ptr<hg::Component>>', ['const std::string &aspect'], ['proxy'])
	])

	gen.bind_method(shared_scene, 'GetComponent<hg::Environment>', 'std::shared_ptr<hg::Environment>', [], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'GetEnvironment failed, scene has no Environment component')}, bound_name='GetEnvironment')

	gen.bind_method(shared_scene, 'HasAspect', 'bool', ['const std::string &aspect'], ['proxy'])
	gen.bind_method(shared_scene, 'GetMinMax', 'hg::MinMax', [], ['proxy'])

	gen.end_class(shared_scene)

	# global functions
	gen.bind_function('hg::NewDefaultScene', 'std::shared_ptr<hg::Scene>', ['std::shared_ptr<hg::RenderSystem> render_system'])
	#gen.bind_function('hg::LoadScene', 'bool', ['hg::Scene &scene', 'const std::string &path', 'std::shared_ptr<hg::RenderSystem> render_system'])
	gen.bind_function('hg::SceneSetupCoreSystemsAndComponents', 'void', ['std::shared_ptr<hg::Scene> scene', 'std::shared_ptr<hg::RenderSystem> render_system'])

	# hg::ScenePicking
	gen.add_include('engine/scene_picking.h')

	scene_picking = gen.begin_class('hg::ScenePicking')

	gen.bind_constructor_overloads(scene_picking, [
		(['std::shared_ptr<hg::RenderSystem> render_system'], [])
	])
	gen.bind_method(scene_picking, 'Prepare', 'std::future<bool>', ['std::shared_ptr<hg::Scene> scene', 'bool prepare_node_picking', 'bool prepare_world_picking'] )
	gen.bind_method_overloads(scene_picking, 'Pick', [
		('bool', ['const hg::Scene &scene', 'int x', 'int y', 'std::vector<std::shared_ptr<hg::Node>> &nodes'], {'arg_out': ['nodes']}),
		('bool', ['const hg::Scene &scene', 'const hg::Rect<int> &rect', 'std::vector<std::shared_ptr<hg::Node>> &nodes'], {'arg_out': ['nodes']})
	])
	
	gen.bind_method(scene_picking, 'PickWorld', 'bool', ['const hg::Scene &scene', 'float x', 'float y', 'hg::Vector3 &world_pos'], {'arg_out': ['world_pos']})
	gen.end_class(scene_picking)


def bind_gpu(gen):
	# types
	gen.add_include('engine/gpu_types.h')

	gen.bind_named_enum('hg::GpuPrimitiveType', ['GpuPrimitiveLine', 'GpuPrimitiveTriangle', 'GpuPrimitivePoint', 'GpuPrimitiveLast'], storage_type='uint8_t')

	# hg::GpuBuffer
	gen.add_include('engine/gpu_buffer.h')

	gen.bind_named_enum('hg::GpuBufferUsage', ['GpuBufferStatic', 'GpuBufferDynamic'])
	gen.bind_named_enum('hg::GpuBufferType', ['GpuBufferIndex', 'GpuBufferVertex'])

	buffer = gen.begin_class('hg::GpuBuffer', bound_name='Buffer_nobind', noncopyable=True, nobind=True)
	gen.end_class(buffer)

	shared_buffer = gen.begin_class('std::shared_ptr<hg::GpuBuffer>', bound_name='GpuBuffer', features={'proxy': lib.stl.SharedPtrProxyFeature(buffer)})
	gen.end_class(shared_buffer)

	# hg::GpuResource
	gen.add_include('engine/gpu_resource.h')

	resource = gen.begin_class('hg::GpuResource', bound_name='GpuResource_nobind', noncopyable=True, nobind=True)
	gen.end_class(resource)

	shared_resource = gen.begin_class('std::shared_ptr<hg::GpuResource>', bound_name='GpuResource', features={'proxy': lib.stl.SharedPtrProxyFeature(resource)})

	gen.bind_method(shared_resource, 'GetName', 'const std::string &', [], ['proxy'])

	gen.bind_method(shared_resource, 'IsReadyOrFailed', 'bool', [], ['proxy'])
	gen.bind_method(shared_resource, 'IsReady', 'bool', [], ['proxy'])
	gen.bind_method(shared_resource, 'IsFailed', 'bool', [], ['proxy'])

	gen.bind_method(shared_resource, 'SetReady', 'void', [], ['proxy'])
	gen.bind_method(shared_resource, 'SetFailed', 'void', [], ['proxy'])
	gen.bind_method(shared_resource, 'SetNotReady', 'void', [], ['proxy'])

	gen.end_class(shared_resource)

	# hg::Texture
	gen.add_include('engine/texture.h')

	gen.bind_named_enum('hg::TextureUsage', ['TextureIsRenderTarget', 'TextureIsShaderResource', 'TextureUsageDefault'])
	gen.bind_named_enum('hg::TextureFormat', ['TextureRGBA8', 'TextureBGRA8', 'TextureRGBA16', 'TextureRGBAF', 'TextureDepth', 'TextureDepthF', 'TextureR8', 'TextureR16', 'TextureInvalidFormat'], 'uint8_t')
	gen.bind_named_enum('hg::TextureAA', ['TextureNoAA', 'TextureMSAA2x', 'TextureMSAA4x', 'TextureMSAA8x', 'TextureMSAA16x', 'TextureAALast'], 'uint8_t')

	texture = gen.begin_class('hg::Texture', bound_name='Texture_nobind', noncopyable=True, nobind=True)
	gen.end_class(texture)

	shared_texture = gen.begin_class('std::shared_ptr<hg::Texture>', bound_name='Texture', features={'proxy': lib.stl.SharedPtrProxyFeature(texture)})

	gen.add_base(shared_texture, shared_resource)

	gen.bind_method(shared_texture, 'GetWidth', 'uint32_t', [], ['proxy'])
	gen.bind_method(shared_texture, 'GetHeight', 'uint32_t', [], ['proxy'])
	gen.bind_method(shared_texture, 'GetDepth', 'uint32_t', [], ['proxy'])
	gen.bind_method(shared_texture, 'GetRect', 'hg::Rect<float>', [], ['proxy'])

	gen.end_class(shared_texture)

	bind_std_vector(gen, shared_texture)

	# hg::RenderTarget
	render_target = gen.begin_class('hg::RenderTarget', bound_name='RenderTarget_nobind', noncopyable=True, nobind=True)
	gen.end_class(render_target)

	gen.insert_binding_code('''\
static std::shared_ptr<hg::Texture> _RenderTarget_GetDepthTexture(hg::RenderTarget *renderTarget) { return renderTarget->depth_texture; }
static uint32_t _RenderTarget_GetColorTextureCount(hg::RenderTarget *renderTarget) { return renderTarget->color_texture_count; }
static std::shared_ptr<hg::Texture> _RenderTarget_GetColorTexture(hg::RenderTarget *renderTarget, uint32_t idx) {
	return (idx < renderTarget->color_texture.size()) ? renderTarget->color_texture[idx] : nullptr;
}
''')

	shared_render_target = gen.begin_class('std::shared_ptr<hg::RenderTarget>', bound_name='RenderTarget', features={'proxy': lib.stl.SharedPtrProxyFeature(render_target)})
	gen.bind_method(shared_render_target, 'GetColorTextureCount', 'uint32_t', [], {'proxy': None, 'route': route_lambda('_RenderTarget_GetColorTextureCount')})
	gen.bind_method(shared_render_target, 'GetDepthTexture', 'std::shared_ptr<hg::Texture>', [], {'proxy': None, 'route': route_lambda('_RenderTarget_GetDepthTexture')})
	gen.bind_method(shared_render_target, 'GetColorTexture', 'std::shared_ptr<hg::Texture>', ['uint32_t index'], {'proxy': None, 'route': route_lambda('_RenderTarget_GetColorTexture')})
	gen.end_class(shared_render_target)
	
	# hg::GpuHardwareInfo
	hw_info = gen.begin_class('hg::GpuHardwareInfo')
	gen.bind_members(hw_info, ['std::string name', 'std::string vendor'])
	gen.end_class(hw_info)

	# hg::GpuShader
	gen.add_include('engine/gpu_shader.h')

	shader = gen.begin_class('hg::GpuShader', bound_name='GpuShader_nobind', noncopyable=True, nobind=True)
	gen.end_class(shader)

	shared_shader = gen.begin_class('std::shared_ptr<hg::GpuShader>', bound_name='GpuShader', features={'proxy': lib.stl.SharedPtrProxyFeature(shader)})
	gen.add_base(shared_shader, shared_resource)
	gen.end_class(shared_shader)

	lib.stl.bind_future_T(gen, 'std::shared_ptr<hg::GpuShader>', 'FutureGpuShader')

	shader_value = gen.begin_class('hg::GpuShaderValue', bound_name='GpuShaderValue')
	gen.bind_members(shader_value, ['std::shared_ptr<hg::Texture> texture', 'hg::TextureUnitConfig tex_unit_cfg'])
	gen.end_class(shader_value)

	shader_variable = gen.begin_class('hg::GpuShaderVariable')
	gen.end_class(shader_variable)

	# hg::ResourceCache<T>
	gen.add_include("engine/resource_cache.h")

	def bind_tcache_T(T, bound_name):
		tcache = gen.begin_class('hg::ResourceCache<%s>'%T, bound_name=bound_name, noncopyable=True)

		gen.bind_method(tcache, 'Purge', 'size_t', [])

		gen.bind_method(tcache, 'Clear', 'void', [])
		gen.bind_method(tcache, 'Has', 'bool', ['const std::string &name'])
		gen.bind_method(tcache, 'Get', 'std::shared_ptr<%s>'%T, ['const std::string &name'])

		gen.bind_method(tcache, 'Add', 'void', ['std::shared_ptr<%s> &resource'%T])
		#const std::vector<std::shared_ptr<T>> &GetContent() const { return cache; }

		gen.end_class(tcache)

	bind_tcache_T('hg::Texture', 'TextureCache')
	bind_tcache_T('hg::GpuShader', 'ShaderCache')

	# hg::Renderer
	gen.add_include('engine/renderer.h')

	gen.bind_named_enum('hg::Renderer::FillMode', ['FillSolid', 'FillWireframe', 'FillLast'])
	gen.bind_named_enum('hg::Renderer::CullFunc', ['CullFront', 'CullBack', 'CullLast'])
	gen.bind_named_enum('hg::Renderer::DepthFunc', ['DepthNever', 'DepthLess', 'DepthEqual', 'DepthLessEqual', 'DepthGreater', 'DepthNotEqual', 'DepthGreaterEqual', 'DepthAlways', 'DepthFuncLast'])
	gen.bind_named_enum('hg::Renderer::BlendFunc', ['BlendZero', 'BlendOne', 'BlendSrcAlpha', 'BlendOneMinusSrcAlpha', 'BlendDstAlpha', 'BlendOneMinusDstAlpha', 'BlendLast'])
	gen.bind_named_enum('hg::Renderer::ClearFunction', ['ClearColor', 'ClearDepth', 'ClearAll'])

	renderer = gen.begin_class('hg::Renderer', bound_name='Renderer_nobind', noncopyable=True, nobind=True)
	gen.end_class(renderer)

	shared_renderer = gen.begin_class('std::shared_ptr<hg::Renderer>', bound_name='Renderer', features={'proxy': lib.stl.SharedPtrProxyFeature(renderer)})

	gen.bind_method(shared_renderer, 'GetName', 'const char *', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetDescription', 'const char *', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetVersion', 'const char *', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetNativeHandle', 'void *', [], ['proxy'])

	gen.bind_method(shared_renderer, 'GetHardwareInfo', 'const hg::GpuHardwareInfo &', [], ['proxy'])

	gen.bind_method(shared_renderer, 'PurgeCache', 'size_t', [], ['proxy'])
	gen.bind_method(shared_renderer, 'RefreshCacheEntry', 'void', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_renderer, 'IsCooked', 'bool', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_renderer, 'GetTextureCache', 'const hg::ResourceCache<hg::Texture> &', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetShaderCache', 'const hg::ResourceCache<hg::GpuShader> &', [], ['proxy'])

	"""
	Signal<void(Renderer &)> open_signal, close_signal;
	Signal<void(Renderer &, const Surface &)> output_surface_created_signal;
	Signal<void(Renderer &, const Surface &)> output_surface_changed_signal;
	Signal<void(Renderer &, const Surface &)> output_surface_destroyed_signal;

	Signal<void(Renderer &)> pre_draw_frame_signal, post_draw_frame_signal;
	Signal<void(Renderer &)> show_frame_signal;
	"""

	gen.bind_method(shared_renderer, 'NewRenderTarget', 'std::shared_ptr<hg::RenderTarget>', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'SetRenderTargetColorTexture', [
		('void', ['hg::RenderTarget &render_target', 'std::shared_ptr<hg::Texture> texture'], ['proxy'])
		#('void', ['hg::RenderTarget &render_target', 'std::shared_ptr<hg::Texture> texture *', 'uint32_t count'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'SetRenderTargetDepthTexture', 'void', ['hg::RenderTarget &render_target', 'std::shared_ptr<hg::Texture> texture'], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'BlitRenderTarget', [
		('void', ['const std::shared_ptr<hg::RenderTarget> &src_render_target', 'const std::shared_ptr<hg::RenderTarget> &dst_render_target', 'const hg::Rect<int> &src_rect', 'const hg::Rect<int> &dst_rect'], ['proxy']),
		('void', ['const std::shared_ptr<hg::RenderTarget> &src_render_target', 'const std::shared_ptr<hg::RenderTarget> &dst_render_target', 'const hg::Rect<int> &src_rect', 'const hg::Rect<int> &dst_rect', 'bool blit_color', 'bool blit_depth'], ['proxy'])
	])
	#gen.bind_method(shared_renderer, 'ReadRenderTargetColorPixels', 'void', ['const std::shared_ptr<hg::RenderTarget> &src_render_target', 'const std::shared_ptr<hg::Picture> &out', 'const hg::Rect<int> &rect'], ['proxy'])
	gen.bind_method(shared_renderer, 'ClearRenderTarget', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetRenderTarget', 'const std::shared_ptr<hg::RenderTarget> &', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetRenderTarget', 'void', ['std::shared_ptr<hg::RenderTarget> render_target'], ['proxy'])
	gen.bind_method(shared_renderer, 'CheckRenderTarget', 'bool', [], ['proxy'])

	gen.bind_method(shared_renderer, 'CreateRenderTarget', 'bool', ['hg::RenderTarget &render_target'], ['proxy'])
	gen.bind_method(shared_renderer, 'FreeRenderTarget', 'void', ['hg::RenderTarget &render_target'], ['proxy'])

	gen.bind_method(shared_renderer, 'NewBuffer', 'std::shared_ptr<hg::GpuBuffer>', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetBufferSize', 'size_t', ['hg::GpuBuffer &buffer'], ['proxy'])
	#std::future<void *> MapBuffer(sBuffer buf) {
	#void UnmapBuffer(sBuffer buf) { run_call<void>(std::bind(&Renderer::UnmapBuffer, shared_ref(renderer), shared_ref(buf)), RA_task_affinity); }
	#std::future<bool> UpdateBuffer(sBuffer buf, const void *p, size_t start = 0, size_t size = 0) {
	#std::future<bool> CreateBuffer(sBuffer buf, const void *data, size_t size, Buffer::Type type, Buffer::Usage usage = Buffer::Static) {
	#std::future<bool> CreateBuffer(sBuffer buf, const BinaryData &data, Buffer::Type type, Buffer::Usage usage = Buffer::Static) {

	gen.insert_binding_code('''\
static bool _CreateBuffer(hg::Renderer *renderer, hg::GpuBuffer &buffer, hg::BinaryData &data, hg::GpuBufferType type, hg::GpuBufferUsage usage = hg::GpuBufferStatic) {
	return renderer->CreateBuffer(buffer, data.GetData(), data.GetDataSize(), type, usage);
}
''')
	gen.bind_method(shared_renderer, 'CreateBuffer', 'void', ['hg::GpuBuffer &buffer', 'hg::BinaryData &data', 'hg::GpuBufferType type', '?hg::GpuBufferUsage usage'], {'proxy': None, 'route': lambda args: '_CreateBuffer(%s);' % ', '.join(args)})
	gen.bind_method(shared_renderer, 'FreeBuffer', 'void', ['hg::GpuBuffer &buffer'], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'NewTexture', [
		('std::shared_ptr<hg::Texture>', [], ['proxy']),
		('std::shared_ptr<hg::Texture>', ['const std::string &name'], ['proxy']),
		('std::shared_ptr<hg::Texture>', ['const std::string &name', 'int width', 'int height'], ['proxy']),
		('std::shared_ptr<hg::Texture>', ['const std::string &name', 'int width', 'int height', 'hg::TextureFormat format', 'hg::TextureAA aa', '?hg::TextureUsage usage', '?bool mipmapped'], ['proxy']),
		('std::shared_ptr<hg::Texture>', ['const std::string &name', 'const hg::Picture &picture', '?hg::TextureUsage usage', '?bool mipmapped'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'NewShadowMap', 'std::shared_ptr<hg::Texture>', ['int width', 'int height', '?const std::string &name'], ['proxy'])
	gen.bind_method(shared_renderer, 'NewExternalTexture', 'std::shared_ptr<hg::Texture>', ['?const std::string &name'], ['proxy'])
	gen.bind_method_overloads(shared_renderer, 'CreateTexture', [
		('bool', ['hg::Texture &texture', 'int width', 'int height', '?hg::TextureFormat format', '?hg::TextureAA aa', '?hg::TextureUsage usage', '?bool mipmapped'], ['proxy']),
		('bool', ['hg::Texture &texture', 'const hg::Picture &picture', '?hg::TextureUsage usage', '?bool mipmapped'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'FreeTexture', 'void', ['hg::Texture &texture'], ['proxy'])

	gen.bind_method(shared_renderer, 'LoadNativeTexture', 'bool', ['hg::Texture &texture', 'const std::string &path'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetNativeTextureExt', 'const char *', [], ['proxy'])

	gen.insert_binding_code('''\
static void RendererBlitTexture_wrapper(hg::Renderer *renderer, hg::Texture &texture, const hg::Picture &picture) { renderer->BlitTexture(texture, picture.GetData(), picture.GetDataSize(), picture.GetWidth(), picture.GetHeight()); }
\n''')

	gen.bind_method_overloads(shared_renderer, 'BlitTexture', [
		('void', ['hg::Texture &texture', 'const hg::Picture &picture'], {'proxy': None, 'route': lambda args: 'RendererBlitTexture_wrapper(%s);' % ', '.join(args)}),
		#('void', ['hg::Texture &texture', 'const void *data', 'size_t data_size', 'uint32_t width', 'uint32_t height'], ['proxy']),
		#('void', ['hg::Texture &texture', 'const void *data', 'size_t data_size', 'uint32_t width', 'uint32_t height', 'uint32_t x', 'uint32_t y'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'ResizeTexture', 'void', ['hg::Texture &texture', 'uint32_t width', 'uint32_t height'], ['proxy'])

	gen.bind_method(shared_renderer, 'CaptureTexture', 'bool', ['const hg::Texture &texture', 'hg::Picture &picture'], ['proxy'])

	gen.bind_method(shared_renderer, 'GenerateTextureMipmap', 'void', ['hg::Texture &texture'], ['proxy'])

	gen.bind_method(shared_renderer, 'HasTexture', 'bool', ['const std::string &path'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetTexture', 'std::shared_ptr<hg::Texture>', ['const std::string &path'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Texture not found')})
	gen.bind_method(shared_renderer, 'LoadTexture', 'std::shared_ptr<hg::Texture>', ['const std::string &path', '?bool use_cache'], ['proxy'])

	#
	gen.bind_method(shared_renderer, 'NewShader', 'std::shared_ptr<hg::GpuShader>', ['?const std::string &name'], ['proxy'])

	gen.bind_method(shared_renderer, 'HasShader', 'bool', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetShader', 'std::shared_ptr<hg::GpuShader>', ['?const std::string &name'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Shader not found')})
	gen.bind_method_overloads(shared_renderer, 'LoadShader', [
		('std::shared_ptr<hg::GpuShader>', ['const std::string &name', '?bool use_cache'], ['proxy']),
		('std::shared_ptr<hg::GpuShader>', ['const std::string &name', 'const std::string &source', '?bool use_cache'], ['proxy'])
	])

	gen.bind_method(shared_renderer, 'CreateShader', 'void', ['const std::shared_ptr<hg::GpuShader> &shader', 'const std::shared_ptr<hg::Shader> &core_shader'], ['proxy'])
	gen.bind_method(shared_renderer, 'FreeShader', 'void', ['hg::GpuShader &shader'], ['proxy'])

	gen.bind_method(shared_renderer, 'GetShaderVariable', 'hg::GpuShaderVariable', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetShaderBuiltin', 'hg::GpuShaderVariable', ['hg::ShaderVariable::Semantic semantic'], ['proxy'])

	def bind_set_shader_var(alias, type, count):
			method_name = "SetShader%s%s" % (alias, str(count) if count>1 else "")
			data = list(map(lambda x: "v%d"%x, range(count)))
			method_args = list(map(lambda x: "%s %s"%(type,x), data))
			args = (method_name, ', '.join(method_args), type, ','.join(data), method_name)
			gen.insert_binding_code('''
	static void _renderer_%s(hg::Renderer *renderer, const hg::GpuShaderVariable &var, %s) {
		%s v[] = {%s};
		renderer->%s(var, v); 
	}''' % tuple(args))
			gen.insert_binding_code('''
	static void _renderer_%s_name(hg::Renderer *renderer, const std::string &name, %s) {
		%s v[] = {%s};
		renderer->%s(renderer->GetShaderVariable(name), v); 
	}
	''' % tuple(args))
			args = (method_name, type, method_name, count)
			gen.insert_binding_code('''
	static void _renderer_%s_vector(hg::Renderer *renderer, const hg::GpuShaderVariable &var, const std::vector<%s> &v) {
		renderer->%s(var, v.data(), v.size()/%d); 
	}
	static void _renderer_%s_vector(hg::Renderer *renderer, const std::string &name, const std::vector<%s> &v) {
		renderer->%s(renderer->GetShaderVariable(name), v.data(), v.size()/%d); 
	}
	''' % tuple(args+args))
			gen.bind_method_overloads(shared_renderer, method_name, expand_std_vector_proto(gen, [
		('void', ['const hg::GpuShaderVariable &var'] + method_args, {'proxy': None, 'route': route_lambda('_renderer_%s' % method_name)}),
		('void', ['const std::string &name'] + method_args, {'proxy': None, 'route': route_lambda('_renderer_%s_name' % method_name)}),
		('void', ['const hg::GpuShaderVariable &var', 'const std::vector<%s>& v' % type], {'proxy': None, 'route': route_lambda('_renderer_%s_vector' % method_name)}),
		('void', ['const std::string &name', 'const std::vector<%s>& v' % type], {'proxy': None, 'route': route_lambda('_renderer_%s_vector' % method_name)})
	]))

	for n in range(1,5) : bind_set_shader_var('Int', 'int', n) 
	for n in range(1,5) : bind_set_shader_var('Unsigned', 'uint32_t', n) 
	for n in range(1,5) : bind_set_shader_var('Float', 'float', n) 

	gen.insert_binding_code('''\
static void _renderer_SetShaderMatrix3(hg::Renderer *renderer, const hg::GpuShaderVariable &var, const hg::Matrix3 &m) { renderer->SetShaderMatrix3(var, &m); }
static void _renderer_SetShaderMatrix4(hg::Renderer *renderer, const hg::GpuShaderVariable &var, const hg::Matrix4 &m) { renderer->SetShaderMatrix4(var, &m); }
static void _renderer_SetShaderMatrix44(hg::Renderer *renderer, const hg::GpuShaderVariable &var, const hg::Matrix44 &m) { renderer->SetShaderMatrix44(var, &m); }

static void _renderer_SetShaderTexture(hg::Renderer *renderer, const hg::GpuShaderVariable &var, const hg::Texture &t) { renderer->SetShaderTexture(var, t); }

static void _renderer_SetShaderMatrix3_name(hg::Renderer *renderer, const std::string &name, const hg::Matrix3 &m) { renderer->SetShaderMatrix3(renderer->GetShaderVariable(name), &m); }
static void _renderer_SetShaderMatrix4_name(hg::Renderer *renderer, const std::string &name, const hg::Matrix4 &m) { renderer->SetShaderMatrix4(renderer->GetShaderVariable(name), &m); }
static void _renderer_SetShaderMatrix44_name(hg::Renderer *renderer, const std::string &name, const hg::Matrix44 &m) { renderer->SetShaderMatrix44(renderer->GetShaderVariable(name), &m); }

static void _renderer_SetShaderTexture_name(hg::Renderer *renderer, const std::string &name, const hg::Texture &t) { renderer->SetShaderTexture(renderer->GetShaderVariable(name), t); }
''')

	gen.bind_method_overloads(shared_renderer, 'SetShaderMatrix3', [
		('void', ['const hg::GpuShaderVariable &var', 'const hg::Matrix3 &m'], {'proxy': None, 'route': route_lambda('_renderer_SetShaderMatrix3')}),
		('void', ['const std::string &name', 'const hg::Matrix3 &m'], {'proxy': None, 'route': route_lambda('_renderer_SetShaderMatrix3_name')})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderMatrix4', [
		('void', ['const hg::GpuShaderVariable &var', 'const hg::Matrix4 &m'], {'proxy': None, 'route': route_lambda('_renderer_SetShaderMatrix4')}),
		('void', ['const std::string &name', 'const hg::Matrix4 &m'], {'proxy': None, 'route': route_lambda('_renderer_SetShaderMatrix4_name')})
	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderMatrix44', [
		('void', ['const hg::GpuShaderVariable &var', 'const hg::Matrix44 &m'], {'proxy': None, 'route': route_lambda('_renderer_SetShaderMatrix44')}),
		('void', ['const std::string &name', 'const hg::Matrix44 &m'], {'proxy': None, 'route': route_lambda('_renderer_SetShaderMatrix44_name')})

	])
	gen.bind_method_overloads(shared_renderer, 'SetShaderTexture', [
		('void', ['const hg::GpuShaderVariable &var', 'const hg::Texture &texture'], {'proxy': None, 'route': route_lambda('_renderer_SetShaderTexture')}),
		('void', ['const std::string &name', 'const hg::Texture &texture'], {'proxy': None, 'route': route_lambda('_renderer_SetShaderTexture_name')})
	])

	"""
	gen.bind_method(shared_renderer, 'SetShaderSystemBuiltins', 'void', ['float clock', 'const hg::tVector2<int> &internal_resolution', 'uint32_t fx_scale', 'const hg::Color &ambient_color', 'bool is_forward', 'bool fog_enabled', 'const hg::Color &fog_color', 'float fog_near', 'float fog_far', 'hg::Texture &depth_map'])
	gen.bind_method(shared_renderer, 'SetShaderCameraBuiltins', 'void', ['const hg::Matrix4 &view_world', 'float z_near', 'float z_far', 'float zoom_factor', 'float eye'])
	gen.bind_method(shared_renderer, 'SetShaderTransformationBuiltins', 'void', ['const hg::Matrix44 &view_pm', 'const hg::Matrix4 &view_m', 'const hg::Matrix4 &view_im', 'const hg::Matrix4 *node_m', 'const hg::Matrix4 *node_im', 'const hg::Matrix44 &prv_view_pm', 'const hg::Matrix4 &prv_view_im', 'const hg::Matrix4 *i_m', 'uint32_t count'])
	gen.bind_method(shared_renderer, 'SetShaderLightBuiltins', 'void', ['const hg::Matrix4 &light_world', 'const hg::Color &light_diffuse', 'const hg::Color &light_specular', 'float range', 'float clip_dist', 'float cone_angle', 'float edge_angle', 'hg::Texture *projection_map', 'const hg::Matrix4 &view_world', 'hg::Texture *shadow_map', 'float shadow_bias', 'float inv_shadow_map_size', 'const hg::Color &shadow_color', 'uint32_t shadow_data_count', 'const hg::Matrix4 *shadow_data_inv_world', 'const hg::Matrix44 *shadow_data_projection_to_map', 'const float *shadow_data_slice_distance'])
	gen.bind_method(shared_renderer, 'SetShaderSkeletonValues', 'void', ['uint32_t skin_bone_count', 'const hg::Matrix4 *skin_bone_matrices', 'const hg::Matrix4 *skin_bone_previous_matrices', 'const uint16_t *skin_bone_idx'])
	gen.bind_method(shared_renderer, 'SetShaderPickingBuiltins', 'void', ['uint32_t uid'])
	gen.bind_method(shared_renderer, 'SetShaderValues', 'void', ['const ShaderValues &shader_values', '?const ShaderValues *material_values'])
	"""

	#
	gen.bind_method(shared_renderer, 'SetFillMode', 'void', ['hg::Renderer::FillMode mode'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetCullFunc', 'void', ['hg::Renderer::CullFunc func'], ['proxy'])
	gen.bind_method(shared_renderer, 'EnableCulling', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetDepthFunc', 'void', ['hg::Renderer::DepthFunc func'], ['proxy'])
	gen.bind_method(shared_renderer, 'EnableDepthTest', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_renderer, 'EnableDepthWrite', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetBlendFunc', 'void', ['hg::Renderer::BlendFunc src', 'hg::Renderer::BlendFunc dst'], ['proxy'])
	gen.bind_method(shared_renderer, 'EnableBlending', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer, 'EnableAlphaToCoverage', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetColorMask', 'void', ['bool red', 'bool green', 'bool blue', 'bool alpha'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetDefaultStates', 'void', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'SetIndexSource', [
		('void', [], ['proxy']),
		('void', ['hg::GpuBuffer &buffer'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'SetVertexSource', 'void', ['hg::GpuBuffer &buffer', 'const hg::VertexLayout &layout'], ['proxy'])

	#gen.bind_method(shared_renderer, 'GetShader', 'const std::shared_ptr<hg::GpuShader> &', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetShader', 'bool', ['const std::shared_ptr<hg::GpuShader> &shader'], ['proxy'])

	gen.bind_method(shared_renderer, 'SetPolygonDepthOffset', 'void', ['float slope_scale', 'float bias'], ['proxy'])

	gen.bind_method(shared_renderer, 'NewOutputSurface', 'hg::Surface', ['const hg::Window &window'], ['proxy'])
	gen.bind_method(shared_renderer, 'SetOutputSurface', 'void', ['const hg::Surface &surface'], ['proxy'])
	gen.bind_method(shared_renderer, 'DestroyOutputSurface', 'void', ['const hg::Surface &surface'], ['proxy'])
	gen.bind_method(shared_renderer, 'NewOffscreenOutputSurface', 'hg::Surface', ['int width', 'int height'], ['proxy'])

	gen.bind_method(shared_renderer, 'GetOutputSurface', 'const hg::Surface &', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetOutputSurfaceSize', 'hg::tVector2<int>', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'Open', [
		('bool', [], ['proxy']),
		('bool', ['bool debug'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'Close', 'void', [], ['proxy'])

	gen.bind_method(shared_renderer, 'IsOpen', 'bool', [], ['proxy'])

	gen.bind_method(shared_renderer, 'GetInverseViewMatrix', 'hg::Matrix4', [], ['proxy'])
	gen.bind_method(shared_renderer, 'GetInverseWorldMatrix', 'hg::Matrix4', [], ['proxy'])

	gen.bind_method(shared_renderer, 'SetViewMatrix', 'void', ['const hg::Matrix4 &view_matrix'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetViewMatrix', 'hg::Matrix4', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetProjectionMatrix', 'void', ['const hg::Matrix44 &projection_matrix'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetProjectionMatrix', 'hg::Matrix44', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetWorldMatrix', 'void', ['const hg::Matrix4 &world_matrix'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetWorldMatrix', 'hg::Matrix4', [], ['proxy'])

	gen.bind_method(shared_renderer, 'SetIdentityMatrices', 'void', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'Set2DMatrices', [
		('void', [], ['proxy']),
		('void', ['const hg::tVector2<float> &resolution'], ['proxy']),
		('void', ['const hg::tVector2<float> &resolution', 'bool y_origin_bottom'], ['proxy']),
		('void', ['bool y_origin_bottom'], ['proxy'])
	])

	gen.bind_method(shared_renderer, 'ScreenVertex', 'hg::Vector3', ['int x', 'int y'], ['proxy'])

	gen.bind_method(shared_renderer, 'EnableClippingPlane', 'void', ['int idx'], ['proxy'])
	gen.bind_method(shared_renderer, 'DisableClippingPlane', 'void', ['int idx'], ['proxy'])
	gen.bind_method(shared_renderer, 'SetClippingPlane', 'void', ['int idx', 'float a', 'float b', 'float c', 'float d'], ['proxy'])

	gen.bind_method(shared_renderer, 'ClearClippingRect', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer, 'SetClippingRect', 'void', ['const hg::Rect<float> &rect'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetClippingRect', 'hg::Rect<float>', [], ['proxy'])

	gen.bind_method(shared_renderer, 'SetViewport', 'void', ['const hg::Rect<float> &rect'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetViewport', 'hg::Rect<float>', [], ['proxy'])

	gen.bind_method(shared_renderer, 'GetAspectRatio', 'hg::tVector2<float>', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'Clear', [
		('void', ['hg::Color color'], ['proxy']),
		('void', ['hg::Color color', 'float z', 'hg::Renderer::ClearFunction flags'], ['proxy'])
	])

	#virtual void DrawElements(PrimitiveType prim_type, int idx_count, IndexType idx_type = IndexUShort, uint32_t idx_offset = 0) = 0;
	#virtual void DrawElementsInstanced(uint32_t instance_count, Buffer &instance_data, PrimitiveType prim_type, int idx_count, IndexType idx_type = IndexUShort) = 0;

	gen.bind_method(shared_renderer, 'DrawFrame', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer, 'ShowFrame', 'void', [], ['proxy'])

	gen.bind_method(shared_renderer, 'SetVSync', 'void', ['bool enabled'], ['proxy'])

	gen.bind_method(shared_renderer, 'CaptureFramebuffer', 'bool', ['hg::Picture &out'], ['proxy'])
	gen.bind_method(shared_renderer, 'InvalidateStateCache', 'void', [], ['proxy'])

	gen.bind_method(shared_renderer, 'GetFrameShownCount', 'size_t', [], ['proxy'])

	gen.end_class(shared_renderer)

	#
	gen.insert_binding_code('''static std::shared_ptr<hg::Renderer> CreateRenderer(const std::string &name) { return hg::g_renderer_factory.get().Instantiate(name); }
static std::shared_ptr<hg::Renderer> CreateRenderer() { return hg::g_renderer_factory.get().Instantiate(); }
	''', 'Renderer custom API')

	gen.bind_function('CreateRenderer', 'std::shared_ptr<hg::Renderer>', ['?const std::string &name'], {'check_rval': check_bool_rval_lambda(gen, 'CreateRenderer failed, was LoadPlugins called succesfully?')})

	# hg::RendererAsync
	gen.add_include('engine/renderer_async.h')

	renderer_async = gen.begin_class('hg::RendererAsync', bound_name='RendererAsync_nobind', noncopyable=True, nobind=True)
	gen.end_class(renderer_async)

	shared_renderer_async = gen.begin_class('std::shared_ptr<hg::RendererAsync>', bound_name='RendererAsync', features={'proxy': lib.stl.SharedPtrProxyFeature(renderer_async)})

	gen.bind_constructor(shared_renderer_async, ['std::shared_ptr<hg::Renderer> renderer'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetRenderer', 'const std::shared_ptr<hg::Renderer> &', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'PurgeCache', 'std::future<size_t>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'RefreshCacheEntry', 'void', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'NewRenderTarget', 'std::shared_ptr<hg::RenderTarget>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetRenderTargetColorTexture', 'void', ['const std::shared_ptr<hg::RenderTarget> &render_target', 'const std::shared_ptr<hg::Texture> &texture'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetRenderTargetDepthTexture', 'void', ['const std::shared_ptr<hg::RenderTarget> &render_target', 'const std::shared_ptr<hg::Texture> &texture'], ['proxy'])
	gen.bind_method_overloads(shared_renderer_async, 'BlitRenderTarget', [
		('void', ['const std::shared_ptr<hg::RenderTarget> &src_render_target', 'const std::shared_ptr<hg::RenderTarget> &dst_render_target', 'const hg::Rect<int> &src_rect', 'const hg::Rect<int> &dst_rect'], ['proxy']),
		('void', ['const std::shared_ptr<hg::RenderTarget> &src_render_target', 'const std::shared_ptr<hg::RenderTarget> &dst_render_target', 'const hg::Rect<int> &src_rect', 'const hg::Rect<int> &dst_rect', 'bool blit_color', 'bool blit_depth'], ['proxy'])
	])
	gen.bind_method(shared_renderer_async, 'ReadRenderTargetColorPixels', 'void', ['const std::shared_ptr<hg::RenderTarget> &src_render_target', 'const std::shared_ptr<hg::Picture> &out', 'const hg::Rect<int> &rect'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'ClearRenderTarget', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetRenderTarget', 'void', ['std::shared_ptr<hg::RenderTarget> &render_target'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'CheckRenderTarget', 'std::future<bool>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'CreateRenderTarget', 'std::future<bool>', ['std::shared_ptr<hg::RenderTarget> &render_target'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'FreeRenderTarget', 'void', ['const std::shared_ptr<hg::RenderTarget> &render_target'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'NewBuffer', 'std::shared_ptr<hg::GpuBuffer>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetBufferSize', 'std::future<size_t>', ['std::shared_ptr<hg::GpuBuffer> buffer'], ['proxy'])
	#std::future<void *> MapBuffer(sBuffer buf) {
	#void UnmapBuffer(sBuffer buf) { run_call<void>(std::bind(&Renderer::UnmapBuffer, shared_ref(renderer), shared_ref(buf)), RA_task_affinity); }
	#std::future<bool> UpdateBuffer(sBuffer buf, const void *p, size_t start = 0, size_t size = 0) {
	#std::future<bool> CreateBuffer(sBuffer buf, const void *data, size_t size, Buffer::Type type, Buffer::Usage usage = Buffer::Static) {
	#std::future<bool> CreateBuffer(sBuffer buf, const BinaryData &data, Buffer::Type type, Buffer::Usage usage = Buffer::Static) {
	gen.bind_method(shared_renderer_async, 'FreeBuffer', 'void', ['std::shared_ptr<hg::GpuBuffer> buffer'], ['proxy'])

	gen.bind_method_overloads(shared_renderer_async, 'NewTexture', [
		('std::shared_ptr<hg::Texture>', [], ['proxy']),
		('std::shared_ptr<hg::Texture>', ['const std::string &name'], ['proxy'])
	])
	gen.bind_method_overloads(shared_renderer_async, 'NewShadowMap', [
		('std::shared_ptr<hg::Texture>', ['int width', 'int height'], ['proxy']),
		('std::shared_ptr<hg::Texture>', ['int width', 'int height', 'const std::string &name'], ['proxy'])
	])
	gen.bind_method_overloads(shared_renderer_async, 'CreateTexture', [
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'int width', 'int height'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'int width', 'int height', 'hg::TextureFormat format', 'hg::TextureAA aa'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'int width', 'int height', 'hg::TextureFormat format', 'hg::TextureAA aa', 'hg::TextureUsage usage'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'int width', 'int height', 'hg::TextureFormat format', 'hg::TextureAA aa', 'hg::TextureUsage usage', 'bool mipmapped'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'hg::BinaryData &data', 'int width', 'int height'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'hg::BinaryData &data', 'int width', 'int height', 'hg::TextureFormat format', 'hg::TextureAA aa'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'hg::BinaryData &data', 'int width', 'int height', 'hg::TextureFormat format', 'hg::TextureAA aa', 'hg::TextureUsage usage'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'hg::BinaryData &data', 'int width', 'int height', 'hg::TextureFormat format', 'hg::TextureAA aa', 'hg::TextureUsage usage', 'bool mipmapped'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'std::shared_ptr<hg::Picture> picture'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'std::shared_ptr<hg::Picture> picture', 'hg::TextureUsage usage'], ['proxy']),
		('std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'std::shared_ptr<hg::Picture> picture', 'hg::TextureUsage usage', 'bool mipmapped'], ['proxy'])

	])
	gen.bind_method(shared_renderer_async, 'FreeTexture', 'void', ['std::shared_ptr<hg::Texture> texture'], ['proxy'])
	gen.bind_method_overloads(shared_renderer_async, 'BlitTexture', [
		('void', ['std::shared_ptr<hg::Texture> texture', 'const hg::BinaryData &data', 'uint32_t width', 'uint32_t height'], ['proxy']),
		('void', ['std::shared_ptr<hg::Texture> texture', 'const hg::BinaryData &data', 'uint32_t width', 'uint32_t height', 'uint32_t x', 'uint32_t y'], ['proxy'])
	])
	gen.bind_method(shared_renderer_async, 'ResizeTexture', 'void', ['std::shared_ptr<hg::Texture> texture', 'uint32_t width', 'uint32_t height'], ['proxy'])
	gen.bind_method_overloads(shared_renderer_async, 'BlitTextureBackground', [
		('void', ['std::shared_ptr<hg::Texture> texture', 'const hg::BinaryData &data', 'uint32_t width', 'uint32_t height'], ['proxy']),
		('void', ['std::shared_ptr<hg::Texture> texture', 'const hg::BinaryData &data', 'uint32_t width', 'uint32_t height', 'uint32_t x', 'uint32_t y'], ['proxy'])
	])
	gen.bind_method(shared_renderer_async, 'CaptureTexture', 'std::future<bool>', ['std::shared_ptr<hg::Texture> texture', 'std::shared_ptr<hg::Picture> out'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GenerateTextureMipmap', 'void', ['std::shared_ptr<hg::Texture> texture'], ['proxy'])
	gen.bind_method_overloads(shared_renderer_async, 'LoadTexture', [
		('std::shared_ptr<hg::Texture>', ['const std::string &path'], ['proxy']),
		('std::shared_ptr<hg::Texture>', ['const std::string &path', 'bool use_cache'], ['proxy'])
	])
	gen.bind_method(shared_renderer_async, 'GetNativeTextureExt', 'const char *', [], ['proxy'])

	#
	gen.bind_method(shared_renderer_async, 'SetFillMode', 'void', ['hg::Renderer::FillMode fill_mode'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetCullFunc', 'void', ['hg::Renderer::CullFunc cull_mode'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'EnableCulling', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetDepthFunc', 'void', ['hg::Renderer::DepthFunc depth_func'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'EnableDepthTest', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'EnableDepthWrite', 'void', ['bool enable'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetBlendFunc', 'void', ['hg::Renderer::BlendFunc src_blend', 'hg::Renderer::BlendFunc dst_blend'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'EnableBlending', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'EnableAlphaToCoverage', 'void', ['bool enable'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetDefaultStates', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetIndexSource', 'void', ['?std::shared_ptr<hg::GpuBuffer> &buffer'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetVertexSource', 'void', ['std::shared_ptr<hg::GpuBuffer> &buffer', 'const hg::VertexLayout &layout'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'GetShader', 'std::future<std::shared_ptr<hg::GpuShader>>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetShader', 'std::future<bool>', ['std::shared_ptr<hg::GpuShader> &shader'], ['proxy'])

	#
	gen.bind_method(shared_renderer_async, 'NewWindow', 'std::future<hg::Window>', ['int w', 'int h', 'int bpp', 'hg::Window::Visibility visibility'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'NewOutputSurface', 'std::future<hg::Surface>', ['const hg::Window &window'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'NewOffscreenOutputSurface', 'std::future<hg::Surface>', ['int width', 'int height'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetOutputSurface', 'void', ['const hg::Surface &surface'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'DestroyOutputSurface', 'void', ['hg::Surface &surface'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'GetOutputSurface', 'std::future<hg::Surface>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetOutputSurfaceSize', 'std::future<hg::tVector2<int>>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'FitViewportToOutputSurface', 'void', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'UpdateWindow', 'void', ['const hg::Window &window'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'Open', 'std::future<bool>', ['?bool debug'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'Close', 'std::future<void>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'GetInverseViewMatrix', 'std::future<hg::Matrix4>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetInverseWorldMatrix', 'std::future<hg::Matrix4>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetViewMatrix', 'void', ['const hg::Matrix4 &view'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetViewMatrix', 'std::future<hg::Matrix4>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetProjectionMatrix', 'void', ['const hg::Matrix44 &projection'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetProjectionMatrix', 'std::future<hg::Matrix44>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetWorldMatrix', 'void', ['const hg::Matrix4 &world'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetWorldMatrix', 'std::future<hg::Matrix4>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetIdentityMatrices', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'Set2DMatrices', 'void', ['?bool reverse_y'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'EnableClippingPlane', 'void', ['int idx'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'DisableClippingPlane', 'void', ['int idx'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetClippingPlane', 'void', ['int idx', 'float a', 'float b', 'float c', 'float d'], ['proxy'])

	#
	gen.bind_method(shared_renderer_async, 'ClearClippingRect', 'void', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'SetClippingRect', 'void', ['const hg::Rect<float> &clip_rect'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetClippingRect', 'std::future<hg::Rect<float>>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetViewport', 'void', ['const hg::Rect<float> &rect'], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetViewport', 'std::future<hg::Rect<float>>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'GetAspectRatio', 'std::future<hg::tVector2<float>>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'Clear', 'void', ['hg::Color color', '?float z', '?hg::Renderer::ClearFunction clear_mask'], ['proxy'])

	gen.bind_method(shared_renderer_async, 'DrawFrame', 'std::future<void>', [], ['proxy'])
	gen.bind_method(shared_renderer_async, 'ShowFrame', 'std::future<void>', [], ['proxy'])

	gen.bind_method(shared_renderer_async, 'SetVSync', 'void', ['bool enabled'], ['proxy'])
	
	gen.bind_method(shared_renderer_async, 'CaptureFramebuffer', 'std::future<bool>', ['const std::shared_ptr<hg::Picture> &out'], ['proxy'])

	gen.end_class(shared_renderer_async)

	# global rendering functions
	gen.bind_function('DrawBuffers', 'void', ['hg::Renderer &renderer', 'uint32_t index_count', 'hg::GpuBuffer &idx', 'hg::GpuBuffer &vtx', 'hg::VertexLayout &layout', '?hg::IndexType idx_type', '?hg::GpuPrimitiveType primitive_type'])


def bind_render(gen):
	gen.add_include('engine/render_system.h')

	gen.bind_named_enum('hg::Eye', ['EyeMono', 'EyeStereoLeft', 'EyeStereoRight'])
	gen.bind_named_enum('hg::CullMode', ['CullBack', 'CullFront', 'CullNever'])
	gen.bind_named_enum('hg::BlendMode', ['BlendOpaque', 'BlendAlpha', 'BlendAdditive'])

	render_system = gen.begin_class('hg::RenderSystem', bound_name='RenderSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(render_system)
	shared_render_system = gen.begin_class('std::shared_ptr<hg::RenderSystem>', bound_name='RenderSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(render_system)})

	# hg::SurfaceShader
	gen.add_include('engine/surface_shader.h')

	surface_shader = gen.begin_class('hg::SurfaceShader', bound_name='SurfaceShader_nobind', noncopyable=True, nobind=True)
	gen.end_class(surface_shader)

	shared_surface_shader = gen.begin_class('std::shared_ptr<hg::SurfaceShader>', bound_name='SurfaceShader', features={'proxy': lib.stl.SharedPtrProxyFeature(surface_shader)})
	gen.bind_method_overloads(shared_surface_shader, 'SetUserUniformValue', [
		('bool', ['const std::string &name', 'hg::Vector4 value'], ['proxy']),
		('bool', ['const std::string &name', 'std::shared_ptr<hg::Texture> texture'], ['proxy'])
	])
	gen.end_class(shared_surface_shader)

	# hg::RenderMaterial
	gen.add_include('engine/render_material.h')

	material = gen.begin_class('hg::RenderMaterial', bound_name='RenderMaterial_nobind', noncopyable=True, nobind=True)
	gen.end_class(material)

	shared_material = gen.begin_class('std::shared_ptr<hg::RenderMaterial>', bound_name='RenderMaterial', features={'proxy': lib.stl.SharedPtrProxyFeature(material)})
	gen.add_base(shared_material, gen.get_conv('std::shared_ptr<hg::GpuResource>'))

	gen.bind_method(shared_material, 'Create', 'void', ['hg::RenderSystem &render_system', 'std::shared_ptr<hg::Material> material'], ['proxy'])
	gen.bind_method(shared_material, 'Free', 'void', [], ['proxy'])

	gen.bind_method(shared_material, 'Clone', 'std::shared_ptr<hg::RenderMaterial>', [], ['proxy'])
	gen.bind_method(shared_material, 'IsReadyOrFailed', 'bool', [], ['proxy'])

	gen.bind_method(shared_material, 'GetSurfaceShader', 'const std::shared_ptr<hg::SurfaceShader> &', [], ['proxy'])
	gen.bind_method(shared_material, 'SetSurfaceShader', 'void', ['std::shared_ptr<hg::SurfaceShader> surface_shader'], ['proxy'])

	gen.insert_binding_code('''
static bool _RenderMaterial_GetFloat(hg::RenderMaterial *m, const std::string &name, float &o0) { if (auto v = m->GetValue(name)) { o0 = v->fv[0]; return true; } return false; }
static bool _RenderMaterial_GetFloat2(hg::RenderMaterial *m, const std::string &name, float &o0, float &o1) { if (auto v = m->GetValue(name)) { o0 = v->fv[0]; o1 = v->fv[1]; return true; } return false; }
static bool _RenderMaterial_GetFloat3(hg::RenderMaterial *m, const std::string &name, float &o0, float &o1, float &o2) { if (auto v = m->GetValue(name)) { o0 = v->fv[0]; o1 = v->fv[1]; o2 = v->fv[2]; return true; } return false; }
static bool _RenderMaterial_GetFloat4(hg::RenderMaterial *m, const std::string &name, float &o0, float &o1, float &o2, float &o3) { if (auto v = m->GetValue(name)) { o0 = v->fv[0]; o1 = v->fv[1]; o2 = v->fv[2]; o3 = v->fv[3]; return true; } return false; }

static bool _RenderMaterial_GetInt(hg::RenderMaterial *m, const std::string &name, int &o0) { if (auto v = m->GetValue(name)) { o0 = v->iv[0]; return true; } return false; }
static bool _RenderMaterial_GetInt2(hg::RenderMaterial *m, const std::string &name, int &o0, int &o1) { if (auto v = m->GetValue(name)) { o0 = v->iv[0]; o1 = v->iv[1]; return true; } return false; }
static bool _RenderMaterial_GetInt3(hg::RenderMaterial *m, const std::string &name, int &o0, int &o1, int &o2) { if (auto v = m->GetValue(name)) { o0 = v->iv[0]; o1 = v->iv[1]; o2 = v->iv[2]; return true; } return false; }
static bool _RenderMaterial_GetInt4(hg::RenderMaterial *m, const std::string &name, int &o0, int &o1, int &o2, int &o3) { if (auto v = m->GetValue(name)) { o0 = v->iv[0]; o1 = v->iv[1]; o2 = v->iv[2]; o3 = v->iv[3]; return true; } return false; }

static bool _RenderMaterial_GetUnsigned(hg::RenderMaterial *m, const std::string &name, unsigned int &o0) { if (auto v = m->GetValue(name)) { o0 = v->uv[0]; return true; } return false; }
static bool _RenderMaterial_GetUnsigned2(hg::RenderMaterial *m, const std::string &name, unsigned int &o0, unsigned int &o1) { if (auto v = m->GetValue(name)) { o0 = v->uv[0]; o1 = v->uv[1]; return true; } return false; }
static bool _RenderMaterial_GetUnsigned3(hg::RenderMaterial *m, const std::string &name, unsigned int &o0, unsigned int &o1, unsigned int &o2) { if (auto v = m->GetValue(name)) { o0 = v->uv[0]; o1 = v->uv[1]; o2 = v->uv[2]; return true; } return false; }
static bool _RenderMaterial_GetUnsigned4(hg::RenderMaterial *m, const std::string &name, unsigned int &o0, unsigned int &o1, unsigned int &o2, unsigned int &o3) { if (auto v = m->GetValue(name)) { o0 = v->uv[0]; o1 = v->uv[1]; o2 = v->uv[2]; o3 = v->uv[3]; return true; } return false; }

static bool _RenderMaterial_GetTexture(hg::RenderMaterial *m, const std::string &name, std::shared_ptr<hg::Texture> &o) { if (auto v = m->GetValue(name)) { o = v->texture; return true; } return false; }

static bool _RenderMaterial_SetFloat(hg::RenderMaterial *m, const std::string &name, float o0) { if (auto v = m->GetValue(name)) { v->fv[0] = o0; return true; } return false; }
static bool _RenderMaterial_SetFloat2(hg::RenderMaterial *m, const std::string &name, float o0, float o1) { if (auto v = m->GetValue(name)) { v->fv[0] = o0; v->fv[1] = o1; return true; } return false; }
static bool _RenderMaterial_SetFloat3(hg::RenderMaterial *m, const std::string &name, float o0, float o1, float o2) { if (auto v = m->GetValue(name)) { v->fv[0] = o0; v->fv[1] = o1; v->fv[2] = o2; return true; } return false; }
static bool _RenderMaterial_SetFloat4(hg::RenderMaterial *m, const std::string &name, float o0, float o1, float o2, float o3) { if (auto v = m->GetValue(name)) { v->fv[0] = o0; v->fv[1] = o1; v->fv[2] = o2; v->fv[3] = o3; return true; } return false; }

static bool _RenderMaterial_SetInt(hg::RenderMaterial *m, const std::string &name, int o0) { if (auto v = m->GetValue(name)) { v->iv[0] = o0; return true; } return false; }
static bool _RenderMaterial_SetInt2(hg::RenderMaterial *m, const std::string &name, int o0, int o1) { if (auto v = m->GetValue(name)) { v->iv[0] = o0; v->iv[1] = o1; return true; } return false; }
static bool _RenderMaterial_SetInt3(hg::RenderMaterial *m, const std::string &name, int o0, int o1, int o2) { if (auto v = m->GetValue(name)) { v->iv[0] = o0; v->iv[1] = o1; v->iv[2] = o2; return true; } return false; }
static bool _RenderMaterial_SetInt4(hg::RenderMaterial *m, const std::string &name, int o0, int o1, int o2, int o3) { if (auto v = m->GetValue(name)) { v->iv[0] = o0; v->iv[1] = o1; v->iv[2] = o2; v->iv[3] = o3; return true; } return false; }

static bool _RenderMaterial_SetUnsigned(hg::RenderMaterial *m, const std::string &name, unsigned int o0) { if (auto v = m->GetValue(name)) { v->uv[0] = o0; return true; } return false; }
static bool _RenderMaterial_SetUnsigned2(hg::RenderMaterial *m, const std::string &name, unsigned int o0, unsigned int o1) { if (auto v = m->GetValue(name)) { v->uv[0] = o0; v->uv[1] = o1; return true; } return false; }
static bool _RenderMaterial_SetUnsigned3(hg::RenderMaterial *m, const std::string &name, unsigned int o0, unsigned int o1, unsigned int o2) { if (auto v = m->GetValue(name)) { v->uv[0] = o0; v->uv[1] = o1; v->uv[2] = o2; return true; } return false; }
static bool _RenderMaterial_SetUnsigned4(hg::RenderMaterial *m, const std::string &name, int o0, unsigned int o1, unsigned int o2, unsigned int o3) { if (auto v = m->GetValue(name)) { v->uv[0] = o0; v->uv[1] = o1; v->uv[2] = o2; v->uv[3] = o3; return true; } return false; }

static bool _RenderMaterial_SetTexture(hg::RenderMaterial *m, const std::string &name, std::shared_ptr<hg::Texture> &o) { if (auto v = m->GetValue(name)) { v->texture = o; return true; } return false; }
''')

	# 
	gen.bind_method(shared_material, 'GetFloat', 'bool', ['const std::string &name', 'float &o0'], {'proxy': None, 'arg_out': ['o0'], 'route': lambda args: '_RenderMaterial_GetFloat(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetFloat2', 'bool', ['const std::string &name', 'float &o0', 'float &o1'], {'proxy': None, 'arg_out': ['o0', 'o1'], 'route': lambda args: '_RenderMaterial_GetFloat2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetFloat3', 'bool', ['const std::string &name', 'float &o0', 'float &o1', 'float &o2'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2'], 'route': lambda args: '_RenderMaterial_GetFloat3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetFloat4', 'bool', ['const std::string &name', 'float &o0', 'float &o1', 'float &o2', 'float &o3'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2', 'o3'], 'route': lambda args: '_RenderMaterial_GetFloat4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'GetInt', 'bool', ['const std::string &name', 'int &o0'], {'proxy': None, 'arg_out': ['o0'], 'route': lambda args: '_RenderMaterial_GetInt(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetInt2', 'bool', ['const std::string &name', 'int &o0', 'int &o1'], {'proxy': None, 'arg_out': ['o0', 'o1'], 'route': lambda args: '_RenderMaterial_GetInt2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetInt3', 'bool', ['const std::string &name', 'int &o0', 'int &o1', 'int &o2'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2'], 'route': lambda args: '_RenderMaterial_GetInt3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetInt4', 'bool', ['const std::string &name', 'int &o0', 'int &o1', 'int &o2', 'int &o3'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2', 'o3'], 'route': lambda args: '_RenderMaterial_GetInt4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'GetUnsigned', 'bool', ['const std::string &name', 'unsigned int &o0'], {'proxy': None, 'arg_out': ['o0'], 'route': lambda args: '_RenderMaterial_GetUnsigned(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetUnsigned2', 'bool', ['const std::string &name', 'unsigned int &o0', 'unsigned int &o1'], {'proxy': None, 'arg_out': ['o0', 'o1'], 'route': lambda args: '_RenderMaterial_GetUnsigned2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetUnsigned3', 'bool', ['const std::string &name', 'unsigned int &o0', 'unsigned int &o1', 'unsigned int &o2'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2'], 'route': lambda args: '_RenderMaterial_GetUnsigned3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'GetUnsigned4', 'bool', ['const std::string &name', 'unsigned int &o0', 'unsigned int &o1', 'unsigned int &o2', 'unsigned int &o3'], {'proxy': None, 'arg_out': ['o0', 'o1', 'o2', 'o3'], 'route': lambda args: '_RenderMaterial_GetUnsigned4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'GetTexture', 'bool', ['const std::string &name', 'std::shared_ptr<hg::Texture> &o'], {'proxy': None, 'arg_out': ['o'], 'route': lambda args: '_RenderMaterial_GetTexture(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'SetFloat', 'bool', ['const std::string &name', 'float o0'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetFloat(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetFloat2', 'bool', ['const std::string &name', 'float o0', 'float o1'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetFloat2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetFloat3', 'bool', ['const std::string &name', 'float o0', 'float o1', 'float o2'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetFloat3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetFloat4', 'bool', ['const std::string &name', 'float o0', 'float o1', 'float o2', 'float o3'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetFloat4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'SetInt', 'bool', ['const std::string &name', 'int o0'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetInt(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetInt2', 'bool', ['const std::string &name', 'int o0', 'int o1'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetInt2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetInt3', 'bool', ['const std::string &name', 'int o0', 'int o1', 'int o2'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetInt3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetInt4', 'bool', ['const std::string &name', 'int o0', 'int o1', 'int o2', 'int o3'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetInt4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'SetUnsigned', 'bool', ['const std::string &name', 'unsigned int o0'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetUnsigned(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetUnsigned2', 'bool', ['const std::string &name', 'unsigned int o0', 'unsigned int o1'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetUnsigned2(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetUnsigned3', 'bool', ['const std::string &name', 'unsigned int o0', 'unsigned int o1', 'unsigned int o2'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetUnsigned3(%s);' % (', '.join(args))})
	gen.bind_method(shared_material, 'SetUnsigned4', 'bool', ['const std::string &name', 'unsigned int o0', 'unsigned int o1', 'unsigned int o2', 'unsigned int o3'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetUnsigned4(%s);' % (', '.join(args))})

	gen.bind_method(shared_material, 'SetTexture', 'bool', ['const std::string &name', 'std::shared_ptr<hg::Texture> &o'], {'proxy': None, 'route': lambda args: '_RenderMaterial_SetTexture(%s);' % (', '.join(args))})

	gen.end_class(shared_material)

	# hg::RenderGeometry
	gen.add_include('engine/render_geometry.h')

	geometry = gen.begin_class('hg::RenderGeometry', bound_name='RenderGeometry_nobind', noncopyable=True, nobind=True)
	gen.end_class(geometry)

	shared_geometry = gen.begin_class('std::shared_ptr<hg::RenderGeometry>', bound_name='RenderGeometry', features={'proxy': lib.stl.SharedPtrProxyFeature(geometry)})
	gen.add_base(shared_geometry, gen.get_conv('std::shared_ptr<hg::GpuResource>'))

	gen.bind_constructor_overloads(shared_geometry, [
		([], ['proxy']),
		(['const std::string &name'], ['proxy']),
	])
	gen.bind_method(shared_geometry, 'SetMaterial', 'bool', ['uint32_t index', 'std::shared_ptr<hg::RenderMaterial> material'], ['proxy'])

	gen.insert_binding_code('static hg::MinMax _render_Geometry_GetMinMax(hg::RenderGeometry *geo) { return geo->minmax; }')
	gen.bind_method(shared_geometry, 'GetMinMax', 'hg::MinMax', [], {'proxy': None, 'route': route_lambda('_render_Geometry_GetMinMax')})

	gen.insert_binding_code('''
static std::shared_ptr<hg::RenderMaterial> _RenderGeometry_GetMaterial(hg::RenderGeometry *geo, uint32_t idx) {
	if (idx >= geo->materials.size())
		return nullptr;
	return geo->materials[idx];
}

static size_t _RenderGeometry_GetMaterialCount(hg::RenderGeometry *geo) { return geo->materials.size(); } 
''')
	gen.bind_method(shared_geometry, 'GetMaterial', 'std::shared_ptr<hg::RenderMaterial>', ['uint32_t index'], {'proxy': None, 'route': route_lambda('_RenderGeometry_GetMaterial'), 'check_rval': check_bool_rval_lambda(gen, 'Empty material')})
	gen.bind_method(shared_geometry, 'GetMaterialCount', 'size_t', [], {'proxy': None, 'route': route_lambda('_RenderGeometry_GetMaterialCount')})

	gen.insert_binding_code('''
static void _RenderGeometry_SetLodProxy(hg::RenderGeometry *geo, std::shared_ptr<hg::RenderGeometry> &proxy, float distance) {
	geo->flag = hg::GeometryFlag(geo->flag & ~hg::GeometryFlagNullLodProxy);
	geo->lod_proxy = proxy;
	geo->lod_distance = distance;
}

static void _RenderGeometry_SetNullLodProxy(hg::RenderGeometry *geo) {
	geo->flag = hg::GeometryFlag(geo->flag | hg::GeometryFlagNullLodProxy);
	geo->lod_proxy = nullptr;
	geo->lod_distance = 0;
}

static void _RenderGeometry_SetShadowProxy(hg::RenderGeometry *geo, std::shared_ptr<hg::RenderGeometry> &proxy) {
	geo->flag = hg::GeometryFlag(geo->flag & ~hg::GeometryFlagNullShadowProxy);
	geo->shadow_proxy = proxy;
}

static void _RenderGeometry_SetNullShadowProxy(hg::RenderGeometry *geo) {
	geo->flag = hg::GeometryFlag(geo->flag | hg::GeometryFlagNullShadowProxy);
	geo->shadow_proxy = nullptr;
}
''')
	gen.bind_method(shared_geometry, 'SetLodProxy', 'void', ['std::shared_ptr<hg::RenderGeometry> &proxy', 'float distance'], {'proxy': None, 'route': route_lambda('_RenderGeometry_SetLodProxy')})
	gen.bind_method(shared_geometry, 'SetNullLodProxy', 'void', [], {'proxy': None, 'route': route_lambda('_RenderGeometry_SetNullLodProxy')})
	gen.bind_method(shared_geometry, 'SetShadowProxy', 'void', ['std::shared_ptr<hg::RenderGeometry> &proxy'], {'proxy': None, 'route': route_lambda('_RenderGeometry_SetShadowProxy')})
	gen.bind_method(shared_geometry, 'SetNullShadowProxy', 'void', [], {'proxy': None, 'route': route_lambda('_RenderGeometry_SetNullShadowProxy')})

	gen.end_class(shared_geometry)

	# hg::RenderStatistics
	gen.add_include('engine/render_stats.h')

	render_stats = gen.begin_class('hg::RenderStatistics')
	gen.bind_members(render_stats, ['hg::time_ns frame_start', 'size_t render_primitive_drawn', 'size_t line_drawn', 'size_t triangle_drawn', 'size_t instanced_batch_count', 'size_t instanced_batch_size'])
	gen.end_class(render_stats)

	# hg::ViewState
	view_state = gen.begin_class('hg::ViewState')
	gen.bind_members(view_state, ['hg::Rect<float> viewport', 'hg::Rect<float> clipping', 'hg::Matrix4 view', 'hg::Matrix44 projection', 'hg::FrustumPlanes frustum_planes', 'hg::Eye eye'])
	gen.end_class(view_state)

	# hg::RenderSystem
	gen.bind_named_enum('hg::RenderTechnique', ['TechniqueForward', 'TechniqueDeferred'], prefix='Render')
	lib.stl.bind_future_T(gen, 'hg::RenderTechnique', 'FutureRenderTechnique')

	gen.bind_constructor(shared_render_system, [], ['proxy'])

	gen.bind_method(shared_render_system, 'GetRenderer', 'const std::shared_ptr<hg::Renderer> &', [], ['proxy'])

	gen.bind_method(shared_render_system, 'Initialize', 'bool', ['std::shared_ptr<hg::Renderer> renderer', '?bool support_3d'], ['proxy'])
	gen.bind_method(shared_render_system, 'IsInitialized', 'bool', [], ['proxy'])

	gen.bind_method(shared_render_system, 'GetInternalResolution', 'hg::tVector2<int>', [], ['proxy'])
	gen.bind_method(shared_render_system, 'SetInternalResolution', 'void', ['const hg::tVector2<int> &resolution'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetViewportToInternalResolutionRatio', 'hg::tVector2<float>', [], ['proxy'])

	gen.bind_method(shared_render_system, 'GetStatistics', 'hg::RenderStatistics', [], ['proxy'])

	gen.bind_method(shared_render_system, 'SetAA', 'void', ['uint32_t sample_count'], ['proxy'])
	gen.bind_method(shared_render_system, 'PurgeCache', 'size_t', [], ['proxy'])
	gen.bind_method(shared_render_system, 'RefreshCacheEntry', 'void', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_render_system, 'HasMaterial', 'bool', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_render_system, 'GetMaterial', 'std::shared_ptr<hg::RenderMaterial>', ['const std::string &name'],  {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Material not found')})
	gen.bind_method(shared_render_system, 'LoadMaterial', 'std::shared_ptr<hg::RenderMaterial>', ['const std::string &name', '?bool use_cache'], ['proxy'])
	gen.bind_method(shared_render_system, 'CreateMaterial', 'std::shared_ptr<hg::RenderMaterial>', ['const std::shared_ptr<hg::Material> &material', '?bool use_cache'], ['proxy'])

	gen.bind_method(shared_render_system, 'HasGeometry', 'bool', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_render_system, 'GetGeometry', 'std::shared_ptr<hg::RenderGeometry>', ['const std::string &name'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Geometry not found')})
	gen.bind_method(shared_render_system, 'LoadGeometry', 'std::shared_ptr<hg::RenderGeometry>', ['const std::string &name', '?bool use_cache'], ['proxy'])
	gen.bind_method(shared_render_system, 'CreateGeometry', 'std::shared_ptr<hg::RenderGeometry>', ['const std::shared_ptr<hg::Geometry> &geometry', '?bool use_cache'], ['proxy'])

	gen.bind_method(shared_render_system, 'HasSurfaceShader', 'bool', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_render_system, 'GetSurfaceShader', 'std::shared_ptr<hg::SurfaceShader>', ['const std::string &name'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Surface shader not found')})
	gen.bind_method(shared_render_system, 'LoadSurfaceShader', 'std::shared_ptr<hg::SurfaceShader>', ['const std::string &name', '?bool use_cache'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetRenderTechnique', 'hg::RenderTechnique', [], ['proxy'])
	gen.bind_method(shared_render_system, 'SetRenderTechnique', 'void', ['hg::RenderTechnique render_technique'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetFrameClock', 'hg::time_ns', [], ['proxy'])

	gen.bind_method(shared_render_system, 'SetView', 'void', ['const hg::Matrix4 &view', 'const hg::Matrix44 &projection', '?hg::Eye eye'], ['proxy'])
	gen.bind_method(shared_render_system, 'GetEye', 'hg::Eye', [], ['proxy'])

	gen.bind_method(shared_render_system, 'GetViewState', 'hg::ViewState', [], ['proxy'])
	gen.bind_method(shared_render_system, 'SetViewState', 'void', ['const hg::ViewState &view_state'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetViewFrustum', 'const hg::FrustumPlanes &', [], ['proxy'])

	gen.bind_method(shared_render_system, 'DrawRasterFontBatch', 'void', [], ['proxy'])

	gen.bind_method(shared_render_system, 'SetShaderAuto', 'bool', ['bool has_color', '?const hg::Texture &texture'], ['proxy'])

	gen.insert_binding_code('''\
static void RenderSystemDrawLine_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos) { render_system->DrawLine(count, pos.data()); }
static void RenderSystemDrawLine_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col) { render_system->DrawLine(count, pos.data(), col.data()); }
static void RenderSystemDrawLine_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col, const std::vector<hg::tVector2<float>> &uv) { render_system->DrawLine(count, pos.data(), col.data(), uv.data()); }

static void RenderSystemDrawTriangle_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos) { render_system->DrawTriangle(count, pos.data()); }
static void RenderSystemDrawTriangle_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col) { render_system->DrawTriangle(count, pos.data(), col.data()); }
static void RenderSystemDrawTriangle_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col, const std::vector<hg::tVector2<float>> &uv) { render_system->DrawTriangle(count, pos.data(), col.data(), uv.data()); }

static void RenderSystemDrawSprite_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos) { render_system->DrawSprite(count, pos.data()); }
static void RenderSystemDrawSprite_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col) { render_system->DrawSprite(count, pos.data(), col.data()); }
static void RenderSystemDrawSprite_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col, const std::vector<float> &size) { render_system->DrawSprite(count, pos.data(), col.data(), size.data()); }
\n''', 'wrapper signatures to cast target language list and std::vector to raw pointers')

	DrawLine_wrapper_route = lambda args: 'RenderSystemDrawLine_wrapper(%s);' % (', '.join(args))
	DrawTriangle_wrapper_route = lambda args: 'RenderSystemDrawTriangle_wrapper(%s);' % (', '.join(args))
	DrawSprite_wrapper_route = lambda args: 'RenderSystemDrawSprite_wrapper(%s);' % (', '.join(args))

	draw_line_protos = [
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos'], {'proxy': None, 'route': DrawLine_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col'], {'proxy': None, 'route': DrawLine_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col', 'const std::vector<hg::tVector2<float>> &uv'], {'proxy': None, 'route': DrawLine_wrapper_route})	]
	gen.bind_method_overloads(shared_render_system, 'DrawLine', expand_std_vector_proto(gen, draw_line_protos))

	draw_triangle_protos = [
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos'], {'proxy': None, 'route': DrawTriangle_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col'], {'proxy': None, 'route': DrawTriangle_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col', 'const std::vector<hg::tVector2<float>> &uv'], {'proxy': None, 'route': DrawTriangle_wrapper_route})	]
	gen.bind_method_overloads(shared_render_system, 'DrawTriangle', expand_std_vector_proto(gen, draw_triangle_protos))

	draw_sprite_protos = [
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos'], {'proxy': None, 'route': DrawSprite_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col'], {'proxy': None, 'route': DrawSprite_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col', 'const std::vector<float> &size'], {'proxy': None, 'route': DrawSprite_wrapper_route})	]
	gen.bind_method_overloads(shared_render_system, 'DrawSprite', expand_std_vector_proto(gen, draw_sprite_protos))
	
	gen.insert_binding_code('''\
static void RenderSystemDrawLineAuto_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos) { render_system->DrawLineAuto(count, pos.data()); }
static void RenderSystemDrawLineAuto_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col) { render_system->DrawLineAuto(count, pos.data(), col.data()); }
static void RenderSystemDrawLineAuto_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col, const std::vector<hg::tVector2<float>> &uv, const hg::Texture *texture) { render_system->DrawLineAuto(count, pos.data(), col.data(), uv.data(), texture); }

static void RenderSystemDrawTriangleAuto_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos) { render_system->DrawTriangleAuto(count, pos.data()); }
static void RenderSystemDrawTriangleAuto_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col) { render_system->DrawTriangleAuto(count, pos.data(), col.data()); }
static void RenderSystemDrawTriangleAuto_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const std::vector<hg::Color> &col, const std::vector<hg::tVector2<float>> &uv, const hg::Texture *texture) { render_system->DrawTriangleAuto(count, pos.data(), col.data(), uv.data(), texture); }

static void RenderSystemDrawSpriteAuto_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const hg::Texture &texture) { render_system->DrawSpriteAuto(count, pos.data(), texture); }
static void RenderSystemDrawSpriteAuto_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const hg::Texture &texture, const std::vector<hg::Color> &col) { render_system->DrawSpriteAuto(count, pos.data(), texture, col.data()); }
static void RenderSystemDrawSpriteAuto_wrapper(hg::RenderSystem *render_system, uint32_t count, const std::vector<hg::Vector3> &pos, const hg::Texture &texture, const std::vector<hg::Color> &col, const std::vector<float> &size) { render_system->DrawSpriteAuto(count, pos.data(), texture, col.data(), size.data()); }
\n''', 'wrapper signatures to cast target language list and std::vector to raw pointers')

	DrawLineAuto_wrapper_route = lambda args: 'RenderSystemDrawLineAuto_wrapper(%s);' % (', '.join(args))
	DrawTriangleAuto_wrapper_route = lambda args: 'RenderSystemDrawTriangleAuto_wrapper(%s);' % (', '.join(args))
	DrawSpriteAuto_wrapper_route = lambda args: 'RenderSystemDrawSpriteAuto_wrapper(%s);' % (', '.join(args))

	draw_line_auto_protos = [
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos'], {'proxy': None, 'route': DrawLineAuto_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col'], {'proxy': None, 'route': DrawLineAuto_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col', 'const std::vector<hg::tVector2<float>> &uv', 'const hg::Texture *texture'], {'proxy': None, 'route': DrawLineAuto_wrapper_route})	]
	gen.bind_method_overloads(shared_render_system, 'DrawLineAuto', expand_std_vector_proto(gen, draw_line_auto_protos))

	draw_triangle_auto_protos = [
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos'], {'proxy': None, 'route': DrawTriangleAuto_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col'], {'proxy': None, 'route': DrawTriangleAuto_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const std::vector<hg::Color> &col', 'const std::vector<hg::tVector2<float>> &uv', 'const hg::Texture *texture'], {'proxy': None, 'route': DrawTriangleAuto_wrapper_route})	]
	gen.bind_method_overloads(shared_render_system, 'DrawTriangleAuto', expand_std_vector_proto(gen, draw_triangle_auto_protos))

	draw_sprite_auto_protos = [
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const hg::Texture &texture'], {'proxy': None, 'route': DrawSpriteAuto_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const hg::Texture &texture', 'const std::vector<hg::Color> &col'], {'proxy': None, 'route': DrawSpriteAuto_wrapper_route}),
		('void', ['uint32_t count', 'const std::vector<hg::Vector3> &pos', 'const hg::Texture &texture', 'const std::vector<hg::Color> &col', 'const std::vector<float> &size'], {'proxy': None, 'route': DrawSpriteAuto_wrapper_route})	]
	gen.bind_method_overloads(shared_render_system, 'DrawSpriteAuto', expand_std_vector_proto(gen, draw_sprite_auto_protos))

	gen.bind_method(shared_render_system, 'DrawQuad2D', 'void', ['const hg::Rect<float> &src_rect', 'const hg::Rect<float> &dst_rect'], ['proxy'])
	gen.bind_method(shared_render_system, 'DrawFullscreenQuad', 'void', ['const hg::tVector2<float> &uv'], ['proxy'])

	gen.bind_method(shared_render_system, 'DrawGeometrySimple', 'void', ['const hg::RenderGeometry &geometry'], ['proxy'])
	#gen.bind_method(shared_render_system, 'DrawSceneSimple', 'void', ['const hg::Scene &scene'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetShadowMap', 'const std::shared_ptr<hg::Texture> &', [], ['proxy'])
	
	gen.insert_binding_code('''static std::shared_ptr<hg::Texture> _GetDepthReadTexture(hg::RenderSystem *render_system) { return render_system->t_depth_read; }\n''', 'Get Depth read texture')
	gen.bind_method(shared_render_system, 'GetDepthReadTexture', 'std::shared_ptr<hg::Texture>', [], {'proxy': None, 'route': route_lambda('_GetDepthReadTexture')})

	gen.end_class(shared_render_system)

	gen.bind_function('SetShaderEngineValues', 'void', ['hg::RenderSystem &render_system'])

	# hg::RenderSystemAsync
	gen.add_include('engine/render_system_async.h')

	render_system_async = gen.begin_class('hg::RenderSystemAsync', bound_name='RenderSystemAsync_nobind', noncopyable=True, nobind=True)
	gen.end_class(render_system_async)

	shared_render_system_async = gen.begin_class('std::shared_ptr<hg::RenderSystemAsync>', bound_name='RenderSystemAsync', features={'proxy': lib.stl.SharedPtrProxyFeature(render_system_async)})
	gen.bind_constructor(shared_render_system_async, ['std::shared_ptr<hg::RenderSystem> render_system'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'GetRenderSystem', 'const std::shared_ptr<hg::RenderSystem> &', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'GetRenderTechnique', 'std::future<hg::RenderTechnique>', [], ['proxy'])
	gen.bind_method(shared_render_system_async, 'SetRenderTechnique', 'void', ['hg::RenderTechnique technique'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'GetInternalResolution', 'std::future<hg::tVector2<int>>', [], ['proxy'])
	gen.bind_method(shared_render_system_async, 'SetInternalResolution', 'void', ['const hg::tVector2<int> &resolution'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'GetViewportToInternalResolutionRatio', 'std::future<hg::tVector2<float>>', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'SetAA', 'void', ['uint32_t sample_count'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'SetView', 'void', ['const hg::Matrix4 &view', 'const hg::Matrix44 &projection'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'PurgeCache', 'std::future<size_t>', [], ['proxy'])
	gen.bind_method(shared_render_system_async, 'RefreshCacheEntry', 'void', ['const std::string &name'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'DrawRasterFontBatch', 'void', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'HasMaterial', 'bool', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_render_system_async, 'GetMaterial', 'std::shared_ptr<hg::RenderMaterial>', ['const std::string &name'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Material not found')})
	gen.bind_method_overloads(shared_render_system_async, 'LoadMaterial', [
		('std::shared_ptr<hg::RenderMaterial>', ['const std::string &name', '?bool use_cache'], ['proxy']),
		('std::shared_ptr<hg::RenderMaterial>', ['const std::string &name', 'const std::string &source', '?hg::DocumentFormat format', '?bool use_cache'], ['proxy'])
	])
	gen.bind_method(shared_render_system_async, 'CreateMaterial', 'std::shared_ptr<hg::RenderMaterial>', ['const std::shared_ptr<hg::Material> &material', '?bool use_cache'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'HasGeometry', 'bool', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_render_system_async, 'GetGeometry', 'std::shared_ptr<hg::RenderGeometry>', ['const std::string &name'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Geometry not found')})
	gen.bind_method_overloads(shared_render_system_async, 'LoadGeometry', [
		('std::shared_ptr<hg::RenderGeometry>', ['const std::string &name', '?bool use_cache'], ['proxy']),
		('std::shared_ptr<hg::RenderGeometry>', ['const std::string &name', 'const std::string &source', '?hg::DocumentFormat format', '?bool use_cache'], ['proxy'])
	])
	gen.bind_method(shared_render_system_async, 'CreateGeometry', 'std::shared_ptr<hg::RenderGeometry>', ['const std::shared_ptr<hg::Geometry> &geometry', '?bool use_cache'], ['proxy'])

	gen.bind_method(shared_render_system_async, 'HasSurfaceShader', 'bool', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_render_system_async, 'GetSurfaceShader', 'std::shared_ptr<hg::SurfaceShader>', ['const std::string &name'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'Surface shader not found')})
	gen.bind_method(shared_render_system_async, 'LoadSurfaceShader', 'std::shared_ptr<hg::SurfaceShader>', ['const std::string &name', '?bool use_cache'], ['proxy'])

	"""
	void DrawLine(uint32_t count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<Vector2> *uv = nullptr) {
	void DrawTriangle(uint32_t count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<Vector2> *uv = nullptr) {
	void DrawSprite(uint32_t count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<float> *size = nullptr, float global_size = 1.f) {
	void DrawLineAuto(uint32_t count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<Vector2> *uv = nullptr, gpu::std::shared_ptr<Texture> texture = nullptr) {
	void DrawTriangleAuto(uint32_t count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<Vector2> *uv = nullptr, gpu::std::shared_ptr<Texture> texture = nullptr) {
	void DrawSpriteAuto(uint32_t count, const std::vector<Vector3> &vtx, const std::vector<Color> *color = nullptr, const std::vector<float> *size = nullptr, gpu::std::shared_ptr<Texture> texture = nullptr, float global_size = 1.f) {
	"""

	gen.bind_method(shared_render_system_async, 'BeginDrawFrame', 'void', [], ['proxy'])
	gen.bind_method(shared_render_system_async, 'EndDrawFrame', 'void', [], ['proxy'])

	#gen.bind_method(shared_render_system_async, 'DrawRenderablesPicking', 'std::future<bool>', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'Initialize', 'std::future<bool>', ['std::shared_ptr<hg::Renderer> renderer', '?bool support_3d'], ['proxy'])
	gen.bind_method(shared_render_system_async, 'Free', 'std::future<void>', [], ['proxy'])

	gen.bind_method(shared_render_system_async, 'SetShaderEngineValues', 'void', [], ['proxy'])

	gen.end_class(shared_render_system_async)
	
	# hg::RenderPass
	gen.bind_named_enum('hg::RenderPass::Pass', ['Opaque', 'Transparent', 'FramebufferDependent', 'Shadow'], bound_name='RenderPass', prefix='RenderPass')
	gen.bind_named_enum('hg::RenderPass::Shader', ['Depth', 'DS_GBufferMRT4', 'FS_Constant', 'FS_PointLight', 'FS_PointLightShadowMapping', 'FS_LinearLight', 'FS_LinearLightShadowMapping', 'FS_SpotLight', 'FS_SpotLightShadowMapping', 'FS_SpotLightProjection', 'FS_SpotLightProjectionShadowMapping', 'PP_NormalDepth', 'PP_Velocity', 'Picking'], bound_name='RenderPassShader', prefix='RenderPassShader')

	# hg::RasterFont
	gen.add_include('engine/raster_font.h')

	raster_font = gen.begin_class('hg::RasterFont', bound_name='RasterFont_nobind', nobind=True)
	gen.end_class(raster_font)

	shared_raster_font = gen.begin_class('std::shared_ptr<hg::RasterFont>', bound_name='RasterFont', features={'proxy': lib.stl.SharedPtrProxyFeature(raster_font)})
	gen.bind_constructor_overloads(shared_raster_font, [
		(['const std::string &font_path', 'float font_size'], ['proxy']),
		(['const std::string &font_path', 'float font_size', 'uint32_t page_resolution'], ['proxy']),
		(['const std::string &font_path', 'float font_size', 'uint32_t page_resolution', 'uint32_t glyph_margin'], ['proxy']),
		(['const std::string &font_path', 'float font_size', 'uint32_t page_resolution', 'uint32_t glyph_margin', 'bool autohint'], ['proxy'])
	])

	gen.bind_method(shared_raster_font, 'Prepare', 'bool', ['hg::RenderSystem &render_system', 'const std::string &text'], ['proxy'])
	gen.bind_method_overloads(shared_raster_font, 'Write', [
		('bool', ['hg::RenderSystem &render_system', 'const std::string &text', 'const hg::Matrix4 &matrix'], ['proxy']),
		('bool', ['hg::RenderSystem &render_system', 'const std::string &text', 'const hg::Matrix4 &matrix', 'hg::Color color'], ['proxy']),
		('bool', ['hg::RenderSystem &render_system', 'const std::string &text', 'const hg::Matrix4 &matrix', 'hg::Color color', 'float scale'], ['proxy']),
		('bool', ['hg::RenderSystem &render_system', 'const std::string &text', 'const hg::Matrix4 &matrix', 'hg::Color color', 'float scale', 'bool snap_glyph_to_grid', 'bool orient_toward_camera'], ['proxy'])
	])

	gen.bind_method(shared_raster_font, 'GetTextRect', 'hg::Rect<float>', ['hg::RenderSystem &render_system', 'const std::string &text'], ['proxy'])

	gen.bind_method(shared_raster_font, 'Load', 'bool', ['const hg::RenderSystem &render_system', 'const std::string &base_path'], ['proxy'])
	gen.bind_method(shared_raster_font, 'Save', 'bool', ['const hg::RenderSystem &render_system', 'const std::string &base_path'], ['proxy'])

	gen.bind_method(shared_raster_font, 'GetSize', 'float', [], ['proxy'])
	gen.end_class(shared_raster_font)

	# hg::SimpleGraphicEngine
	gen.add_include('engine/simple_graphic_engine.h')

	simple_graphic_engine = gen.begin_class('hg::SimpleGraphicEngine', bound_name='SimpleGraphicEngine', noncopyable=True)
	gen.bind_constructor(simple_graphic_engine, [])

	gen.bind_method(simple_graphic_engine, 'SetSnapGlyphToGrid', 'void', ['bool snap'])
	gen.bind_method(simple_graphic_engine, 'GetSnapGlyphToGrid', 'bool', [])

	gen.bind_method(simple_graphic_engine, 'SetBlendMode', 'void', ['hg::BlendMode mode'])
	gen.bind_method(simple_graphic_engine, 'GetBlendMode', 'hg::BlendMode', [])
	gen.bind_method(simple_graphic_engine, 'SetCullMode', 'void', ['hg::CullMode mode'])
	gen.bind_method(simple_graphic_engine, 'GetCullMode', 'hg::CullMode', [])

	gen.bind_method(simple_graphic_engine, 'SetDepthWrite', 'void', ['bool enable'])
	gen.bind_method(simple_graphic_engine, 'GetDepthWrite', 'bool', [])
	gen.bind_method(simple_graphic_engine, 'SetDepthTest', 'void', ['bool enable'])
	gen.bind_method(simple_graphic_engine, 'GetDepthTest', 'bool', [])

	gen.insert_binding_code('''
static void _Quad(hg::SimpleGraphicEngine *engine, float ax, float ay, float az, float bx, float by, float bz, float cx, float cy, float cz, float dx, float dy, float dz, const hg::Color &a_color, const hg::Color &b_color, const hg::Color &c_color, const hg::Color &d_color) {
	engine->Quad(ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz, 0, 0, 0, 0, nullptr, a_color, b_color, c_color, d_color);
}
''')

	gen.bind_method(simple_graphic_engine, 'Line', 'void', ['float sx', 'float sy', 'float sz', 'float ex', 'float ey', 'float ez', 'const hg::Color &start_color', 'const hg::Color &end_color'])
	gen.bind_method(simple_graphic_engine, 'Triangle', 'void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'const hg::Color &a_color', 'const hg::Color &b_color', 'const hg::Color &c_color'])
	gen.bind_method_overloads(simple_graphic_engine, 'Text', [
		('void', ['float x', 'float y', 'float z', 'const std::string &text', 'const hg::Color &color', 'std::shared_ptr<hg::RasterFont> font', 'float scale'], []),
		('void', ['const hg::Matrix4 &mat', 'const std::string &text', 'const hg::Color &color', 'std::shared_ptr<hg::RasterFont> font', 'float scale'], [])
	])
	gen.bind_method_overloads(simple_graphic_engine, 'Quad', [
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'const hg::Color &a_color', 'const hg::Color &b_color', 'const hg::Color &c_color', 'const hg::Color &d_color'], {'route': lambda args: '_Quad(%s);' % ', '.join(args)}),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'float uv_sx', 'float uv_sy', 'float uv_ex', 'float uv_ey', 'std::shared_ptr<hg::Texture> texture', 'const hg::Color &a_color', 'const hg::Color &b_color', 'const hg::Color &c_color', 'const hg::Color &d_color'], [])
	])
	gen.bind_method(simple_graphic_engine, 'Geometry', 'void', ['float x', 'float y', 'float z', 'float ex', 'float ey', 'float ez', 'float sx', 'float sy', 'float sz', 'std::shared_ptr<hg::RenderGeometry> geometry'])

	gen.bind_method(simple_graphic_engine, 'Draw', 'void', ['hg::RenderSystem &render_system'])
	gen.bind_method(simple_graphic_engine, 'Clear', 'void', ['hg::RenderSystem &render_system'])

	gen.bind_method(simple_graphic_engine, 'Flush', 'void', ['hg::RenderSystem &render_system'])

	gen.end_class(simple_graphic_engine)


def bind_iso_surface(gen):
	gen.add_include('engine/iso_surface.h')

	iso_surface = gen.begin_class('hg::IsoSurface', bound_name='IsoSurface_nobind', nobind=True)
	gen.end_class(iso_surface)

	shared_iso_surface = gen.begin_class('std::shared_ptr<hg::IsoSurface>', bound_name='IsoSurface', features={'proxy': lib.stl.SharedPtrProxyFeature(iso_surface)})
	gen.bind_constructor(shared_iso_surface, [], ['proxy'])
	gen.bind_method(shared_iso_surface, 'Clear', 'void', [], ['proxy'])
	gen.bind_method(shared_iso_surface, 'AddTriangle', 'void', ['const hg::Vector3 &p0', 'const hg::Vector3 &p1', 'const hg::Vector3 &p2'], ['proxy'])
	gen.bind_method(shared_iso_surface, 'GetTriangleCount', 'size_t', [], ['proxy'])
	gen.end_class(shared_iso_surface)

	#
	gen.insert_binding_code('''\
static void _PolygoniseIsoSurface(uint32_t width, uint32_t height, uint32_t depth, const hg::BinaryData &field, float isolevel, hg::IsoSurface &out, const hg::Vector3 &unit = hg::Vector3::One) { return hg::PolygoniseIsoSurface(width, height, depth, reinterpret_cast<const float *>(field.GetData()), isolevel, out, unit); }
''')
	gen.bind_function('PolygoniseIsoSurface', 'void', ['uint32_t width', 'uint32_t height', 'uint32_t depth', 'const hg::BinaryData &field', 'float isolevel', 'hg::IsoSurface &iso', '?const hg::Vector3 &unit'], {'route': lambda args: '_PolygoniseIsoSurface(%s);' % (', '.join(args))})

	gen.bind_function('IsoSurfaceToCoreGeometry', 'void', ['const hg::IsoSurface &iso', 'hg::Geometry &out'], bound_name='IsoSurfaceToGeometry')
	gen.bind_function('IsoSurfaceToRenderGeometry', 'std::future<void>', ['std::shared_ptr<hg::RenderSystem> render_system', 'std::shared_ptr<hg::IsoSurface> iso', 'std::shared_ptr<hg::RenderGeometry> geo', 'std::shared_ptr<hg::RenderMaterial> mat'])

	gen.insert_binding_code('''\
static std::future<void> _PolygoniseIsoSurfaceToRenderGeometry(const std::shared_ptr<hg::RenderSystem> &render_system, const std::shared_ptr<hg::RenderGeometry> &geo, const std::shared_ptr<hg::RenderMaterial> &mat, uint32_t width, uint32_t height, uint32_t depth, const hg::BinaryData &field, float isolevel, const std::shared_ptr<hg::IsoSurface> &iso, const hg::Vector3 &unit = hg::Vector3::One) {
	return hg::PolygoniseIsoSurfaceToRenderGeometry(render_system, geo, mat, width, height, depth, reinterpret_cast<const float *>(field.GetData()), isolevel, iso, unit);
}
''')
	gen.bind_function('PolygoniseIsoSurfaceToRenderGeometry', 
'std::future<void>', ['const std::shared_ptr<hg::RenderSystem> &render_system', 'const std::shared_ptr<hg::RenderGeometry> &geo', 'const std::shared_ptr<hg::RenderMaterial> &mat', 'uint32_t width', 'uint32_t height', 'uint32_t depth', 'const hg::BinaryData &field', 'float isolevel', 'const std::shared_ptr<hg::IsoSurface> &iso', '?const hg::Vector3 &unit'], {'route': lambda args: '_PolygoniseIsoSurfaceToRenderGeometry(%s);' % (', '.join(args))})


def bind_plus(gen):
	gen.add_include('engine/plus.h')

	# hg::RenderWindow
	window_conv = gen.begin_class('hg::RenderWindow')
	gen.bind_members(window_conv, ['hg::Window window', 'hg::Surface surface'])
	gen.end_class(window_conv)

	# hg::Plus
	plus_conv = gen.begin_class('hg::Plus', noncopyable=True)

	gen.bind_method(plus_conv, 'CreateWorkers', 'void', [])
	gen.bind_method(plus_conv, 'DeleteWorkers', 'void', [])

	gen.bind_method(plus_conv, 'Mount', 'void', ['?const std::string &path'])
	gen.bind_method(plus_conv, 'MountAs', 'void', ['const std::string &path', 'const std::string &prefix'])
	gen.bind_method(plus_conv, 'Unmount', 'void', ['const std::string &path'])
	gen.bind_method(plus_conv, 'UnmountAll', 'void', [])

	gen.bind_method(plus_conv, 'GetRenderer', 'std::shared_ptr<hg::Renderer>', [], {'check_rval': check_bool_rval_lambda(gen, 'no renderer, was RenderInit called succesfully?')})
	gen.bind_method(plus_conv, 'GetRendererAsync', 'std::shared_ptr<hg::RendererAsync>', [], {'check_rval': check_bool_rval_lambda(gen, 'no renderer, was RenderInit called succesfully?')})

	gen.bind_method(plus_conv, 'GetRenderSystem', 'std::shared_ptr<hg::RenderSystem>', [], {'check_rval': check_bool_rval_lambda(gen, 'no render system, was RenderInit called succesfully?')})
	gen.bind_method(plus_conv, 'GetRenderSystemAsync', 'std::shared_ptr<hg::RenderSystemAsync>', [], {'check_rval': check_bool_rval_lambda(gen, 'no render system, was RenderInit called succesfully?')})

	gen.bind_method(plus_conv, 'AudioInit', 'bool', [], {'check_rval': check_bool_rval_lambda(gen, 'AudioInit failed, was LoadPlugins called succesfully?')})
	gen.bind_method(plus_conv, 'AudioUninit', 'void', [])

	gen.bind_method(plus_conv, 'GetMixer', 'std::shared_ptr<hg::Mixer>', [], {'check_rval': check_bool_rval_lambda(gen, 'no mixer, was AudioInit called succesfully?')})
	gen.bind_method(plus_conv, 'GetMixerAsync', 'std::shared_ptr<hg::MixerAsync>', [], {'check_rval': check_bool_rval_lambda(gen, 'no mixer, was AudioInit called succesfully?')})

	gen.bind_named_enum('hg::Plus::AppEndCondition', ['EndOnEscapePressed', 'EndOnDefaultWindowClosed', 'EndOnAny'], prefix='App')

	gen.bind_method_overloads(plus_conv, 'IsAppEnded', [
		('bool', [], []),
		('bool', ['hg::Plus::AppEndCondition flags'], [])
	])

	gen.insert_binding_code('''\
static bool _Plus_RenderInit(hg::Plus *plus, int width, int height, int aa = 1, hg::Window::Visibility vis = hg::Window::Windowed, bool debug = false) { return plus->RenderInit(width, height, {}, aa, vis, debug); }
''')
	gen.bind_method_overloads(plus_conv, 'RenderInit', [
		('bool', ['int width', 'int height', '?const std::string &core_path', '?int aa', '?hg::Window::Visibility visibility', '?bool debug'], {'check_rval': check_bool_rval_lambda(gen, 'RenderInit failed, was LoadPlugins called succesfully?')}),
		('bool', ['int width', 'int height', 'int aa', '?hg::Window::Visibility visibility', '?bool debug'], {'check_rval': check_bool_rval_lambda(gen, 'RenderInit failed, was LoadPlugins called succesfully?'), 'route': lambda args: '_Plus_RenderInit(%s);' % (', '.join(args))})
	])
	gen.bind_method(plus_conv, 'RenderUninit', 'void', [])

	gen.bind_method(plus_conv, 'NewRenderWindow', 'hg::RenderWindow', ['int width', 'int height', '?hg::Window::Visibility visibility'])
	gen.bind_method(plus_conv, 'FreeRenderWindow', 'void', ['hg::RenderWindow &window'])

	gen.bind_method(plus_conv, 'GetRenderWindow', 'hg::RenderWindow', [])
	gen.bind_method_overloads(plus_conv, 'SetRenderWindow', [
		('void', ['hg::RenderWindow &window'], {'exception': 'check your program for a missing ImGuiUnlock call'}),
		('void', [], {'exception': 'check your program for a missing ImGuiUnlock call'})
	])

	gen.bind_method(plus_conv, 'GetRenderWindowSize', 'hg::tVector2<int>', ['const hg::RenderWindow &window'])
	gen.bind_method(plus_conv, 'UpdateRenderWindow', 'void', ['const hg::RenderWindow &window'])

	gen.bind_method_overloads(plus_conv, 'SetWindowTitle', [
		('void', ['const std::string &title'], {}),
		('void', ['const hg::RenderWindow &window', 'const std::string &title'], {})
	])

	gen.bind_method(plus_conv, 'InitExtern', 'void', ['std::shared_ptr<hg::Renderer> renderer', 'std::shared_ptr<hg::RendererAsync> renderer_async', 'std::shared_ptr<hg::RenderSystem> render_system', 'std::shared_ptr<hg::RenderSystemAsync> render_system_async'])
	gen.bind_method(plus_conv, 'UninitExtern', 'void', [])

	gen.bind_method(plus_conv, 'Set2DOriginIsTopLeft', 'void', ['bool top_left'])
	gen.bind_method(plus_conv, 'SetFixed2DResolution', 'void', ['float w', 'float h'])
	gen.bind_method(plus_conv, 'GetFixed2DResolution', 'hg::tVector2<float>', [])

	gen.bind_method(plus_conv, 'Commit2D', 'void', [])
	gen.bind_method(plus_conv, 'Commit3D', 'void', [])

	gen.bind_method(plus_conv, 'GetScreenWidth', 'int', [])
	gen.bind_method(plus_conv, 'GetScreenHeight', 'int', [])

	gen.bind_method(plus_conv, 'Flip', 'void', [])

	gen.bind_method(plus_conv, 'EndFrame', 'void', [])

	gen.bind_method(plus_conv, 'SetBlend2D', 'void', ['hg::BlendMode mode'])
	gen.bind_method(plus_conv, 'GetBlend2D', 'hg::BlendMode', [])
	gen.bind_method(plus_conv, 'SetCulling2D', 'void', ['hg::CullMode mode'])
	gen.bind_method(plus_conv, 'GetCulling2D', 'hg::CullMode', [])

	gen.bind_method(plus_conv, 'SetBlend3D', 'void', ['hg::BlendMode mode'])
	gen.bind_method(plus_conv, 'GetBlend3D', 'hg::BlendMode', [])
	gen.bind_method(plus_conv, 'SetCulling3D', 'void', ['hg::CullMode mode'])
	gen.bind_method(plus_conv, 'GetCulling3D', 'hg::CullMode', [])

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
		('void', ['hg::Color color'], [])
	])

	gen.bind_method_overloads(plus_conv, 'Plot2D', [
		('void', ['float x', 'float y'], []),
		('void', ['float x', 'float y', 'hg::Color color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Line2D', [
		('void', ['float sx', 'float sy', 'float ex', 'float ey'], []),
		('void', ['float sx', 'float sy', 'float ex', 'float ey', 'hg::Color start_color', 'hg::Color end_color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Triangle2D', [
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy'], []),
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'hg::Color a_color', 'hg::Color b_color', 'hg::Color c_color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Quad2D', [
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'float dx', 'float dy'], []),
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'float dx', 'float dy', 'hg::Color a_color', 'hg::Color b_color', 'hg::Color c_color', 'hg::Color d_color'], []),
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'float dx', 'float dy', 'hg::Color a_color', 'hg::Color b_color', 'hg::Color c_color', 'hg::Color d_color', 'std::shared_ptr<hg::Texture> texture'], []),
		('void', ['float ax', 'float ay', 'float bx', 'float by', 'float cx', 'float cy', 'float dx', 'float dy', 'hg::Color a_color', 'hg::Color b_color', 'hg::Color c_color', 'hg::Color d_color', 'std::shared_ptr<hg::Texture> texture', 'float uv_sx', 'float uv_sy', 'float uv_ex', 'float uv_ey'], [])
	])

	gen.bind_method_overloads(plus_conv, 'Line3D', [
		('void', ['float sx', 'float sy', 'float sz', 'float ex', 'float ey', 'float ez'], []),
		('void', ['float sx', 'float sy', 'float sz', 'float ex', 'float ey', 'float ez', 'hg::Color start_color', 'hg::Color end_color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Triangle3D', [
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz'], []),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'hg::Color a_color', 'hg::Color b_color', 'hg::Color c_color'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Quad3D', [
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz'], []),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'hg::Color a_color', 'hg::Color b_color', 'hg::Color c_color', 'hg::Color d_color'], []),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'hg::Color a_color', 'hg::Color b_color', 'hg::Color c_color', 'hg::Color d_color', 'std::shared_ptr<hg::Texture> texture'], []),
		('void', ['float ax', 'float ay', 'float az', 'float bx', 'float by', 'float bz', 'float cx', 'float cy', 'float cz', 'float dx', 'float dy', 'float dz', 'hg::Color a_color', 'hg::Color b_color', 'hg::Color c_color', 'hg::Color d_color', 'std::shared_ptr<hg::Texture> texture', 'float uv_sx', 'float uv_sy', 'float uv_ex', 'float uv_ey'], [])
	])

	gen.bind_method(plus_conv, 'SetFont', 'void', ['const std::string &path'])
	gen.bind_method(plus_conv, 'GetFont', 'const std::string &', [])

	gen.bind_method_overloads(plus_conv, 'Text2D', [
		('void', ['float x', 'float y', 'const std::string &text'], []),
		('void', ['float x', 'float y', 'const std::string &text', 'float size'], []),
		('void', ['float x', 'float y', 'const std::string &text', 'float size', 'hg::Color color'], []),
		('void', ['float x', 'float y', 'const std::string &text', 'float size', 'hg::Color color', 'const std::string &font_path'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Text3D', [
		('void', ['float x', 'float y', 'float z', 'const std::string &text'], []),
		('void', ['float x', 'float y', 'float z', 'const std::string &text', 'float size'], []),
		('void', ['float x', 'float y', 'float z', 'const std::string &text', 'float size', 'hg::Color color'], []),
		('void', ['float x', 'float y', 'float z', 'const std::string &text', 'float size', 'hg::Color color', 'const std::string &font_path'], [])
	])

	gen.bind_method(plus_conv, 'GetTextRect', 'hg::Rect<float>', ['const std::string &text', '?float size', '?const std::string &font_path'])

	gen.bind_method_overloads(plus_conv, 'Sprite2D', [
		('void', ['float x', 'float y', 'float size', 'const std::string &image_path'], []),
		('void', ['float x', 'float y', 'float size', 'const std::string &image_path', 'hg::Color tint'], []),
		('void', ['float x', 'float y', 'float size', 'const std::string &image_path', 'hg::Color tint', 'float pivot_x', 'float pivot_y'], []),
		('void', ['float x', 'float y', 'float size', 'const std::string &image_path', 'hg::Color tint', 'float pivot_x', 'float pivot_y', 'bool flip_h', 'bool flip_v'], [])
	])
	gen.bind_method_overloads(plus_conv, 'RotatedSprite2D', [
		('void', ['float x', 'float y', 'float angle', 'float size', 'const std::string &image_path'], []),
		('void', ['float x', 'float y', 'float angle', 'float size', 'const std::string &image_path', 'hg::Color tint'], []),
		('void', ['float x', 'float y', 'float angle', 'float size', 'const std::string &image_path', 'hg::Color tint', 'float pivot_x', 'float pivot_y'], []),
		('void', ['float x', 'float y', 'float angle', 'float size', 'const std::string &image_path', 'hg::Color tint', 'float pivot_x', 'float pivot_y', 'bool flip_h', 'bool flip_v'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Image2D', [
		('void', ['float x', 'float y', 'float scale', 'const std::string &image_path'], []),
		('void', ['float x', 'float y', 'float scale', 'const std::string &image_path', 'hg::Color tint'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Blit2D', [
		('void', ['float src_x', 'float src_y', 'float src_w', 'float src_h', 'float dst_x', 'float dst_y', 'float dst_w', 'float dst_h', 'const std::string &image_path'], []),
		('void', ['float src_x', 'float src_y', 'float src_w', 'float src_h', 'float dst_x', 'float dst_y', 'float dst_w', 'float dst_h', 'const std::string &image_path', 'hg::Color tint'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Texture2D', [
		('void', ['float x', 'float y', 'float scale', 'const std::shared_ptr<hg::Texture> &texture'], []),
		('void', ['float x', 'float y', 'float scale', 'const std::shared_ptr<hg::Texture> &texture', 'hg::Color tint'], []),
		('void', ['float x', 'float y', 'float scale', 'const std::shared_ptr<hg::Texture> &texture', 'hg::Color color', 'bool flip_h', 'bool flip_v'], [])
	])

	gen.bind_method(plus_conv, 'LoadTexture', 'std::shared_ptr<hg::Texture>', ['const std::string &path'])
	gen.bind_method(plus_conv, 'LoadMaterial', 'std::shared_ptr<hg::RenderMaterial>', ['const std::string &path', '?const std::string &source'])
	gen.bind_method(plus_conv, 'LoadSurfaceShader', 'std::shared_ptr<hg::SurfaceShader>', ['const std::string &path', '?const std::string &source'])
	gen.bind_method(plus_conv, 'LoadGeometry', 'std::shared_ptr<hg::RenderGeometry>', ['const std::string &path'])
	gen.bind_method(plus_conv, 'CreateGeometry', 'std::shared_ptr<hg::RenderGeometry>', ['const std::shared_ptr<hg::Geometry> &geometry', '?bool use_cache'], [])

	gen.bind_method_overloads(plus_conv, 'Geometry2D', [
		('void', ['float x', 'float y', 'const std::shared_ptr<hg::RenderGeometry> &geometry'], []),
		('void', ['float x', 'float y', 'const std::shared_ptr<hg::RenderGeometry> &geometry', 'float angle_x', 'float angle_y', 'float angle_z'], []),
		('void', ['float x', 'float y', 'const std::shared_ptr<hg::RenderGeometry> &geometry', 'float angle_x', 'float angle_y', 'float angle_z', 'float scale'], [])
	])
	gen.bind_method_overloads(plus_conv, 'Geometry3D', [
		('void', ['float x', 'float y', 'float z', 'const std::shared_ptr<hg::RenderGeometry> &geometry'], []),
		('void', ['float x', 'float y', 'float z',  'const std::shared_ptr<hg::RenderGeometry> &geometry', 'float angle_x', 'float angle_y', 'float angle_z'], []),
		('void', ['float x', 'float y', 'float z',  'const std::shared_ptr<hg::RenderGeometry> &geometry', 'float angle_x', 'float angle_y', 'float angle_z', 'float scale'], [])
	])

	gen.bind_method_overloads(plus_conv, 'SetCamera3D', [
		('void', ['float x', 'float y', 'float z'], []),
		('void', ['float x', 'float y', 'float z', 'float angle_x', 'float angle_y', 'float angle_z'], []),
		('void', ['float x', 'float y', 'float z', 'float angle_x', 'float angle_y', 'float angle_z', 'float fov'], []),
		('void', ['float x', 'float y', 'float z', 'float angle_x', 'float angle_y', 'float angle_z', 'float fov', 'float z_near', 'float z_far'], []),
		('void', ['const hg::Matrix4 &view', 'const hg::Matrix44 &projection'], [])
	])
	gen.bind_method(plus_conv, 'GetCamera3DMatrix', 'hg::Matrix4', [])
	gen.bind_method(plus_conv, 'GetCamera3DProjectionMatrix', 'hg::Matrix44', [])

	gen.bind_method_overloads(plus_conv, 'CreateCapsule', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x', 'int subdiv_y', '?const std::string &material_path', '?const std::string &name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreateCone', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', 'int subdiv_x', '?const std::string &material_path', '?const std::string &name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreateCube', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float height', 'float length', '?const std::string &material_path', '?const std::string &name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreateCylinder', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'float height', '?int subdiv_x', '?const std::string &material_path', '?const std::string &name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreatePlane', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float width', 'float length', '?int subdiv', '?const std::string &material_path', '?const std::string &name'], [])
	])
	gen.bind_method_overloads(plus_conv, 'CreateSphere', [
		('std::shared_ptr<hg::Geometry>', [], []),
		('std::shared_ptr<hg::Geometry>', ['float radius'], []),
		('std::shared_ptr<hg::Geometry>', ['float radius', 'int subdiv_x', 'int subdiv_y', '?const std::string &material_path', '?const std::string &name'], [])
	])
	#std::shared_ptr<Geometry> CreateGeometryFromHeightmap(uint32_t width, uint32_t height, const std::vector<float> &heightmap, float scale = 1, const char *_material_path = nullptr, const char *_name = nullptr);

	gen.bind_method(plus_conv, 'NewScene', 'std::shared_ptr<hg::Scene>', ['?bool use_physics', '?bool use_lua'], [])
	gen.bind_method(plus_conv, 'LoadScene', 'bool', ['hg::Scene &scene', 'const std::string &path'], [])
	gen.bind_method(plus_conv, 'UpdateScene', 'void', ['hg::Scene &scene', '?hg::time_ns dt'], [])
	gen.bind_method(plus_conv, 'AddDummy', 'std::shared_ptr<hg::Node>', ['hg::Scene &scene', '?hg::Matrix4 world'], [])
	gen.bind_method(plus_conv, 'AddCamera', 'std::shared_ptr<hg::Node>', ['hg::Scene &scene', '?hg::Matrix4 matrix', '?bool orthographic', '?bool set_as_current'], [])
	gen.bind_method(plus_conv, 'AddLight', 'std::shared_ptr<hg::Node>', ['hg::Scene &scene', '?hg::Matrix4 matrix', '?hg::Light::Model model', '?float range', '?bool shadow', '?hg::Color diffuse', '?hg::Color specular'], [])
	gen.bind_method(plus_conv, 'AddObject', 'std::shared_ptr<hg::Node>', ['hg::Scene &scene', 'std::shared_ptr<hg::RenderGeometry> geometry', '?hg::Matrix4 matrix', '?bool is_static'], [])
	gen.bind_method(plus_conv, 'AddGeometry', 'std::shared_ptr<hg::Node>', ['hg::Scene &scene', 'const std::string &geometry_path', '?hg::Matrix4 matrix'], [])
	gen.bind_method_overloads(plus_conv, 'AddPlane', [
		('std::shared_ptr<hg::Node>', ['hg::Scene &scene', '?hg::Matrix4 matrix'], []),
		('std::shared_ptr<hg::Node>', ['hg::Scene &scene', 'hg::Matrix4 matrix', 'float size_x', 'float size_z', '?const std::string &material_path', '?bool use_geometry_cache'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddCube', [
		('std::shared_ptr<hg::Node>', ['hg::Scene &scene', '?hg::Matrix4 matrix'], []),
		('std::shared_ptr<hg::Node>', ['hg::Scene &scene', 'hg::Matrix4 matrix', 'float size_x', 'float size_y', 'float size_z', '?const std::string &material_path', '?bool use_geometry_cache'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddSphere', [
		('std::shared_ptr<hg::Node>', ['hg::Scene &scene', '?hg::Matrix4 matrix', '?float radius'], []),
		('std::shared_ptr<hg::Node>', ['hg::Scene &scene', 'hg::Matrix4 matrix', 'float radius', 'int subdiv_x', 'int subdiv_y', '?const std::string &material_path', '?bool use_geometry_cache'], [])
	])

	gen.bind_method_overloads(plus_conv, 'AddEnvironment', [
		('std::shared_ptr<hg::Environment>', ['hg::Scene &scene'], []),
		('std::shared_ptr<hg::Environment>', ['hg::Scene &scene', 'hg::Color background_color', 'hg::Color ambient_color'], []),
		('std::shared_ptr<hg::Environment>', ['hg::Scene &scene', 'hg::Color background_color', 'hg::Color ambient_color', 'hg::Color fog_color', 'float fog_near', 'float fog_far'], [])
	])

	gen.bind_method_overloads(plus_conv, 'AddPhysicCube', [
		('std::shared_ptr<hg::Node>', ['std::shared_ptr<hg::RigidBody> &rigid_body', 'hg::Scene &scene'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<hg::Node>', ['std::shared_ptr<hg::RigidBody> &rigid_body', 'hg::Scene &scene', 'hg::Matrix4 m'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<hg::Node>', ['std::shared_ptr<hg::RigidBody> &rigid_body', 'hg::Scene &scene', 'hg::Matrix4 m', 'float width', 'float height', 'float depth', '?float mass', '?const std::string &material_path'], {'arg_out': ['rigid_body']})
	])
	gen.bind_method_overloads(plus_conv, 'AddPhysicPlane', [
		('std::shared_ptr<hg::Node>', ['std::shared_ptr<hg::RigidBody> &rigid_body', 'hg::Scene &scene'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<hg::Node>', ['std::shared_ptr<hg::RigidBody> &rigid_body', 'hg::Scene &scene', 'hg::Matrix4 m'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<hg::Node>', ['std::shared_ptr<hg::RigidBody> &rigid_body', 'hg::Scene &scene', 'hg::Matrix4 m', 'float width', 'float length', '?float mass', '?const std::string &material_path'], {'arg_out': ['rigid_body']})
	])
	gen.bind_method_overloads(plus_conv, 'AddPhysicSphere', [
		('std::shared_ptr<hg::Node>', ['std::shared_ptr<hg::RigidBody> &rigid_body', 'hg::Scene &scene'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<hg::Node>', ['std::shared_ptr<hg::RigidBody> &rigid_body', 'hg::Scene &scene', 'hg::Matrix4 m'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<hg::Node>', ['std::shared_ptr<hg::RigidBody> &rigid_body', 'hg::Scene &scene', 'hg::Matrix4 m', 'float radius', 'int subdiv_x', 'int subdiv_y', '?float mass', '?const std::string &material_path'], {'arg_out': ['rigid_body']})
	])

	#
	gen.bind_method(plus_conv, 'GetMouse', 'std::shared_ptr<hg::InputDevice>', [])
	gen.bind_method(plus_conv, 'GetKeyboard', 'std::shared_ptr<hg::InputDevice>', [])

	gen.bind_method(plus_conv, 'GetMousePos', 'void', ['float &x', 'float &y'], {'arg_out': ['x', 'y']})
	gen.bind_method(plus_conv, 'GetMouseDt', 'void', ['float &x', 'float &y'], {'arg_out': ['x', 'y']})

	gen.bind_method_overloads(plus_conv, 'MouseButtonDown', [
		('bool', [], []),
		('bool', ['hg::Button button'], [])
	])
	gen.bind_method(plus_conv, 'KeyDown', 'bool', ['hg::Key key'])
	gen.bind_method(plus_conv, 'KeyPress', 'bool', ['hg::Key key'])
	gen.bind_method(plus_conv, 'KeyReleased', 'bool', ['hg::Key key'])

	#
	gen.bind_method(plus_conv, 'ResetClock', 'void', [])
	gen.bind_method(plus_conv, 'UpdateClock', 'hg::time_ns', [])

	gen.bind_method(plus_conv, 'GetClockDt', 'hg::time_ns', [])
	gen.bind_method(plus_conv, 'GetClock', 'hg::time_ns', [])

	gen.end_class(plus_conv)

	gen.insert_binding_code('static hg::Plus &GetPlus() { return hg::g_plus.get(); }')
	gen.bind_function('GetPlus', 'hg::Plus &', [])

	# hg::FPSController
	fps_controller = gen.begin_class('hg::FPSController')

	gen.bind_constructor_overloads(fps_controller, [
		([], []),
		(['float x', 'float y', 'float z'], []),
		(['float x', 'float y', 'float z', 'float speed', 'float turbo'], [])
	])

	gen.bind_method(fps_controller, 'Reset', 'void', ['hg::Vector3 position', 'hg::Vector3 rotation'])

	gen.bind_method(fps_controller, 'SetSmoothFactor', 'void', ['float k_pos', 'float k_rot'])

	gen.bind_method(fps_controller, 'ApplyToNode', 'void', ['hg::Node &node'])

	gen.bind_method(fps_controller, 'Update', 'void', ['hg::time_ns dt'])
	gen.bind_method(fps_controller, 'UpdateAndApplyToNode', 'void', ['hg::Node &node', 'hg::time_ns dt'])

	gen.bind_method(fps_controller, 'GetPos', 'hg::Vector3', [])
	gen.bind_method(fps_controller, 'GetRot', 'hg::Vector3', [])
	gen.bind_method(fps_controller, 'SetPos', 'void', ['const hg::Vector3 &position'])
	gen.bind_method(fps_controller, 'SetRot', 'void', ['const hg::Vector3 &rotation'])

	gen.bind_method(fps_controller, 'GetSpeed', 'float', [])
	gen.bind_method(fps_controller, 'SetSpeed', 'void', ['float speed'])
	gen.bind_method(fps_controller, 'GetTurbo', 'float', [])
	gen.bind_method(fps_controller, 'SetTurbo', 'void', ['float turbo'])

	gen.end_class(fps_controller)


def bind_filesystem(gen):
	gen.add_include('foundation/filesystem.h')
	gen.add_include('foundation/std_file_driver.h')
	gen.add_include('foundation/file_handle.h')
	gen.add_include('foundation/file_mode.h')

	gen.bind_named_enum('hg::SeekRef', ['SeekStart', 'SeekCurrent', 'SeekEnd'])
	gen.bind_named_enum('hg::FileMode', ['FileRead', 'FileWrite'])
	gen.bind_named_enum('hg::FileDriverCaps', ['FileDriverIsCaseSensitive', 'FileDriverCanRead', 'FileDriverCanWrite', 'FileDriverCanSeek', 'FileDriverCanDelete', 'FileDriverCanMkDir'])

	# forward declarations
	file_driver = gen.begin_class('hg::FileDriver', bound_name='FileDriver_nobind', noncopyable=True, nobind=True)
	gen.end_class(file_driver)

	file_handle = gen.begin_class('hg::FileHandle', bound_name='FileHandle_nobind', noncopyable=True, nobind=True)
	gen.end_class(file_handle)

	shared_file_driver = gen.begin_class('std::shared_ptr<hg::FileDriver>', bound_name='FileDriver', features={'proxy': lib.stl.SharedPtrProxyFeature(file_driver)})

	# binding specific API
	gen.insert_binding_code('''static bool MountFileDriver(std::shared_ptr<hg::FileDriver> driver) {
	return hg::g_fs.get().Mount(driver);
}
static bool MountFileDriver(std::shared_ptr<hg::FileDriver> driver, const std::string &prefix) {
	return hg::g_fs.get().Mount(driver, prefix);
}
	''', 'Filesystem custom API')

	# hg::FileHandle
	shared_file_handle = gen.begin_class('std::shared_ptr<hg::FileHandle>', bound_name='FileHandle', features={'proxy': lib.stl.SharedPtrProxyFeature(file_handle)})

	gen.bind_method(shared_file_handle, 'GetSize', 'size_t', [], ['proxy'])

	gen.bind_method(shared_file_handle, 'Rewind', 'size_t', [], ['proxy'])
	gen.bind_method(shared_file_handle, 'IsEOF', 'bool', [], ['proxy'])

	gen.bind_method(shared_file_handle, 'Tell', 'size_t', [], ['proxy'])
	gen.bind_method(shared_file_handle, 'Seek', 'size_t', ['int offset', 'hg::SeekRef ref'], ['proxy'])

	gen.insert_binding_code('static size_t FileHandle_WriteBinaryData(hg::FileHandle *handle, hg::BinaryData &data) { return handle->Write(data.GetData(), data.GetDataSize()); }')
	gen.bind_method(shared_file_handle, 'Write', 'size_t', ['hg::BinaryData &data'], {'route': lambda args: 'FileHandle_WriteBinaryData(%s);' % (', '.join(args)), 'proxy': None})

	gen.bind_method(shared_file_handle, 'GetDriver', 'std::shared_ptr<hg::FileDriver>', [], ['proxy'])

	gen.end_class(shared_file_handle)

	# hg::FileDriver
	gen.bind_method(shared_file_driver, 'FileHash', 'std::string', ['const std::string &path'], ['proxy'])

	gen.bind_method(shared_file_driver, 'MapToAbsolute', 'std::string', ['std::string path'], ['proxy'])
	gen.bind_method(shared_file_driver, 'MapToRelative', 'std::string', ['std::string path'], ['proxy'])

	gen.bind_method(shared_file_driver, 'GetCaps', 'hg::FileDriverCaps', [], ['proxy'])

	gen.bind_method(shared_file_driver, 'Open', 'std::shared_ptr<hg::FileHandle>', ['const std::string &path', 'hg::FileMode mode'], ['proxy'])
	gen.bind_method(shared_file_driver, 'Close', 'void', ['hg::FileHandle &handle'], ['proxy'])

	gen.bind_method(shared_file_driver, 'Delete', 'bool', ['const std::string &path'], ['proxy'])

	gen.bind_method(shared_file_driver, 'Tell', 'size_t', ['hg::FileHandle &handle'], ['proxy'])
	gen.bind_method(shared_file_driver, 'Seek', 'size_t', ['hg::FileHandle &handle', 'int offset', 'hg::SeekRef ref'], ['proxy'])
	gen.bind_method(shared_file_driver, 'Size', 'size_t', ['hg::FileHandle &handle'], ['proxy'])

	gen.bind_method(shared_file_driver, 'IsEOF', 'bool', ['hg::FileHandle &handle'], ['proxy'])

	#virtual size_t Read(Handle &h, void *buffer_out, size_t size) = 0;
	#virtual size_t Write(Handle &h, const void *buffer_in, size_t size) = 0;

	#virtual std::vector<DirEntry> Dir(const std::string &path, const std::string &wildcard = "*.*", DirEntry::Type filter = DirEntry::All);

	gen.bind_method(shared_file_driver, 'MkDir', 'bool', ['const std::string &path'], ['proxy'])
	gen.bind_method(shared_file_driver, 'IsDir', 'bool', ['const std::string &path'], ['proxy'])

	gen.end_class(shared_file_driver)

	# hg::StdFileDriver
	std_file_driver = gen.begin_class('hg::StdFileDriver', bound_name='StdFileDriver_nobind', nobind=True)
	gen.end_class(std_file_driver)

	shared_std_file_driver = gen.begin_class('std::shared_ptr<hg::StdFileDriver>', bound_name='StdFileDriver', features={'proxy': lib.stl.SharedPtrProxyFeature(std_file_driver)})
	gen.add_base(shared_std_file_driver, shared_file_driver)

	gen.bind_constructor_overloads(shared_std_file_driver, [
		([], ['proxy']),
		(['const std::string &root_path'], ['proxy']),
		(['const std::string &root_path', 'bool sandbox'], ['proxy'])
	])
	gen.bind_method_overloads(shared_std_file_driver, 'SetRootPath', [
		('void', ['const std::string &path'], ['proxy']),
		('void', ['const std::string &path', 'bool sandbox'], ['proxy'])
	])

	gen.end_class(shared_std_file_driver)

	gen.bind_function_overloads('MountFileDriver', [
		('bool', ['std::shared_ptr<hg::FileDriver> driver'], []),
		('bool', ['std::shared_ptr<hg::FileDriver> driver', 'const std::string &prefix'], [])
	])

	# hg::ZipFileDriver
	gen.add_include('engine/zip_file_driver.h')

	zip_file_driver = gen.begin_class('hg::ZipFileDriver', bound_name='ZipFileDriver_nobind', noncopyable=True, nobind=True)
	gen.end_class(zip_file_driver)

	shared_zip_file_driver = gen.begin_class('std::shared_ptr<hg::ZipFileDriver>', bound_name='ZipFileDriver', features={'proxy': lib.stl.SharedPtrProxyFeature(zip_file_driver)})
	gen.add_base(shared_zip_file_driver, shared_file_driver)

	gen.bind_constructor_overloads(shared_zip_file_driver, [
		(['std::shared_ptr<hg::FileHandle> archive'], ['proxy']),
		(['std::shared_ptr<hg::FileHandle> archive', 'const std::string &password'], ['proxy'])
	])
	gen.bind_method_overloads(shared_zip_file_driver, 'SetArchive', [
		('bool', ['std::shared_ptr<hg::FileHandle> archive'], ['proxy']),
		('bool', ['std::shared_ptr<hg::FileHandle> archive', 'const std::string &password'], ['proxy'])
	])

	gen.end_class(shared_zip_file_driver)

	# hg::BufferFileDriver
	gen.add_include('foundation/buffer_file_driver.h')

	buffer_file_driver = gen.begin_class('hg::BufferFileDriver', bound_name='BufferFileDriver_nobind', noncopyable=True, nobind=True)
	gen.end_class(buffer_file_driver)

	shared_buffer_file_driver = gen.begin_class('std::shared_ptr<hg::BufferFileDriver>', bound_name='BufferFileDriver', features={'proxy': lib.stl.SharedPtrProxyFeature(buffer_file_driver)})
	gen.add_base(shared_buffer_file_driver, shared_file_driver)

	gen.bind_constructor_overloads(shared_buffer_file_driver, [
		(['std::shared_ptr<hg::FileDriver> driver'], ['proxy']),
		(['std::shared_ptr<hg::FileDriver> driver', 'size_t read_buffer_size', 'size_t write_buffer_size'], ['proxy'])
	])
	gen.end_class(shared_buffer_file_driver)

	# hg::Filesystem
	fs = gen.begin_class('hg::Filesystem')

	gen.bind_method_overloads(fs, 'Mount', [
		('bool', ['std::shared_ptr<hg::FileDriver> driver'], []),
		('bool', ['std::shared_ptr<hg::FileDriver> driver', 'const std::string &prefix'], [])
	])
	gen.bind_method(fs, 'IsPrefixMounted', 'bool', ['const std::string &prefix'])

	gen.bind_method_overloads(fs, 'Unmount', [
		('void', ['const std::string &prefix'], []),
		('void', ['const std::shared_ptr<hg::FileDriver> &driver'], [])
	])
	gen.bind_method(fs, 'UnmountAll', 'void', [])

	gen.bind_method(fs, 'MapToAbsolute', 'std::string', ['const std::string &path'])
	gen.bind_method(fs, 'MapToRelative', 'std::string', ['const std::string &path'])
	gen.bind_method(fs, 'StripPrefix', 'std::string', ['const std::string &path'])

	gen.bind_method(fs, 'Open', 'std::shared_ptr<hg::FileHandle>', ['const std::string &path', 'hg::FileMode mode'])
	gen.bind_method(fs, 'Close', 'void', ['hg::FileHandle &handle'])

	gen.bind_method(fs, 'MkDir', 'bool', ['const std::string &path'])

	gen.bind_method(fs, 'Exists', 'bool', ['const std::string &path'])
	gen.bind_method(fs, 'Delete', 'bool', ['const std::string &path'])

	gen.insert_binding_code('''\
static bool _FileSystem_FileLoad(hg::Filesystem *m, const std::string &path, hg::BinaryData &out) {
	auto h{m->Open(path)};
	if (!h)
		return false;
	auto size = h->GetSize();
	out.Reset();
	out.Grow(size);
	size_t nread = h->Read(out.GetData(), size);
	out.Commit(nread);
	return (nread == size);
}
static bool _FileSystem_FileSave(hg::Filesystem *m, const std::string &path, const hg::BinaryData &in) {
	return m->FileSave(path, in.GetData(), in.GetDataSize());
}
''')

	gen.bind_method_overloads(fs, 'FileLoad', expand_std_vector_proto(gen, [
		('bool', ['const std::string &path', 'std::vector<char> &out'], []),
		('bool', ['const std::string &path', 'hg::BinaryData &out'], {'route': route_lambda('_FileSystem_FileLoad')})
	]))

	gen.bind_method_overloads(fs, 'FileSave', expand_std_vector_proto(gen, [
		('bool', ['const std::string &path', 'const std::vector<char> &in'], []),
		('bool', ['const std::string &path', 'const hg::BinaryData &in'], {'route': route_lambda('_FileSystem_FileSave')})
	]))

	gen.bind_method(fs, 'FileSize', 'size_t', ['const std::string &path'])
	gen.bind_method(fs, 'FileCopy', 'bool', ['const std::string &src', 'const std::string &dst'])
	gen.bind_method(fs, 'FileMove', 'bool', ['const std::string &src', 'const std::string &dst'])

	gen.bind_method(fs, 'FileToString', 'std::string', ['const std::string &path'])
	gen.bind_method(fs, 'StringToFile', 'bool', ['const std::string &path', 'const std::string &text'])

	gen.end_class(fs)

	#
	gen.insert_binding_code('static hg::Filesystem &GetFilesystem() { return hg::g_fs.get(); }')
	gen.bind_function('GetFilesystem', 'hg::Filesystem &', [])


def bind_color(gen):
	gen.add_include('foundation/color.h')
	gen.add_include('foundation/color_api.h')

	color = gen.begin_class('hg::Color')
	color._inline = True  # use inline alloc where possible

	gen.bind_static_members(color, ['const hg::Color Zero', 'const hg::Color One', 'const hg::Color White', 'const hg::Color Grey', 'const hg::Color Black', 'const hg::Color Red', 'const hg::Color Green', 'const hg::Color Blue', 'const hg::Color Yellow', 'const hg::Color Orange', 'const hg::Color Purple', 'const hg::Color Transparent'])
	gen.bind_members(color, ['float r', 'float g', 'float b', 'float a'])

	gen.bind_constructor_overloads(color, [
		([], []),
		(['const hg::Color &color'], []),
		(['float r', 'float g', 'float b'], []),
		(['float r', 'float g', 'float b', 'float a'], [])
	])

	gen.bind_arithmetic_ops_overloads(color, ['+', '-', '/', '*'], [('hg::Color', ['const hg::Color &color'], []), ('hg::Color', ['float k'], [])])
	gen.bind_inplace_arithmetic_ops_overloads(color, ['+=', '-=', '*=', '/='], [
		(['hg::Color &color'], []),
		(['float k'], [])
	])
	gen.bind_comparison_ops(color, ['==', '!='], ['const hg::Color &color'])

	gen.end_class(color)

	gen.bind_function('hg::ColorToGrayscale', 'float', ['const hg::Color &color'])

	gen.bind_function('hg::ColorToRGBA32', 'uint32_t', ['const hg::Color &color'])
	gen.bind_function('hg::ColorFromRGBA32', 'hg::Color', ['uint32_t rgba32'])

	gen.bind_function('hg::ARGB32ToRGBA32', 'uint32_t', ['uint32_t argb'])

	#inline float Dist2(const Color &i, const Color &j) { return (j.r - i.r) * (j.r - i.r) + (j.g - i.g) * (j.g - i.g) + (j.b - i.b) * (j.b - i.b) + (j.a - i.a) * (j.a - i.a); }
	#inline float Dist(const Color &i, const Color &j) { return Sqrt(Dist2(i, j)); }

	#inline bool AlmostEqual(const Color &a, const Color &b, float epsilon)

	gen.bind_function('hg::ChromaScale', 'hg::Color', ['const hg::Color &color', 'float k'])
	gen.bind_function('hg::AlphaScale', 'hg::Color', ['const hg::Color &color', 'float k'])

	#Color Clamp(const Color &c, float min, float max);
	#Color Clamp(const Color &c, const Color &min, const Color &max);
	#Color ClampMagnitude(const Color &c, float min, float max);

	gen.bind_function('hg::ColorFromVector3', 'hg::Color', ['const hg::Vector3 &v'])
	gen.bind_function('hg::ColorFromVector4', 'hg::Color', ['const hg::Vector4 &v'])

	bind_std_vector(gen, color)


def bind_font_engine(gen):
	gen.add_include('engine/font_engine.h')

	font_engine = gen.begin_class('hg::FontEngine', noncopyable=True)

	gen.bind_constructor(font_engine, [])

	gen.bind_method(font_engine, 'SetFont', 'bool', ['const char *path', '?bool autohint'])
	gen.bind_method(font_engine, 'SetSize', 'void', ['float size'])
	
	gen.insert_binding_code('static hg::Rect<int> _GetGlyphInfo(hg::FontEngine *engine, char32_t codepoint, hg::tVector2<float> &advance) { hg::GlyphInfo nfo = engine->GetGlyphInfo(codepoint); advance = nfo.advance; return nfo.rect; }')
	gen.bind_method(font_engine, 'GetGlyphInfo', 'hg::Rect<int>', ['char32_t codepoint', 'hg::tVector2<float> &advance'], {'route': route_lambda('_GetGlyphInfo'), 'arg_out': ['advance']})
	
	gen.bind_method_overloads(font_engine, 'GetTextRect', [
		('hg::Rect<float>', ['const char *utf8', 'float x', 'float y'], []),
		('hg::Rect<float>', ['const char32_t *codepoints', 'uint32_t count', 'float x', 'float y'], [])
	])
	
	gen.bind_method(font_engine, 'GetKerning', 'bool', ['char32_t first_codepoint', 'char32_t second_codepoint', 'float &kerning_x', 'float &kerning_y'], {'arg_out': ['kerning_x', 'kerning_y']})

	gen.end_class(font_engine)


def bind_picture(gen):
	gen.add_include('engine/picture.h')

	gen.bind_named_enum('hg::PictureFormat', ['PictureGray8', 'PictureGray16', 'PictureGrayF', 'PictureRGB555', 'PictureRGB565', 'PictureRGB8', 'PictureBGR8', 'PictureRGBA8', 'PictureBGRA8', 'PictureARGB8', 'PictureABGR8', 'PictureRGB16', 'PictureBGR16', 'PictureRGBA16', 'PictureBGRA16', 'PictureARGB16', 'PictureABGR16', 'PictureRGBF', 'PictureBGRF', 'PictureRGBAF', 'PictureBGRAF', 'PictureARGBF', 'PictureABGRF', 'PictureInvalidFormat'])

	gen.bind_named_enum('hg::BrushMode', ['BrushNone', 'BrushSolid'])
	gen.bind_named_enum('hg::PenMode', ['PenNone', 'PenSolid'])
	gen.bind_named_enum('hg::PenCap', ['ButtCap', 'SquareCap', 'RoundCap'])
	gen.bind_named_enum('hg::LineJoin', ['MiterJoin', 'MiterJoinRevert', 'RoundJoin', 'BevelJoin', 'MiterJoinRound'])
	gen.bind_named_enum('hg::InnerJoin', ['InnerBevel', 'InnerMiter', 'InnerJag', 'InnerRound'])

	gen.bind_named_enum('hg::PictureFilter', ['FilterNearest', 'FilterBilinear', 'FilterHanning', 'FilterHamming', 'FilterHermite', 'FilterQuadric', 'FilterBicubic', 'FilterKaiser', 'FilterCatrom', 'FilterMitchell', 'FilterSpline16', 'FilterSpline36', 'FilterGaussian', 'FilterBessel', 'FilterSinc36', 'FilterSinc64', 'FilterSinc256', 'FilterLanczos36', 'FilterLanczos64', 'FilterLanczos256', 'FilterBlackman36', 'FilterBlackman64', 'FilterBlackman256'])

	# hg::Picture
	picture = gen.begin_class('hg::Picture', bound_name='Picture_nobind', nobind=True)
	gen.end_class(picture)

	shared_picture = gen.begin_class('std::shared_ptr<hg::Picture>', bound_name='Picture', features={'proxy': lib.stl.SharedPtrProxyFeature(picture)})

	gen.bind_constructor_overloads(shared_picture, [
		([], ['proxy']),
		(['const hg::Picture &picture'], ['proxy']),
		(['uint32_t width', 'uint32_t height', 'hg::PictureFormat format'], ['proxy'])
	])

	gen.bind_method(shared_picture, 'GetWidth', 'uint32_t', [], ['proxy'])
	gen.bind_method(shared_picture, 'GetHeight', 'uint32_t', [], ['proxy'])
	gen.bind_method(shared_picture, 'GetCenter', 'hg::tVector2<float>', [], ['proxy'])
	gen.bind_method(shared_picture, 'GetStride', 'size_t', [], ['proxy'])
	gen.bind_method(shared_picture, 'GetFormat', 'hg::PictureFormat', [], ['proxy'])

	gen.bind_method(shared_picture, 'GetRect', 'hg::Rect<int>', [], ['proxy'])

	gen.bind_method_overloads(shared_picture, 'AllocAs', [
		('bool', ['uint32_t width', 'uint32_t height', 'hg::PictureFormat format'], ['proxy']),
		('bool', ['const hg::Picture &picture'], ['proxy'])
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
	gen.bind_method(shared_picture, 'GetPixelRGBA', 'hg::Vector4', ['int x', 'int y'], ['proxy'])
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

	gen.bind_method(shared_picture, 'BlitCopy', 'bool', ['const hg::Picture &src', 'hg::Rect<int> src_rect', 'hg::tVector2<int> dst_pos'], ['proxy'])
	gen.bind_method_overloads(shared_picture, 'Blit', [
		('bool', ['const hg::Picture &src', 'hg::Rect<int> src_rect', 'hg::tVector2<int> dst_pos'], ['proxy']),
		('bool', ['const hg::Picture &src', 'hg::Rect<int> src_rect', 'hg::Rect<int> dst_rect'], ['proxy']),
		('bool', ['const hg::Picture &src', 'hg::Rect<int> src_rect', 'hg::Rect<int> dst_rect', 'hg::PictureFilter filter'], ['proxy'])
	])
	gen.bind_method_overloads(shared_picture, 'BlitTransform', [
		('bool', ['const hg::Picture &src', 'hg::Rect<int> dst_rect', 'const hg::Matrix3 &m'], ['proxy']),
		('bool', ['const hg::Picture &src', 'hg::Rect<int> dst_rect', 'const hg::Matrix3 &m', 'hg::PictureFilter filter'], ['proxy'])
	])

	gen.bind_method(shared_picture, 'Flip', 'void', ['bool horizontal', 'bool vertical'], ['proxy'])
	gen.bind_method(shared_picture, 'Reframe', 'bool', ['int32_t top', 'int32_t bottom', 'int32_t left', 'int32_t right'], ['proxy'])
	gen.bind_method(shared_picture, 'Crop', 'bool', ['int32_t start_x', 'int32_t start_y', 'int32_t end_x', 'int32_t end_y'], ['proxy'])

	gen.bind_method_overloads(shared_picture, 'Resize', [
		('bool', ['uint32_t width', 'uint32_t height'], ['proxy']),
		('bool', ['uint32_t width', 'uint32_t height', 'hg::PictureFilter filter'], ['proxy'])
	])

	gen.bind_method(shared_picture, 'Convert', 'bool', ['hg::PictureFormat format'], ['proxy'])

	gen.bind_method(shared_picture, 'SetFillMode', 'void', ['hg::BrushMode brush_mode'], ['proxy'])
	gen.bind_method(shared_picture, 'SetPenMode', 'void', ['hg::PenMode pen_mode'], ['proxy'])
	gen.bind_method(shared_picture, 'SetPenWidth', 'void', ['float width'], ['proxy'])
	gen.bind_method(shared_picture, 'SetPenCap', 'void', ['hg::PenCap cap'], ['proxy'])
	gen.bind_method(shared_picture, 'SetLineJoin', 'void', ['hg::LineJoin join'], ['proxy'])
	gen.bind_method(shared_picture, 'SetInnerJoin', 'void', ['hg::InnerJoin join'], ['proxy'])

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

	gen.bind_method(shared_picture, 'DrawGlyph', 'void', ['hg::FontEngine &font_engine', 'char32_t glyph_utf32', 'float x', 'float y'], ['proxy'])
	gen.bind_method(shared_picture, 'DrawText', 'void', ['hg::FontEngine &font_engine', 'const std::string &text', 'float x', 'float y'], ['proxy'])

	gen.bind_method_overloads(shared_picture, 'Compare', [
		('bool', ['const hg::Picture &picture'], ['proxy']),
		('bool', ['const hg::Picture &picture', 'float threshold'], ['proxy'])
	])

	gen.end_class(shared_picture)

	#
	gen.add_include('engine/picture_io.h')

	gen.insert_binding_code('''
static bool LoadPicture(std::shared_ptr<hg::Picture> &picture, const char *path) {
	return hg::g_picture_io.get().Load(*picture, path);
}
''')
	gen.bind_function('LoadPicture', 'bool', ['std::shared_ptr<hg::Picture> &picture', 'const char *path'])

	gen.insert_binding_code('''
static bool SavePicture(std::shared_ptr<hg::Picture> &picture, const std::string &path, const std::string &codec_name, const std::string &parm = "") {
	return hg::g_picture_io.get().Save(*picture, path.c_str(), codec_name.c_str(), parm.empty() ? nullptr : parm.c_str());
}
''')
	gen.bind_function('SavePicture', 'bool', ['std::shared_ptr<hg::Picture> &picture', 'const std::string &path', 'const std::string &codec_name', '?const std::string &parm'])


def bind_document(gen):
	gen.add_include('foundation/document.h')
	gen.add_include('foundation/binary_document.h')
	gen.add_include('foundation/xml_document.h')
	gen.add_include('foundation/json_document.h')

	gen.bind_named_enum('hg::DocumentFormat', ['DocumentFormatUnknown', 'DocumentFormatXML', 'DocumentFormatJSON', 'DocumentFormatBinary'])

	doc_reader = gen.begin_class('hg::DocumentReader', bound_name='DocumentReader_nobind', nobind=True, noncopyable=True)
	gen.end_class(doc_reader)

	shared_doc_reader = gen.begin_class('std::shared_ptr<hg::DocumentReader>', bound_name='DocumentReader', features={'proxy': lib.stl.SharedPtrProxyFeature(doc_reader)})
	gen.bind_method(shared_doc_reader, 'GetScopeName', 'std::string', [], ['proxy'])
	gen.bind_method(shared_doc_reader, 'GetChildCount', 'uint32_t', ['?const char *name'], ['proxy'])

	gen.bind_method(shared_doc_reader, 'EnterScope', 'bool', ['const char *name'], ['proxy'])
	gen.bind_method(shared_doc_reader, 'EnterScopeMultiple', 'bool', ['const char *name'], ['proxy'])
	gen.bind_method(shared_doc_reader, 'ExitScopeMultiple', 'bool', ['uint32_t count'], ['proxy'])

	gen.bind_method(shared_doc_reader, 'EnterFirstChild', 'bool', [], ['proxy'])
	gen.bind_method(shared_doc_reader, 'EnterSibling', 'bool', [], ['proxy'])
	gen.bind_method(shared_doc_reader, 'ExitScope', 'bool', [], ['proxy'])

	gen.bind_method(shared_doc_reader, 'Read', 'bool', ['const std::string &name', 'bool &v'], {'proxy': None, 'arg_out': ['v']}, 'ReadBool')
	gen.bind_method(shared_doc_reader, 'Read', 'bool', ['const std::string &name', 'char &v'], {'proxy': None, 'arg_out': ['v']}, 'ReadInt8')
	gen.bind_method(shared_doc_reader, 'Read', 'bool', ['const std::string &name', 'uint8_t &v'], {'proxy': None, 'arg_out': ['v']}, 'ReadUInt8')
	gen.bind_method(shared_doc_reader, 'Read', 'bool', ['const std::string &name', 'short &v'], {'proxy': None, 'arg_out': ['v']}, 'ReadInt16')
	gen.bind_method(shared_doc_reader, 'Read', 'bool', ['const std::string &name', 'uint16_t &v'], {'proxy': None, 'arg_out': ['v']}, 'ReadUInt16')
	gen.bind_method(shared_doc_reader, 'Read', 'bool', ['const std::string &name', 'int32_t &v'], {'proxy': None, 'arg_out': ['v']}, 'ReadInt32')
	gen.bind_method(shared_doc_reader, 'Read', 'bool', ['const std::string &name', 'uint32_t &v'], {'proxy': None, 'arg_out': ['v']}, 'ReadUInt32')
	gen.bind_method(shared_doc_reader, 'Read', 'bool', ['const std::string &name', 'float &v'], {'proxy': None, 'arg_out': ['v']}, 'ReadFloat')
	gen.bind_method(shared_doc_reader, 'Read', 'bool', ['const std::string &name', 'std::string &v'], {'proxy': None, 'arg_out': ['v']}, 'ReadString')

	gen.bind_method(shared_doc_reader, 'HasBinarySupport', 'bool', [], ['proxy'])

	gen.bind_method(shared_doc_reader, 'Load', 'bool', ['const std::string &path'], ['proxy'])
	gen.end_class(shared_doc_reader)

	gen.insert_binding_code('''
static std::shared_ptr<hg::DocumentReader> _CreateBinaryDocumentReader() { return std::shared_ptr<hg::DocumentReader>(new hg::BinaryDocumentReader); }
static std::shared_ptr<hg::DocumentReader> _CreateJSONDocumentReader() { return std::shared_ptr<hg::DocumentReader>(new hg::JSONDocumentReader); }
static std::shared_ptr<hg::DocumentReader> _CreateXMLDocumentReader() { return std::shared_ptr<hg::DocumentReader>(new hg::XMLDocumentReader); }
''')
	gen.bind_function('CreateBinaryDocumentReader', 'std::shared_ptr<hg::DocumentReader>', [], {'route': route_lambda('_CreateBinaryDocumentReader')})
	gen.bind_function('CreateJSONDocumentReader', 'std::shared_ptr<hg::DocumentReader>', [], {'route': route_lambda('_CreateJSONDocumentReader')})
	gen.bind_function('CreateXMLDocumentReader', 'std::shared_ptr<hg::DocumentReader>', [], {'route': route_lambda('_CreateXMLDocumentReader')})

	#
	doc_writer = gen.begin_class('hg::DocumentWriter', bound_name='DocumentWriter_nobind', nobind=True, noncopyable=True)
	gen.end_class(doc_writer)

	shared_doc_writer = gen.begin_class('std::shared_ptr<hg::DocumentWriter>', bound_name='DocumentWriter', features={'proxy': lib.stl.SharedPtrProxyFeature(doc_writer)})

	gen.bind_method(shared_doc_writer, 'EnterScope', 'bool', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_doc_writer, 'EnterScopeMultiple', 'bool', ['const std::string &name'], ['proxy'])
	gen.bind_method(shared_doc_writer, 'ExitScopeMultiple', 'bool', ['uint32_t count'], ['proxy'])
	gen.bind_method(shared_doc_writer, 'ExitScope', 'bool', [], ['proxy'])

	gen.bind_method(shared_doc_writer, 'Write', 'bool', ['const std::string &name', 'bool v'], ['proxy'], 'WriteBool')
	gen.bind_method(shared_doc_writer, 'Write', 'bool', ['const std::string &name', 'char v'], ['proxy'], 'WriteInt8')
	gen.bind_method(shared_doc_writer, 'Write', 'bool', ['const std::string &name', 'uint8_t v'], ['proxy'], 'WriteUInt8')
	gen.bind_method(shared_doc_writer, 'Write', 'bool', ['const std::string &name', 'short v'], ['proxy'], 'WriteInt16')
	gen.bind_method(shared_doc_writer, 'Write', 'bool', ['const std::string &name', 'uint16_t v'], ['proxy'], 'WriteUInt16')
	gen.bind_method(shared_doc_writer, 'Write', 'bool', ['const std::string &name', 'int32_t v'], ['proxy'], 'WriteInt32')
	gen.bind_method(shared_doc_writer, 'Write', 'bool', ['const std::string &name', 'uint32_t v'], ['proxy'], 'WriteUInt32')
	gen.bind_method(shared_doc_writer, 'Write', 'bool', ['const std::string &name', 'float v'], ['proxy'], 'WriteFloat')
	gen.bind_method(shared_doc_writer, 'Write', 'bool', ['const std::string &name', 'const std::string &v'], ['proxy'], 'WriteString')

	gen.bind_method(shared_doc_writer, 'HasBinarySupport', 'bool', [], ['proxy'])

	gen.bind_method(shared_doc_writer, 'Save', 'bool', ['const std::string &path'], ['proxy'])
	gen.end_class(shared_doc_writer)

	gen.insert_binding_code('''
static std::shared_ptr<hg::DocumentWriter> _CreateBinaryDocumentWriter() { return std::shared_ptr<hg::DocumentWriter>(new hg::BinaryDocumentWriter); }
static std::shared_ptr<hg::DocumentWriter> _CreateJSONDocumentWriter() { return std::shared_ptr<hg::DocumentWriter>(new hg::JSONDocumentWriter); }
static std::shared_ptr<hg::DocumentWriter> _CreateXMLDocumentWriter() { return std::shared_ptr<hg::DocumentWriter>(new hg::XMLDocumentWriter); }
''')
	gen.bind_function('CreateBinaryDocumentWriter', 'std::shared_ptr<hg::DocumentWriter>', [], {'route': route_lambda('_CreateBinaryDocumentWriter')})
	gen.bind_function('CreateJSONDocumentWriter', 'std::shared_ptr<hg::DocumentWriter>', [], {'route': route_lambda('_CreateJSONDocumentWriter')})
	gen.bind_function('CreateXMLDocumentWriter', 'std::shared_ptr<hg::DocumentWriter>', [], {'route': route_lambda('_CreateXMLDocumentWriter')})

	#
	gen.bind_function('hg::GetDocumentReadFormat', 'hg::DocumentFormat', ['const std::string &path'])
	gen.bind_function('hg::GetDocumentWriteFormat', 'hg::DocumentFormat', ['const std::string &path'])

	gen.bind_function('hg::GetDocumentFormatFromString', 'hg::DocumentFormat', ['const std::string &document'])


def bind_math(gen):
	gen.begin_class('hg::Vector3')
	gen.begin_class('hg::Vector4')
	gen.begin_class('hg::Matrix3')
	gen.begin_class('hg::Matrix4')
	gen.begin_class('hg::Matrix44')
	gen.begin_class('hg::Quaternion')

	# math
	gen.add_include('foundation/rect.h')
	gen.add_include('foundation/math.h')

	gen.bind_named_enum('hg::RotationOrder', [
		'RotationOrderZYX',
		'RotationOrderYZX',
		'RotationOrderZXY',
		'RotationOrderXZY',
		'RotationOrderYXZ',
		'RotationOrderXYZ',
		'RotationOrderXY',
		'RotationOrder_Default'
		], storage_type='uint8_t')

	gen.bind_named_enum('hg::Axis', ['AxisX', 'AxisY', 'AxisZ', 'AxisRotX', 'AxisRotY', 'AxisRotZ', 'AxisLast'], storage_type='uint8_t')

	gen.bind_function('hg::LinearInterpolate<float>', 'float', ['float y0', 'float y1', 'float t'])
	gen.bind_function('hg::CosineInterpolate<float>', 'float', ['float y0', 'float y1', 'float t'])
	gen.bind_function('hg::CubicInterpolate<float>', 'float', ['float y0', 'float y1', 'float y2', 'float y3', 'float t'])
	gen.bind_function('hg::HermiteInterpolate<float>', 'float', ['float y0', 'float y1', 'float y2', 'float y3', 'float t', 'float tension', 'float bias'])

	gen.bind_function('hg::ReverseRotationOrder', 'hg::RotationOrder', ['hg::RotationOrder rotation_order'])

	# hg::MinMax
	gen.add_include('foundation/minmax.h')

	minmax = gen.begin_class('hg::MinMax')

	gen.bind_members(minmax, ['hg::Vector3 mn', 'hg::Vector3 mx'])
	gen.bind_constructor_overloads(minmax, [
		([], []),
		(['const hg::Vector3 &min', 'const hg::Vector3 &max'], [])
	])
	gen.bind_method(minmax, 'GetArea', 'float', [])
	gen.bind_method(minmax, 'GetCenter', 'hg::Vector3', [])

	gen.bind_arithmetic_op(minmax, '*', 'hg::MinMax', ['const hg::Matrix4 &m'])
	gen.bind_comparison_ops(minmax, ['==', '!='], ['const hg::MinMax &minmax'])

	gen.end_class(minmax)

	#void GetMinMaxVertices(const MinMax &minmax, Vector3 out[8]);
	gen.bind_function('hg::ComputeMinMaxBoundingSphere', 'void', ['const hg::MinMax &minmax', 'hg::Vector3 &origin', 'float &radius'], {'arg_out': ['origin', 'radius']})

	gen.bind_function_overloads('hg::Overlap', [
		('bool', ['const hg::MinMax &minmax_a', 'const hg::MinMax &minmax_b'], []),
		('bool', ['const hg::MinMax &minmax_a', 'const hg::MinMax &minmax_b', 'hg::Axis axis'], [])
	])
	gen.bind_function('hg::Contains', 'bool', ['const hg::MinMax &minmax', 'const hg::Vector3 &position'])

	gen.bind_function_overloads('hg::Union', [
		('hg::MinMax', ['const hg::MinMax &minmax_a', 'const hg::MinMax &minmax_b'], []),
		('hg::MinMax', ['const hg::MinMax &minmax', 'const hg::Vector3 &position'], [])
	])

	gen.bind_function('hg::IntersectRay', 'bool', ['const hg::MinMax &minmax', 'const hg::Vector3 &origin', 'const hg::Vector3 &direction', 'float &t_min', 'float &t_max'], {'arg_out': ['t_min', 't_max']})

	gen.bind_function('hg::ClassifyLine', 'bool', ['const hg::MinMax &minmax', 'const hg::Vector3 &position', 'const hg::Vector3 &direction', 'hg::Vector3 &intersection', 'hg::Vector3 *normal'], {'arg_out': ['intersection', 'normal']})
	gen.bind_function('hg::ClassifySegment', 'bool', ['const hg::MinMax &minmax', 'const hg::Vector3 &p0', 'const hg::Vector3 &p1', 'hg::Vector3 &intersection', 'hg::Vector3 *normal'], {'arg_out': ['intersection', 'normal']})

	gen.bind_function('MinMaxFromPositionSize', 'hg::MinMax', ['const hg::Vector3 &position', 'const hg::Vector3 &size'])

	# hg::Vector2<T>
	gen.add_include('foundation/vector2.h')

	def bind_vector2_T(T, bound_name):
		vector2 = gen.begin_class('hg::tVector2<%s>'%T, bound_name=bound_name)
		gen.bind_static_members(vector2, ['const hg::tVector2<%s> Zero'%T, 'const hg::tVector2<%s> One'%T])

		gen.bind_members(vector2, ['%s x'%T, '%s y'%T])

		gen.bind_constructor_overloads(vector2, [
			([], []),
			(['%s x'%T, '%s y'%T], []),
			(['const hg::tVector2<%s> &v'%T], []),
			(['const hg::Vector3 &v'], []),
			(['const hg::Vector4 &v'], [])
		])

		gen.bind_arithmetic_ops_overloads(vector2, ['+', '-', '/'], [
			('hg::tVector2<%s>'%T, ['const hg::tVector2<%s> &v'%T], []),
			('hg::tVector2<%s>'%T, ['const %s k'%T], [])
		])
		gen.bind_arithmetic_op_overloads(vector2, '*', [
			('hg::tVector2<%s>'%T, ['const hg::tVector2<%s> &v'%T], []),
			('hg::tVector2<%s>'%T, ['const %s k'%T], []),
			('hg::tVector2<%s>'%T, ['const hg::Matrix3 &m'], [])
		])
		gen.bind_inplace_arithmetic_ops_overloads(vector2, ['+=', '-=', '*=', '/='], [
			(['const hg::tVector2<%s> &v'%T], []),
			(['const %s k'%T], [])
		])

		gen.bind_method(vector2, 'Min', 'hg::tVector2<%s>'%T, ['const hg::tVector2<%s> &v'%T])
		gen.bind_method(vector2, 'Max', 'hg::tVector2<%s>'%T, ['const hg::tVector2<%s> &v'%T])

		gen.bind_method(vector2, 'Len2', T, [])
		gen.bind_method(vector2, 'Len', T, [])

		gen.bind_method(vector2, 'Dot', T, ['const hg::tVector2<%s> &v'%T])

		gen.bind_method(vector2, 'Normalize', 'void', [])
		gen.bind_method(vector2, 'Normalized', 'hg::tVector2<%s>'%T, [])

		gen.bind_method(vector2, 'Reversed', 'hg::tVector2<%s>'%T, [])

		gen.bind_static_method(vector2, 'Dist2', T, ['const hg::tVector2<%s> &a'%T, 'const hg::tVector2<%s> &b'%T])
		gen.bind_static_method(vector2, 'Dist', T, ['const hg::tVector2<%s> &a'%T, 'const hg::tVector2<%s> &b'%T])

		gen.insert_binding_code('static void _Vector2_%s_Set(hg::tVector2<%s> *v, %s x, %s y) { v->x = x; v->y = y; }'%(T, T, T, T))
		gen.bind_method(vector2, 'Set', 'void', ['%s x'%T, '%s y'%T], {'route': route_lambda('_Vector2_%s_Set'%T)})

		gen.end_class(vector2)
		return vector2

	vector2 = bind_vector2_T('float', 'Vector2')
	ivector2 = bind_vector2_T('int', 'IntVector2')

	# hg::Vector4
	gen.add_include('foundation/vector4.h')

	vector4 = gen.begin_class('hg::Vector4')
	vector4._inline = True
	gen.bind_members(vector4, ['float x', 'float y', 'float z', 'float w'])

	gen.bind_constructor_overloads(vector4, [
		([], []),
		(['float x', 'float y', 'float z', 'float w'], []),
		(['const hg::tVector2<float> &v'], []),
		(['const hg::tVector2<int> &v'], []),
		(['const hg::Vector3 &v'], []),
		(['const hg::Vector4 &v'], [])
	])

	gen.bind_arithmetic_ops_overloads(vector4, ['+', '-', '/'], [
		('hg::Vector4', ['hg::Vector4 &v'], []),
		('hg::Vector4', ['float k'], [])
	])
	gen.bind_arithmetic_ops_overloads(vector4, ['*'], [
		('hg::Vector4', ['hg::Vector4 &v'], []),
		('hg::Vector4', ['float k'], []),
		('hg::Vector4', ['const hg::Matrix4 &m'], []),
		('hg::Vector4', ['const hg::Matrix44 &m'], [])
	])

	gen.bind_inplace_arithmetic_ops_overloads(vector4, ['+=', '-=', '*=', '/='], [
		(['hg::Vector4 &v'], []),
		(['float k'], [])
	])

	gen.bind_method(vector4, 'Abs', 'hg::Vector4', [])

	gen.bind_method(vector4, 'Normalized', 'hg::Vector4', [])

	gen.insert_binding_code('static void _Vector4_Set(hg::Vector4 *v, float x, float y, float z, float w = 1.f) { v->x = x; v->y = y; v->z = z; v->w = w; }')
	gen.bind_method(vector4, 'Set', 'void', ['float x', 'float y', 'float z', '?float w'], {'route': route_lambda('_Vector4_Set')})

	gen.end_class(vector4)

	# hg::Quaternion
	gen.add_include('foundation/quaternion.h')

	quaternion = gen.begin_class('hg::Quaternion')

	gen.bind_members(quaternion, ['float x', 'float y', 'float z', 'float w'])

	gen.bind_constructor_overloads(quaternion, [
		([], []),
		(['float x', 'float y', 'float z', 'float w'], []),
		(['const hg::Quaternion &q'], [])
	])

	#gen.bind_comparison_ops(quaternion, ['==', '!='], ['const hg::Quaternion &q'])
	gen.bind_arithmetic_ops_overloads(quaternion, ['+', '-', '*'], [
		('hg::Quaternion', ['float v'], []),
		('hg::Quaternion', ['hg::Quaternion &q'], [])
	])
	gen.bind_arithmetic_op(quaternion, '/', 'hg::Quaternion', ['float v'])
	gen.bind_inplace_arithmetic_ops_overloads(quaternion, ['+=', '-=', '*='], [
		(['float v'], []),
		(['const hg::Quaternion &q'], [])
	])
	gen.bind_inplace_arithmetic_op(quaternion, '/=', ['float v'])

	gen.bind_method(quaternion, 'Inversed', 'hg::Quaternion', [])
	gen.bind_method(quaternion, 'Normalized', 'hg::Quaternion', [])
	gen.bind_method(quaternion, 'ToMatrix3', 'hg::Matrix3', [])
	gen.bind_method(quaternion, 'ToEuler', 'hg::Vector3', ['?hg::RotationOrder rotation_order'])

	gen.bind_static_method(quaternion, 'Distance', 'float', ['const hg::Quaternion &a', 'const hg::Quaternion &b'])
	gen.bind_static_method(quaternion, 'Slerp', 'hg::Quaternion', ['float t', 'const hg::Quaternion &a', 'const hg::Quaternion &b'])

	gen.bind_static_method(quaternion, 'FromEuler', 'hg::Quaternion', ['float x', 'float y', 'float z', '?hg::RotationOrder rotation_order'])
	gen.bind_static_method(quaternion, 'LookAt', 'hg::Quaternion', ['const hg::Vector3 &at'])
	gen.bind_static_method(quaternion, 'FromMatrix3', 'hg::Quaternion', ['const hg::Matrix3 &m'])
	gen.bind_static_method(quaternion, 'FromAxisAngle', 'hg::Quaternion', ['float angle', 'const hg::Vector3 &axis'])

	gen.end_class(quaternion)

	# hg::Matrix3
	gen.add_include('foundation/matrix3.h')

	matrix3 = gen.begin_class('hg::Matrix3')
	gen.bind_static_members(matrix3, ['const hg::Matrix3 Zero', 'const hg::Matrix3 Identity'])

	gen.bind_constructor_overloads(matrix3, [
		([], []),
		(['const hg::Matrix4 &m'], []),
		(['const hg::Vector3 &x', 'const hg::Vector3 &y', 'const hg::Vector3 &z'], [])
	])

	gen.bind_comparison_ops(matrix3, ['==', '!='], ['const hg::Matrix3 &m'])

	gen.bind_arithmetic_ops(matrix3, ['+', '-'], 'hg::Matrix3', ['hg::Matrix3 &m'])
	gen.bind_arithmetic_op_overloads(matrix3, '*', [
		('hg::Matrix3', ['const float v'], []),
		('hg::tVector2<float>', ['const hg::tVector2<float> &v'], []),
		('hg::Vector3', ['const hg::Vector3 &v'], []),
		('hg::Vector4', ['const hg::Vector4 &v'], []),
		('hg::Matrix3', ['const hg::Matrix3 &m'], [])
	])
	gen.bind_inplace_arithmetic_ops(matrix3, ['+=', '-='], ['const hg::Matrix3 &m'])
	gen.bind_inplace_arithmetic_op_overloads(matrix3, '*=', [
		(['const float k'], []),
		(['const hg::Matrix3 &m'], [])
	])

	gen.bind_method(matrix3, 'Det', 'float', [])
	gen.bind_method(matrix3, 'Inverse', 'bool', ['hg::Matrix3 &I'], {'arg_out': ['I']})

	gen.bind_method(matrix3, 'Transposed', 'hg::Matrix3', [])

	gen.bind_method(matrix3, 'GetRow', 'hg::Vector3', ['uint32_t n'])
	gen.bind_method(matrix3, 'GetColumn', 'hg::Vector3', ['uint32_t n'])
	gen.bind_method(matrix3, 'SetRow', 'void', ['uint32_t n', 'const hg::Vector3 &row'])
	gen.bind_method(matrix3, 'SetColumn', 'void', ['uint32_t n', 'const hg::Vector3 &column'])

	gen.bind_method(matrix3, 'GetX', 'hg::Vector3', [])
	gen.bind_method(matrix3, 'GetY', 'hg::Vector3', [])
	gen.bind_method(matrix3, 'GetZ', 'hg::Vector3', [])
	gen.bind_method(matrix3, 'GetTranslation', 'hg::Vector3', [])
	gen.bind_method(matrix3, 'GetScale', 'hg::Vector3', [])

	gen.bind_method(matrix3, 'SetX', 'void', ['const hg::Vector3 &X'])
	gen.bind_method(matrix3, 'SetY', 'void', ['const hg::Vector3 &Y'])
	gen.bind_method(matrix3, 'SetZ', 'void', ['const hg::Vector3 &Z'])
	gen.bind_method_overloads(matrix3, 'SetTranslation', [
		('void', ['const hg::Vector3 &T'], []),
		('void', ['const hg::tVector2<float> &T'], [])
	])
	gen.bind_method(matrix3, 'SetScale', 'void', ['const hg::Vector3 &S'])

	gen.bind_method(matrix3, 'Set', 'void', ['const hg::Vector3 &X', 'const hg::Vector3 &Y', 'const hg::Vector3 &Z'])

	gen.bind_method(matrix3, 'Normalized', 'hg::Matrix3', [])
	gen.bind_method(matrix3, 'Orthonormalized', 'hg::Matrix3', [])
	gen.bind_method_overloads(matrix3, 'ToEuler', [
		('hg::Vector3', [], []),
		('hg::Vector3', ['hg::RotationOrder rotation_order'], [])
	])

	gen.bind_static_method(matrix3, 'VectorMatrix', 'hg::Matrix3', ['const hg::Vector3 &V'])
	gen.bind_static_method_overloads(matrix3, 'TranslationMatrix', [
		('hg::Matrix3', ['const hg::tVector2<float> &T'], []),
		('hg::Matrix3', ['const hg::Vector3 &T'], [])
	])
	gen.bind_static_method_overloads(matrix3, 'ScaleMatrix', [
		('hg::Matrix3', ['const hg::tVector2<float> &S'], []),
		('hg::Matrix3', ['const hg::Vector3 &S'], [])
	])
	gen.bind_static_method(matrix3, 'CrossProductMatrix', 'hg::Matrix3', ['const hg::Vector3 &V'])

	gen.bind_static_method(matrix3, 'RotationMatrixXAxis', 'hg::Matrix3', ['float angle'])
	gen.bind_static_method(matrix3, 'RotationMatrixYAxis', 'hg::Matrix3', ['float angle'])
	gen.bind_static_method(matrix3, 'RotationMatrixZAxis', 'hg::Matrix3', ['float angle'])

	gen.bind_static_method(matrix3, 'RotationMatrix2D', 'hg::Matrix3', ['float angle', 'const hg::tVector2<float> &pivot'])

	gen.bind_static_method_overloads(matrix3, 'FromEuler', [
		('hg::Matrix3', ['float x', 'float y', 'float z'], []),
		('hg::Matrix3', ['float x', 'float y', 'float z', 'hg::RotationOrder rotation_order'], []),
		('hg::Matrix3', ['const hg::Vector3 &euler'], []),
		('hg::Matrix3', ['const hg::Vector3 &euler', 'hg::RotationOrder rotation_order'], [])
	])

	gen.bind_static_method(matrix3, 'LookAt', 'hg::Matrix3', ['const hg::Vector3 &front', '?const hg::Vector3 &up'])

	gen.end_class(matrix3)

	gen.bind_function('hg::RotationMatrixXZY', 'hg::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('hg::RotationMatrixZYX', 'hg::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('hg::RotationMatrixXYZ', 'hg::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('hg::RotationMatrixZXY', 'hg::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('hg::RotationMatrixYZX', 'hg::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('hg::RotationMatrixYXZ', 'hg::Matrix3', ['float x', 'float y', 'float z'])
	gen.bind_function('hg::RotationMatrixXY', 'hg::Matrix3', ['float x', 'float y'])

	# hg::Matrix4
	gen.add_include('foundation/matrix4.h')

	matrix4 = gen.begin_class('hg::Matrix4')
	gen.bind_static_members(matrix4, ['const hg::Matrix4 Zero', 'const hg::Matrix4 Identity'])

	gen.bind_constructor_overloads(matrix4, [
		([], []),
		(['const hg::Matrix3 &m'], [])
	])

	gen.bind_comparison_ops(matrix4, ['==', '!='], ['const hg::Matrix4 &m'])

	gen.bind_arithmetic_ops(matrix4, ['+', '-'], 'hg::Matrix4', ['hg::Matrix4 &m'])
	gen.bind_arithmetic_op_overloads(matrix4, '*', [
		('hg::Matrix4', ['const float v'], []),
		('hg::Matrix4', ['const hg::Matrix4 &m'], []),
		('hg::Vector3', ['const hg::Vector3 &v'], []),
		('hg::Vector4', ['const hg::Vector4 &v'], []),
		('hg::Matrix44', ['const hg::Matrix44 &m'], [])
	])

	gen.bind_method(matrix4, 'GetRow', 'hg::Vector3', ['uint32_t n'])
	gen.bind_method(matrix4, 'GetColumn', 'hg::Vector4', ['uint32_t n'])
	gen.bind_method(matrix4, 'SetRow', 'void', ['uint32_t n', 'const hg::Vector3 &v'])
	gen.bind_method(matrix4, 'SetColumn', 'void', ['uint32_t n', 'const hg::Vector4 &v'])

	gen.bind_method(matrix4, 'GetX', 'hg::Vector3', [])
	gen.bind_method(matrix4, 'GetY', 'hg::Vector3', [])
	gen.bind_method(matrix4, 'GetZ', 'hg::Vector3', [])
	gen.bind_method(matrix4, 'GetT', 'hg::Vector3', [])
	gen.bind_method(matrix4, 'GetTranslation', 'hg::Vector3', [])
	gen.bind_method(matrix4, 'GetRotation', 'hg::Vector3', ['?hg::RotationOrder rotation_order'])
	gen.bind_method(matrix4, 'GetRotationMatrix', 'hg::Matrix3', [])
	gen.bind_method(matrix4, 'GetScale', 'hg::Vector3', [])

	gen.bind_method(matrix4, 'SetX', 'void', ['const hg::Vector3 &X'])
	gen.bind_method(matrix4, 'SetY', 'void', ['const hg::Vector3 &Y'])
	gen.bind_method(matrix4, 'SetZ', 'void', ['const hg::Vector3 &Z'])
	gen.bind_method(matrix4, 'SetTranslation', 'void', ['const hg::Vector3 &T'])
	gen.bind_method(matrix4, 'SetScale', 'void', ['const hg::Vector3 &scale'])

	gen.bind_method(matrix4, 'Inverse', 'bool', ['hg::Matrix4 &out'])
	gen.bind_method(matrix4, 'InversedFast', 'hg::Matrix4', [])

	gen.bind_method(matrix4, 'Orthonormalized', 'hg::Matrix4', [])

	gen.bind_static_method_overloads(matrix4, 'LerpAsOrthonormalBase', [
		('hg::Matrix4', ['const hg::Matrix4 &from', 'const hg::Matrix4 &to', 'float k'], []),
		('hg::Matrix4', ['const hg::Matrix4 &from', 'const hg::Matrix4 &to', 'float k', 'bool fast'], [])
	])

	#void Decompose(Vector3 *position, Vector3 *scale = nullptr, Matrix3 *rotation = nullptr) const;
	gen.bind_method(matrix4, 'Decompose', 'void', ['hg::Vector3 *position', 'hg::Vector3 *scale', 'hg::Vector3 *rotation', '?hg::RotationOrder rotation_order'], {'arg_out': ['position', 'scale', 'rotation']})

	gen.bind_method(matrix4, 'LookAt', 'hg::Matrix4', ['const hg::Vector3 &at', '?const hg::Vector3 &up'])

	gen.bind_static_method(matrix4, 'TranslationMatrix', 'hg::Matrix4', ['const hg::Vector3 &t'])
	gen.bind_static_method_overloads(matrix4, 'RotationMatrix', [
		('hg::Matrix4', ['const hg::Vector3 &euler'], []),
		('hg::Matrix4', ['const hg::Vector3 &euler', 'hg::RotationOrder order'], [])
	])
	gen.bind_static_method_overloads(matrix4, 'ScaleMatrix', [
		('hg::Matrix4', ['const hg::Vector3 &scale'], []),
		('hg::Matrix4', ['float scale'], [])
	])
	gen.bind_static_method_overloads(matrix4, 'TransformationMatrix', [
		('hg::Matrix4', ['const hg::Vector3 &position', 'const hg::Vector3 &rotation'], []),
		('hg::Matrix4', ['const hg::Vector3 &euler', 'const hg::Vector3 &rotation', 'const hg::Vector3 &scale'], []),
		('hg::Matrix4', ['const hg::Vector3 &position', 'const hg::Matrix3 &rotation'], []),
		('hg::Matrix4', ['const hg::Vector3 &euler', 'const hg::Matrix3 &rotation', 'const hg::Vector3 &scale'], [])
	])
	gen.bind_static_method(matrix4, 'LookToward', 'hg::Matrix4', ['const hg::Vector3 &position', 'const hg::Vector3 &direction', '?const hg::Vector3 &scale'])
	gen.bind_static_method(matrix4, 'LookTowardUp', 'hg::Matrix4', ['const hg::Vector3 &position', 'const hg::Vector3 &direction', 'const hg::Vector3 &up', '?const hg::Vector3 &scale'])

	gen.end_class(matrix4)

	# hg::Matrix44
	gen.add_include('foundation/matrix44.h')

	matrix44 = gen.begin_class('hg::Matrix44')
	gen.bind_static_members(matrix44, ['const hg::Matrix44 Zero', 'const hg::Matrix44 Identity'])

	gen.bind_arithmetic_op_overloads(matrix44, '*', [
		('hg::Matrix44', ['const hg::Matrix4 &m'], []),
		('hg::Matrix44', ['const hg::Matrix44 &m'], [])
	])

	gen.bind_method(matrix44, 'Inverse', 'hg::Matrix44', ['bool &result'], {'arg_out': ['result']})

	gen.bind_method(matrix44, 'GetRow', 'hg::Vector4', ['uint32_t idx'])
	gen.bind_method(matrix44, 'GetColumn', 'hg::Vector4', ['uint32_t idx'])
	gen.bind_method(matrix44, 'SetRow', 'void', ['uint32_t idx', 'const hg::Vector4 &v'])
	gen.bind_method(matrix44, 'SetColumn', 'void', ['uint32_t idx', 'const hg::Vector4 &v'])

	gen.end_class(matrix44)

	# hg::Vector3
	gen.add_include('foundation/vector3.h')
	gen.add_include('foundation/vector3_api.h')

	vector3 = gen.begin_class('hg::Vector3')
	vector3._inline = True

	gen.bind_static_members(vector3, ['const hg::Vector3 Zero', 'const hg::Vector3 One', 'const hg::Vector3 Left', 'const hg::Vector3 Right', 'const hg::Vector3 Up', 'const hg::Vector3 Down', 'const hg::Vector3 Front', 'const hg::Vector3 Back'])
	gen.bind_members(vector3, ['float x', 'float y', 'float z'])

	gen.bind_constructor_overloads(vector3, [
		([], []),
		(['float x', 'float y', 'float z'], []),
		(['const hg::tVector2<float> &v'], []),
		(['const hg::tVector2<int> &v'], []),
		(['const hg::Vector3 &v'], []),
		(['const hg::Vector4 &v'], [])
	])

	gen.bind_function('hg::Vector3FromVector4', 'hg::Vector3', ['const hg::Vector4 &v'])

	gen.bind_arithmetic_ops_overloads(vector3, ['+', '-', '/'], [('hg::Vector3', ['hg::Vector3 &v'], []), ('hg::Vector3', ['float k'], [])])
	gen.bind_arithmetic_ops_overloads(vector3, ['*'], [
		('hg::Vector3', ['const hg::Vector3 &v'], []),
		('hg::Vector3', ['float k'], []),
		('hg::Vector3', ['const hg::Matrix3 &m'], []),
		('hg::Vector3', ['const hg::Matrix4 &m'], []),
		('hg::Vector3', ['const hg::Matrix44 &m'], [])
	])

	gen.bind_inplace_arithmetic_ops_overloads(vector3, ['+=', '-=', '*=', '/='], [
		(['hg::Vector3 &v'], []),
		(['float k'], [])
	])
	gen.bind_comparison_ops(vector3, ['==', '!='], ['const hg::Vector3 &v'])

	gen.bind_function('hg::Dot', 'float', ['const hg::Vector3 &u', 'const hg::Vector3 &v'])
	gen.bind_function('hg::Cross', 'hg::Vector3', ['const hg::Vector3 &u', 'const hg::Vector3 &v'])

	gen.bind_method(vector3, 'Reverse', 'void', [])
	gen.bind_method(vector3, 'Inverse', 'void', [])
	gen.bind_method(vector3, 'Normalize', 'void', [])
	gen.bind_method(vector3, 'Normalized', 'hg::Vector3', [])
	gen.bind_method_overloads(vector3, 'Clamped', [('hg::Vector3', ['float min', 'float max'], []), ('hg::Vector3', ['const hg::Vector3 &min', 'const hg::Vector3 &max'], [])])
	gen.bind_method(vector3, 'ClampedMagnitude', 'hg::Vector3', ['float min', 'float max'])
	gen.bind_method(vector3, 'Reversed', 'hg::Vector3', [])
	gen.bind_method(vector3, 'Inversed', 'hg::Vector3', [])
	gen.bind_method(vector3, 'Abs', 'hg::Vector3', [])
	gen.bind_method(vector3, 'Sign', 'hg::Vector3', [])
	gen.bind_method(vector3, 'Maximum', 'hg::Vector3', ['const hg::Vector3 &left', 'const hg::Vector3 &right'])
	gen.bind_method(vector3, 'Minimum', 'hg::Vector3', ['const hg::Vector3 &left', 'const hg::Vector3 &right'])

	gen.bind_function('hg::Reflect', 'hg::Vector3', ['const hg::Vector3 &v', 'const hg::Vector3 &normal'])
	gen.bind_function_overloads('hg::Refract', [
		('hg::Vector3', ['const hg::Vector3 &v', 'const hg::Vector3 &normal'], []),
		('hg::Vector3', ['const hg::Vector3 &v', 'const hg::Vector3 &normal', 'float index_of_refraction_in', 'float index_of_refraction_out'], [])
	])

	gen.bind_method(vector3, 'Len2', 'float', [])
	gen.bind_method(vector3, 'Len', 'float', [])
	gen.bind_method(vector3, 'Floor', 'hg::Vector3', [])
	gen.bind_method(vector3, 'Ceil', 'hg::Vector3', [])

	gen.insert_binding_code('static void _Vector3_Set(hg::Vector3 *v, float x, float y, float z) { v->x = x; v->y = y; v->z = z; }')
	gen.bind_method(vector3, 'Set', 'void', ['float x', 'float y', 'float z'], {'route': route_lambda('_Vector3_Set')})

	gen.end_class(vector3)

	gen.bind_function_overloads('hg::RandomVector3', [
		('hg::Vector3', ['float min', 'float max'], []),
		('hg::Vector3', ['const hg::Vector3 &min', 'const hg::Vector3 &max'], [])
	])

	# hg::Rect<T>
	def bind_rect_T(T, bound_name):
		rect = gen.begin_class('hg::Rect<%s>'%T, bound_name=bound_name)
		rect._inline = True

		gen.bind_members(rect, ['%s sx'%T, '%s sy'%T, '%s ex'%T, '%s ey'%T])

		gen.bind_constructor_overloads(rect, [
			([], []),
			(['%s usx'%T, '%s usy'%T], []),
			(['%s usx'%T, '%s usy'%T, '%s uex'%T, '%s uey'%T], []),
			(['const hg::Rect<%s> &rect'%T], [])
		])

		gen.bind_method(rect, 'GetX', T, [])
		gen.bind_method(rect, 'GetY', T, [])
		gen.bind_method(rect, 'SetX', 'void', ['%s x'%T])
		gen.bind_method(rect, 'SetY', 'void', ['%s y'%T])

		gen.bind_method(rect, 'GetWidth', T, [])
		gen.bind_method(rect, 'GetHeight', T, [])
		gen.bind_method(rect, 'SetWidth', 'void', ['%s width'%T])
		gen.bind_method(rect, 'SetHeight', 'void', ['%s height'%T])

		gen.bind_method(rect, 'GetSize', 'hg::tVector2<%s>'%T, [])

		gen.bind_method(rect, 'Inside', 'bool', ['%s x'%T, '%s y'%T])

		gen.bind_method(rect, 'FitsInside', 'bool', ['const hg::Rect<%s> &rect'%T])
		gen.bind_method(rect, 'Intersects', 'bool', ['const hg::Rect<%s> &rect'%T])

		gen.bind_method(rect, 'Intersection', 'hg::Rect<%s>'%T, ['const hg::Rect<%s> &rect'%T])

		gen.bind_method(rect, 'Grow', 'hg::Rect<%s>'%T, ['%s border'%T])

		gen.bind_method(rect, 'Offset', 'hg::Rect<%s>'%T, ['%s x'%T, '%s y'%T])
		gen.bind_method(rect, 'Cropped', 'hg::Rect<%s>'%T, ['%s osx'%T, '%s osy'%T, '%s oex'%T, '%s oey'%T])

		gen.bind_static_method(rect, 'FromWidthHeight', 'hg::Rect<%s>'%T, ['%s x'%T, '%s y'%T, '%s w'%T, '%s h'%T])

		gen.end_class(rect)

	bind_rect_T('float', 'Rect')
	bind_rect_T('int', 'IntRect')

	gen.bind_function('ToFloatRect', 'hg::Rect<float>', ['const hg::Rect<int> &rect'])
	gen.bind_function('ToIntRect', 'hg::Rect<int>', ['const hg::Rect<float> &rect'])

	# hg::Plane
	gen.add_include('foundation/plane.h')
	
	gen.insert_binding_code('''\
static void _Plane_Set(hg::Plane *p, const hg::Vector3 &p0, const hg::Vector3 &p1, const hg::Vector3 &p2, const hg::Matrix4 *transform=nullptr) {
	hg::Vector3 frame[3] = { p0, p1, p2};
	p->Set(frame, transform);
}''')

	plane = gen.begin_class('hg::Plane')
	gen.bind_constructor_overloads(plane, [
		([], []),
		(['const hg::Vector3 &p', 'const hg::Vector3 &n', '?const hg::Matrix4 *transform'], []),
	])
	gen.bind_members(plane, ['hg::Vector3 n', 'float d'])
	gen.bind_method(plane, 'DistanceToPlane', 'float', ['const hg::Vector3& p'], [])
	gen.bind_method_overloads(plane, 'Set', [
		('void', ['const hg::Vector3 &p', 'const hg::Vector3 &n', '?const hg::Matrix4 *transform'], []),
		('void', ['const hg::Vector3 &p0', 'const hg::Vector3 &p1', 'const hg::Vector3 &p2', '?const hg::Matrix4 *transform'], {'route': route_lambda('_Plane_Set')}),
	])
	gen.end_class(plane)

	# hg::AxisLock
	gen.add_include('foundation/axis_lock.h')
	gen.insert_binding_code('''
namespace Binding {
enum AxisLock {
	X = hg::AxisLock::LockX,
	Y = hg::AxisLock::LockY,
	Z = hg::AxisLock::LockZ, 
	RotX = hg::AxisLock::LockRotX,
	RotY = hg::AxisLock::LockRotY,
	RotZ = hg::AxisLock::LockRotZ
};
}
''')
	gen.bind_named_enum('Binding::AxisLock', ['X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ'], 'uint8_t', bound_name='AxisLock', prefix='AxisLock')

	# math futures
	lib.stl.bind_future_T(gen, 'hg::tVector2<float>', 'FutureVector2')
	lib.stl.bind_future_T(gen, 'hg::tVector2<int>', 'FutureIntVector2')
	lib.stl.bind_future_T(gen, 'hg::Vector3', 'FutureVector3')
	lib.stl.bind_future_T(gen, 'hg::Vector4', 'FutureVector4')
	lib.stl.bind_future_T(gen, 'hg::Matrix3', 'FutureMatrix3')
	lib.stl.bind_future_T(gen, 'hg::Matrix4', 'FutureMatrix4')
	lib.stl.bind_future_T(gen, 'hg::Matrix44', 'FutureMatrix44')
	lib.stl.bind_future_T(gen, 'hg::Rect<float>', 'FutureFloatRect')
	lib.stl.bind_future_T(gen, 'hg::Rect<int>', 'FutureIntRect')

	# math std::vector
	bind_std_vector(gen, vector2)
	bind_std_vector(gen, ivector2)
	bind_std_vector(gen, vector3)
	bind_std_vector(gen, vector4)
	bind_std_vector(gen, matrix3)
	bind_std_vector(gen, matrix4)
	bind_std_vector(gen, matrix44)

	# globals
	gen.bind_function_overloads('hg::Dist', [
		('float', ['const hg::Vector3 &a', 'const hg::Vector3 &b'], [])
	])
	gen.bind_function_overloads('hg::Dist2', [
		('float', ['const hg::Vector3 &a', 'const hg::Vector3 &b'], [])
	])


def bind_frustum(gen):
	gen.add_include('foundation/frustum.h')

	gen.bind_named_enum('hg::Frustum::Type', ['Perspective', 'Orthographic'], 'uint8_t', bound_name='FrustumType', prefix='Frustum')

	frustum = gen.begin_class('hg::Frustum')
	gen.bind_members(frustum, ['hg::Frustum::Type type', 'float fov_size', 'hg::tVector2<float> aspect_ratio', 'float znear', 'float zfar', 'hg::Matrix4 world'])
	gen.end_class(frustum)

	gen.insert_binding_code('''
static const hg::Plane &_FrustumPlanes_GetTop(hg::FrustumPlanes *fsplanes) { return fsplanes->plane[hg::FrustumPlaneTop]; }
static void _FrustumPlanes_SetTop(hg::FrustumPlanes *fsplanes, const hg::Plane &plane) { fsplanes->plane[hg::FrustumPlaneTop] = plane; }
static const hg::Plane &_FrustumPlanes_GetBottom(hg::FrustumPlanes *fsplanes) { return fsplanes->plane[hg::FrustumPlaneBottom]; }
static void _FrustumPlanes_SetBottom(hg::FrustumPlanes *fsplanes, const hg::Plane &plane) { fsplanes->plane[hg::FrustumPlaneBottom] = plane; }
static const hg::Plane &_FrustumPlanes_GetLeft(hg::FrustumPlanes *fsplanes) { return fsplanes->plane[hg::FrustumPlaneLeft]; }
static void _FrustumPlanes_SetLeft(hg::FrustumPlanes *fsplanes, const hg::Plane &plane) { fsplanes->plane[hg::FrustumPlaneLeft] = plane; }
static const hg::Plane &_FrustumPlanes_GetRight(hg::FrustumPlanes *fsplanes) { return fsplanes->plane[hg::FrustumPlaneRight]; }
static void _FrustumPlanes_SetRight(hg::FrustumPlanes *fsplanes, const hg::Plane &plane) { fsplanes->plane[hg::FrustumPlaneRight] = plane; }
static const hg::Plane &_FrustumPlanes_GetNear(hg::FrustumPlanes *fsplanes) { return fsplanes->plane[hg::FrustumPlaneNear]; }
static void _FrustumPlanes_SetNear(hg::FrustumPlanes *fsplanes, const hg::Plane &plane) { fsplanes->plane[hg::FrustumPlaneNear] = plane; }
static const hg::Plane &_FrustumPlanes_GetFar(hg::FrustumPlanes *fsplanes) { return fsplanes->plane[hg::FrustumPlaneFar]; }
static void _FrustumPlanes_SetFar(hg::FrustumPlanes *fsplanes, const hg::Plane &plane) { fsplanes->plane[hg::FrustumPlaneFar] = plane; }
''')

	frustum_planes = gen.begin_class('hg::FrustumPlanes')
	gen.bind_method(frustum_planes, 'GetTop', 'hg::Plane', [], {'route': route_lambda('_FrustumPlanes_GetTop')})
	gen.bind_method(frustum_planes, 'SetTop', 'void', ['const hg::Plane &plane'], {'route': route_lambda('_FrustumPlanes_SetTop')})
	gen.bind_method(frustum_planes, 'GetBottom', 'hg::Plane', [], {'route': route_lambda('_FrustumPlanes_GetBottom')})
	gen.bind_method(frustum_planes, 'SetBottom', 'void', ['const hg::Plane &plane'], {'route': route_lambda('_FrustumPlanes_SetBottom')})
	gen.bind_method(frustum_planes, 'GetLeft', 'hg::Plane', [], {'route': route_lambda('_FrustumPlanes_GetLeft')})
	gen.bind_method(frustum_planes, 'SetLeft', 'void', ['const hg::Plane &plane'], {'route': route_lambda('_FrustumPlanes_SetLeft')})
	gen.bind_method(frustum_planes, 'GetRight', 'hg::Plane', [], {'route': route_lambda('_FrustumPlanes_GetRight')})
	gen.bind_method(frustum_planes, 'SetRight', 'void', ['const hg::Plane &plane'], {'route': route_lambda('_FrustumPlanes_SetRight')})
	gen.bind_method(frustum_planes, 'GetNear', 'hg::Plane', [], {'route': route_lambda('_FrustumPlanes_GetNear')})
	gen.bind_method(frustum_planes, 'SetNear', 'void', ['const hg::Plane &plane'], {'route': route_lambda('_FrustumPlanes_SetNear')})
	gen.bind_method(frustum_planes, 'GetFar', 'hg::Plane', [], {'route': route_lambda('_FrustumPlanes_GetFar')})
	gen.bind_method(frustum_planes, 'SetFar', 'void', ['const hg::Plane &plane'], {'route': route_lambda('_FrustumPlanes_SetFar')})
	gen.end_class(frustum_planes)

	gen.bind_function('hg::MakePerspectiveFrustum', 'hg::Frustum', ['float znear', 'float zfar', 'float fov', 'const hg::tVector2<float> &ar', 'const hg::Matrix4 &m'])
	gen.bind_function('hg::MakeOrthographicFrustum', 'hg::Frustum', ['float znear', 'float zfar', 'float size', 'const hg::tVector2<float> &ar', 'const hg::Matrix4 &m'])
	gen.bind_function('hg::BuildFrustumPlanes', 'hg::FrustumPlanes', ['const hg::Frustum &frustum'])
	
	gen.insert_binding_code('''\
static void BuildFrustumVertices(const hg::Frustum &frustum, hg::Vector3 &v0, hg::Vector3 &v1, hg::Vector3 &v2, hg::Vector3 &v3, hg::Vector3 &v4, hg::Vector3 &v5, hg::Vector3 &v6, hg::Vector3 &v7) {
	auto vertices = hg::BuildFrustumVertices(frustum);
	v0 = vertices[0]; v1 = vertices[1]; v2 = vertices[2]; v3 = vertices[3];
	v4 = vertices[4]; v5 = vertices[5]; v6 = vertices[6]; v7 = vertices[7];
}
''')
	gen.bind_function('BuildFrustumVertices', 'void', ['const hg::Frustum &frustum','hg::Vector3 &v0', 'hg::Vector3 &v1', 'hg::Vector3 &v2', 'hg::Vector3 &v3', 'hg::Vector3 &v4', 'hg::Vector3 &v5', 'hg::Vector3 &v6', 'hg::Vector3 &v7'], {'arg_out': ['v0','v1','v2','v3','v4','v5','v6','v7']})
	gen.bind_function('hg::BuildFrustumPlanesFromProjectionMatrix', 'hg::FrustumPlanes', ['const hg::Matrix44 &projection'])

	gen.bind_named_enum('hg::Visibility', ['Outside', 'Inside', 'Clipped'], 'uint8_t', bound_name='Visibility')
	gen.bind_function('hg::ClassifyPoint', 'hg::Visibility', ['const hg::FrustumPlanes &frustum', 'uint32_t count', 'const hg::Vector3 *points', '?float distance'])
	gen.bind_function('hg::ClassifySphere', 'hg::Visibility', ['const hg::FrustumPlanes &frustum', 'const hg::Vector3 &origin', 'float radius'])
	gen.bind_function('hg::ClassifyMinMax', 'hg::Visibility', ['const hg::FrustumPlanes &frustum', 'const hg::MinMax &minmax'])


def bind_mixer(gen):
	gen.add_include('engine/mixer.h')

	# hg::AudioFormat
	gen.bind_named_enum('hg::AudioFormat::Encoding', ['PCM', 'WiiADPCM'], 'uint8_t', bound_name='AudioFormatEncoding', prefix='AudioFormat')
	gen.bind_named_enum('hg::AudioFormat::Type', ['Integer', 'Float'], 'uint8_t', bound_name='AudioFormatType', prefix='AudioType')

	audio_format = gen.begin_class('hg::AudioFormat')
	gen.bind_constructor_overloads(audio_format, [
			([], []),
			(['hg::AudioFormat::Encoding encoding'], []),
			(['hg::AudioFormat::Encoding encoding', 'uint8_t channels'], []),
			(['hg::AudioFormat::Encoding encoding', 'uint8_t channels', 'uint32_t frequency'], []),
			(['hg::AudioFormat::Encoding encoding', 'uint8_t channels', 'uint32_t frequency', 'uint8_t resolution'], []),
			(['hg::AudioFormat::Encoding encoding', 'uint8_t channels', 'uint32_t frequency', 'uint8_t resolution', 'hg::AudioFormat::Type type'], [])
		])
	gen.bind_members(audio_format, ['hg::AudioFormat::Encoding encoding', 'uint8_t channels', 'uint32_t frequency', 'uint8_t resolution', 'hg::AudioFormat::Type type'])
	gen.end_class(audio_format)

	# hg::AudioData
	gen.bind_named_enum('hg::AudioData::State', ['Ready', 'Ended', 'Disconnected'], bound_name='AudioDataState', prefix='AudioData')

	audio_data = gen.begin_class('hg::AudioData', bound_name='AudioData_nobind', noncopyable=True, nobind=True)
	gen.end_class(audio_data)

	shared_audio_data = gen.begin_class('std::shared_ptr<hg::AudioData>', bound_name='AudioData', features={'proxy': lib.stl.SharedPtrProxyFeature(audio_data)})

	gen.bind_method(shared_audio_data, 'GetFormat', 'hg::AudioFormat', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'Open', 'bool', ['const std::string &path'], ['proxy'])
	gen.bind_method(shared_audio_data, 'Close', 'void', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'GetState', 'hg::AudioData::State', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'Seek', 'bool', ['hg::time_ns t'], ['proxy'])

	gen.insert_binding_code('''\
static size_t AudioData_GetFrameToBinaryData(hg::AudioData *audio_data, hg::BinaryData &frame, hg::time_ns &frame_timestamp) {
	frame.Reset();
	frame.Grow(audio_data->GetFrameSize());
	size_t size = audio_data->GetFrame(frame.GetData(), frame_timestamp);
	frame.Commit(size);
	return size;
}
''', 'AudioData class extension')

	gen.bind_method(shared_audio_data, 'GetFrame', 'size_t', ['hg::BinaryData &frame', 'hg::time_ns &frame_timestamp'], {'proxy': None, 'arg_out': ['frame_timestamp'], 'route': lambda args: 'AudioData_GetFrameToBinaryData(%s);' % (', '.join(args))})
	gen.bind_method(shared_audio_data, 'GetFrameSize', 'size_t', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'SetTransform', 'void', ['const hg::Matrix4 &m'], ['proxy'])
	gen.bind_method(shared_audio_data, 'GetDataSize', 'size_t', [], ['proxy'])

	gen.end_class(shared_audio_data)

	gen.insert_binding_code('''\
static size_t AudioData_ExtractAudioData(hg::AudioData* source, hg::BinaryData &frame) {
	std::vector<char> buffer;
	size_t size = ExtractAudioData(*source, buffer);

	frame.Reset();
	frame.Write(&buffer[0], size);
	frame.Commit(size);
	return size;
}
''')
	gen.bind_function('ExtractAudioData', 'size_t', ['hg::AudioData *source', 'hg::BinaryData &data'], {'route':  route_lambda('AudioData_ExtractAudioData')})

	# hg::AudioIO
	gen.add_include('engine/audio_io.h')

	audio_io = gen.begin_class('hg::AudioIO', noncopyable=True)
	gen.bind_method(audio_io, 'Open', 'std::shared_ptr<hg::AudioData>', ['const std::string &path', '?const std::string &codec_name'])
	gen.bind_method(audio_io, 'GetSupportedExt', 'std::string', [])
	gen.end_class(audio_io)

	gen.insert_binding_code('static hg::AudioIO &GetAudioIO() { return hg::g_audio_io.get(); }')
	gen.bind_function('GetAudioIO', 'hg::AudioIO &', [])

	# hg::audio
	gen.bind_named_enum('hg::MixerLoopMode', ['MixerNoLoop', 'MixerRepeat', 'MixerLoopInvalidChannel'], 'uint8_t')
	gen.bind_named_enum('hg::MixerPlayState', ['MixerStopped', 'MixerPlaying', 'MixerPaused', 'MixerStateInvalidChannel'], 'uint8_t')

	gen.typedef('hg::MixerChannel', 'int32_t')
	gen.typedef('hg::MixerPriority', 'uint8_t')

	#
	mixer_channel_state = gen.begin_class('hg::MixerChannelState')
	gen.bind_constructor_overloads(mixer_channel_state, [
		([], []),
		(['float volume'], []),
		(['float volume', 'bool direct'], []),
		(['hg::MixerPriority priority', '?float volume', '?hg::MixerLoopMode loop_mode', '?float pitch', '?bool direct'], [])
	])
	gen.bind_members(mixer_channel_state, ['hg::MixerPriority priority', 'hg::MixerLoopMode loop_mode', 'float volume', 'float pitch', 'bool direct'])
	gen.end_class(mixer_channel_state)

	mixer_channel_location = gen.begin_class('hg::MixerChannelLocation')
	gen.bind_constructor_overloads(mixer_channel_location, [
		([], []),
		(['const hg::Vector3 &pos'], [])
	])
	gen.bind_members(mixer_channel_location, ['hg::Vector3 position', 'hg::Vector3 velocity'])
	gen.end_class(mixer_channel_location)

	#
	sound = gen.begin_class('hg::Sound', bound_name='Sound_nobind', noncopyable=True, nobind=True)
	gen.end_class(sound)

	shared_sound = gen.begin_class('std::shared_ptr<hg::Sound>', bound_name='Sound', features={'proxy': lib.stl.SharedPtrProxyFeature(sound)})
	gen.bind_constructor(shared_sound, ['?const std::string &name'], ['proxy'])
	gen.bind_method(shared_sound, 'GetName', 'const std::string &', [], ['proxy'])
	gen.bind_method(shared_sound, 'IsReady', 'bool', [], ['proxy'])
	gen.bind_method(shared_sound, 'SetReady', 'void', [], ['proxy'])
	gen.bind_method(shared_sound, 'SetNotReady', 'void', [], ['proxy'])
	gen.end_class(shared_sound)

	# hg::Mixer
	audio_mixer = gen.begin_class('hg::Mixer', bound_name='Mixer_nobind', noncopyable=True, nobind=True)
	gen.end_class(audio_mixer)

	shared_audio_mixer = gen.begin_class('std::shared_ptr<hg::Mixer>', bound_name='Mixer', features={'proxy': lib.stl.SharedPtrProxyFeature(audio_mixer)})

	gen.bind_static_members(shared_audio_mixer, [
		'const hg::MixerChannelState DefaultState', 'const hg::MixerChannelState RepeatState',
		'const hg::MixerChannelLocation DefaultLocation', 'const hg::MixerPriority DefaultPriority',
		'const hg::MixerChannel ChannelError'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'Open', 'bool', [], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'Close', 'void', [], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetMasterVolume', 'float', [], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SetMasterVolume', 'void', ['float volume'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'EnableSpatialization', 'bool', ['bool enable'], ['proxy'])

	gen.bind_method_overloads(shared_audio_mixer, 'Start', [
		('hg::MixerChannel', ['hg::Sound &sound'], ['proxy']),
		('hg::MixerChannel', ['hg::Sound &sound', 'hg::MixerChannelState state'], ['proxy']),
		('hg::MixerChannel', ['hg::Sound &sound', 'hg::MixerChannelLocation location'], ['proxy']),
		('hg::MixerChannel', ['hg::Sound &sound', 'hg::MixerChannelLocation location', 'hg::MixerChannelState state'], ['proxy'])
	])
	gen.bind_method_overloads(shared_audio_mixer, 'StreamData', [
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'bool paused'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'bool paused', 'hg::time_ns t_start'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'hg::MixerChannelState state'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'hg::MixerChannelState state', 'bool paused'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'hg::MixerChannelState state', 'bool paused', 'hg::time_ns t_start'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'hg::MixerChannelLocation location'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'hg::MixerChannelLocation location', 'bool paused'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'hg::MixerChannelLocation location', 'bool paused', 'hg::time_ns t_start'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'hg::MixerChannelLocation location', 'hg::MixerChannelState state'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'hg::MixerChannelLocation location', 'hg::MixerChannelState state', 'bool paused'], ['proxy']),
		('hg::MixerChannel', ['std::shared_ptr<hg::AudioData> data', 'hg::MixerChannelLocation location', 'hg::MixerChannelState state', 'bool paused', 'hg::time_ns t_start'], ['proxy'])
	])

	gen.bind_method(shared_audio_mixer, 'GetPlayState', 'hg::MixerPlayState', ['hg::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetChannelState', 'hg::MixerChannelState', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SetChannelState', 'void', ['hg::MixerChannel channel', 'hg::MixerChannelState state'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetChannelLocation', 'hg::MixerChannelLocation', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SetChannelLocation', 'void', ['hg::MixerChannel channel', 'hg::MixerChannelLocation location'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetChannelTimestamp', 'hg::time_ns', ['hg::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'Stop', 'void', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'Pause', 'void', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'Resume', 'void', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'StopAll', 'void', [], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'SetStreamLoopPoint', 'void', ['hg::MixerChannel channel', 'hg::time_ns t'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SeekStream', 'void', ['hg::MixerChannel channel', 'hg::time_ns t'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'GetStreamBufferingPercentage', 'int', ['hg::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'SetChannelStreamDataTransform', 'void', ['hg::MixerChannel channel', 'const hg::Matrix4 &transform'], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'FlushChannelBuffers', 'void', ['hg::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_audio_mixer, 'GetListener', 'hg::Matrix4', [], ['proxy'])
	gen.bind_method(shared_audio_mixer, 'SetListener', 'void', ['const hg::Matrix4 &transform'], ['proxy'])

	gen.bind_method_overloads(shared_audio_mixer, 'Stream', [
		('hg::MixerChannel', ['const std::string &path', '?bool paused', '?hg::time_ns t_start'], ['proxy']),
		('hg::MixerChannel', ['const std::string &path', 'hg::MixerChannelState state', '?bool paused', '?hg::time_ns t_start'], ['proxy']),
		('hg::MixerChannel', ['const std::string &path', 'hg::MixerChannelLocation location', '?bool paused', '?hg::time_ns t_start'], ['proxy']),
		('hg::MixerChannel', ['const std::string &path', 'hg::MixerChannelLocation location', 'hg::MixerChannelState state', '?bool paused', '?hg::time_ns t_start'], ['proxy'])
	])

	gen.bind_method_overloads(shared_audio_mixer, 'LoadSoundData', [
		('std::shared_ptr<hg::Sound>', ['std::shared_ptr<hg::AudioData> data'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'LoadSoundData failed')}),
		('std::shared_ptr<hg::Sound>', ['std::shared_ptr<hg::AudioData> data', 'const std::string &path'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'LoadSoundData failed')})
	])

	gen.bind_method(shared_audio_mixer, 'LoadSound', 'std::shared_ptr<hg::Sound>', ['const std::string &path'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'LoadSound failed')})
	gen.bind_method(shared_audio_mixer, 'FreeSound', 'void', ['hg::Sound &sound'], ['proxy'])

	gen.end_class(shared_audio_mixer)

	gen.insert_binding_code('''static std::shared_ptr<hg::Mixer> CreateMixer(const std::string &name) { return hg::g_mixer_factory.get().Instantiate(name); }
static std::shared_ptr<hg::Mixer> CreateMixer() { return hg::g_mixer_factory.get().Instantiate(); }
	''', 'Mixer custom API')

	gen.bind_function('CreateMixer', 'std::shared_ptr<hg::Mixer>', ['?const std::string &name'], {'check_rval': check_bool_rval_lambda(gen, 'CreateMixer failed, was LoadPlugins called succesfully?')})

	# hg::MixerAsync
	gen.add_include('engine/mixer_async.h')

	mixer_async = gen.begin_class('hg::MixerAsync', bound_name='MixerAsync_nobind', noncopyable=True, nobind=True)
	gen.end_class(mixer_async)

	shared_mixer_async = gen.begin_class('std::shared_ptr<hg::MixerAsync>', bound_name='MixerAsync', features={'proxy': lib.stl.SharedPtrProxyFeature(mixer_async)})

	gen.bind_constructor(shared_mixer_async, ['std::shared_ptr<hg::Mixer> mixer'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'Open', 'std::future<bool>', [], ['proxy'])
	gen.bind_method(shared_mixer_async, 'Close', 'std::future<void>', [], ['proxy'])

	gen.bind_method(shared_mixer_async, 'EnableSpatialization', 'std::future<bool>', ['bool enable'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetMasterVolume', 'std::future<float>', [], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SetMasterVolume', 'void', ['float volume'], ['proxy'])

	lib.stl.bind_future_T(gen, 'hg::MixerChannel', 'FutureMixerChannel')
	lib.stl.bind_future_T(gen, 'hg::MixerChannelState', 'FutureMixerChannelState')
	lib.stl.bind_future_T(gen, 'hg::MixerChannelLocation', 'FutureMixerChannelLocation')
	lib.stl.bind_future_T(gen, 'hg::MixerPlayState', 'FutureMixerPlayState')

	gen.bind_method_overloads(shared_mixer_async, 'Start', [
		('std::future<hg::MixerChannel>', ['std::shared_ptr<hg::Sound> sound'], ['proxy']),
		('std::future<hg::MixerChannel>', ['std::shared_ptr<hg::Sound> sound', 'hg::MixerChannelState state'], ['proxy']),
		('std::future<hg::MixerChannel>', ['std::shared_ptr<hg::Sound> sound', 'hg::MixerChannelLocation location'], ['proxy']),
		('std::future<hg::MixerChannel>', ['std::shared_ptr<hg::Sound> sound', 'hg::MixerChannelLocation location', 'hg::MixerChannelState state'], ['proxy'])
	])
	gen.bind_method_overloads(shared_mixer_async, 'Stream', [
		('std::future<hg::MixerChannel>', ['const std::string &path', '?bool paused', '?hg::time_ns t_start'], ['proxy']),
		('std::future<hg::MixerChannel>', ['const std::string &path', 'hg::MixerChannelState state', '?bool paused', '?hg::time_ns t_start'], ['proxy']),
		('std::future<hg::MixerChannel>', ['const std::string &path', 'hg::MixerChannelLocation location', '?bool paused', '?hg::time_ns t_start'], ['proxy']),
		('std::future<hg::MixerChannel>', ['const std::string &path', 'hg::MixerChannelLocation location', 'hg::MixerChannelState state', '?bool paused', '?hg::time_ns t_start'], ['proxy'])
	])

	gen.bind_method(shared_mixer_async, 'GetPlayState', 'std::future<hg::MixerPlayState>', ['hg::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetChannelState', 'std::future<hg::MixerChannelState>', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SetChannelState', 'void', ['hg::MixerChannel channel', 'hg::MixerChannelState state'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetChannelLocation', 'std::future<hg::MixerChannelLocation>', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SetChannelLocation', 'void', ['hg::MixerChannel channel', 'hg::MixerChannelLocation location'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetChannelTimestamp', 'std::future<hg::time_ns>', ['hg::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'Stop', 'void', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'Pause', 'void', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'Resume', 'void', ['hg::MixerChannel channel'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'StopAll', 'void', [], ['proxy'])

	gen.bind_method(shared_mixer_async, 'SetStreamLoopPoint', 'void', ['hg::MixerChannel channel', 'hg::time_ns t'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SeekStream', 'void', ['hg::MixerChannel channel', 'hg::time_ns t'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'GetStreamBufferingPercentage', 'std::future<int>', ['hg::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'SetChannelStreamDataTransform', 'void', ['hg::MixerChannel channel', 'const hg::Matrix4 &transform'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'FlushChannelBuffers', 'void', ['hg::MixerChannel channel'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'GetListener', 'std::future<hg::Matrix4>', [], ['proxy'])
	gen.bind_method(shared_mixer_async, 'SetListener', 'void', ['const hg::Matrix4 &transform'], ['proxy'])

	gen.bind_method(shared_mixer_async, 'LoadSound', 'std::shared_ptr<hg::Sound>', ['const std::string &path'], {'proxy': None, 'check_rval': check_bool_rval_lambda(gen, 'LoadSound failed')})
	gen.bind_method(shared_mixer_async, 'FreeSound', 'void', ['const std::shared_ptr<hg::Sound> &sound'], ['proxy'])

	gen.end_class(shared_mixer_async)


def bind_movie(gen):
	gen.add_include('engine/movie.h')

	# hg::Movie
	gen.bind_named_enum('hg::Movie::FrameFormat', ['YUV3PlanesHalfChroma', 'ExternalOES'], bound_name='MovieFrameFormat')

	movie = gen.begin_class('hg::Movie', bound_name='Movie_nobind', noncopyable=True, nobind=True)
	gen.end_class(movie)

	shared_movie = gen.begin_class('std::shared_ptr<hg::Movie>', bound_name='Movie', features={'proxy': lib.stl.SharedPtrProxyFeature(movie)})

	gen.bind_method(shared_movie, 'Open', 'bool', ['std::shared_ptr<hg::Renderer> renderer', 'std::shared_ptr<hg::Mixer> mixer', 'const std::string &filename', '?bool paused'], ['proxy'])
	gen.bind_method(shared_movie, 'Play', 'bool', [], ['proxy'])
	gen.bind_method(shared_movie, 'Pause', 'bool', [], ['proxy'])
	gen.bind_method(shared_movie, 'Close', 'bool', [], ['proxy'])

	gen.bind_method(shared_movie, 'GetDuration', 'hg::time_ns', [], ['proxy'])
	gen.bind_method(shared_movie, 'GetTimeStamp', 'hg::time_ns', [], ['proxy'])
	gen.bind_method(shared_movie, 'Seek', 'bool', ['hg::time_ns t'], ['proxy'])
	gen.bind_method(shared_movie, 'IsEnded', 'bool', [], ['proxy'])
	gen.bind_method(shared_movie, 'GetFormat', 'hg::Movie::FrameFormat', [], ['proxy'])
	gen.bind_method(shared_movie, 'GetFrame', 'bool', ['std::vector<std::shared_ptr<hg::Texture>> &planes'], {'proxy':None, 'arg_out': ['planes']})
	
	gen.end_class(shared_movie)
	# [todo] GetFrame
	
	gen.insert_binding_code('''static std::shared_ptr<hg::Movie> CreateMovie(const std::string &name) { return hg::g_movie_factory.get().Instantiate(name); }
static std::shared_ptr<hg::Movie> CreateMovie() { return hg::g_movie_factory.get().Instantiate(); }
	''', 'Movie custom API')

	gen.bind_function('CreateMovie', 'std::shared_ptr<hg::Movie>', ['?const std::string &name'], {'check_rval': check_bool_rval_lambda(gen, 'CreateMovie failed, was LoadPlugins called succesfully?')})


def bind_imgui(gen):
	gen.add_include('engine/imgui.h')
	gen.add_include('engine/imgui_hg_ext.h')

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
		'ImGuiWindowFlags_NoCollapse', 'ImGuiWindowFlags_AlwaysAutoResize', 'ImGuiWindowFlags_NoSavedSettings', 'ImGuiWindowFlags_NoInputs',
		'ImGuiWindowFlags_MenuBar', 'ImGuiWindowFlags_HorizontalScrollbar', 'ImGuiWindowFlags_NoFocusOnAppearing', 'ImGuiWindowFlags_NoBringToFrontOnFocus',
		'ImGuiWindowFlags_AlwaysVerticalScrollbar', 'ImGuiWindowFlags_AlwaysHorizontalScrollbar', 'ImGuiWindowFlags_AlwaysUseWindowPadding'
	], 'int', namespace='')

	gen.bind_named_enum('ImGuiCond', ['ImGuiCond_Always', 'ImGuiCond_Once', 'ImGuiCond_FirstUseEver', 'ImGuiCond_Appearing'], 'int', namespace='')

	gen.bind_named_enum('ImGuiHoveredFlags', ['ImGuiHoveredFlags_Default', 'ImGuiHoveredFlags_ChildWindows', 'ImGuiHoveredFlags_RootWindow', 'ImGuiHoveredFlags_AllowWhenBlockedByPopup', 'ImGuiHoveredFlags_AllowWhenBlockedByActiveItem', 'ImGuiHoveredFlags_AllowWhenOverlapped', 'ImGuiHoveredFlags_RectOnly', 'ImGuiHoveredFlags_RootAndChildWindows'], 'int', namespace='')
	gen.bind_named_enum('ImGuiFocusedFlags', ['ImGuiFocusedFlags_ChildWindows', 'ImGuiFocusedFlags_RootWindow', 'ImGuiFocusedFlags_RootAndChildWindows'], 'int', namespace='')

	gen.bind_named_enum('ImGuiColorEditFlags', [
		'ImGuiColorEditFlags_NoAlpha', 'ImGuiColorEditFlags_NoPicker', 'ImGuiColorEditFlags_NoOptions', 'ImGuiColorEditFlags_NoSmallPreview', 'ImGuiColorEditFlags_NoInputs', 'ImGuiColorEditFlags_NoTooltip', 'ImGuiColorEditFlags_NoLabel', 'ImGuiColorEditFlags_NoSidePreview',
		'ImGuiColorEditFlags_AlphaBar', 'ImGuiColorEditFlags_AlphaPreview', 'ImGuiColorEditFlags_AlphaPreviewHalf', 'ImGuiColorEditFlags_HDR', 'ImGuiColorEditFlags_RGB', 'ImGuiColorEditFlags_HSV', 'ImGuiColorEditFlags_HEX', 'ImGuiColorEditFlags_Uint8', 'ImGuiColorEditFlags_Float', 'ImGuiColorEditFlags_PickerHueBar', 'ImGuiColorEditFlags_PickerHueWheel'
	], 'int', namespace='')

	gen.bind_named_enum('ImGuiInputTextFlags', [
		'ImGuiInputTextFlags_CharsDecimal', 'ImGuiInputTextFlags_CharsHexadecimal', 'ImGuiInputTextFlags_CharsUppercase', 'ImGuiInputTextFlags_CharsNoBlank',
		'ImGuiInputTextFlags_AutoSelectAll', 'ImGuiInputTextFlags_EnterReturnsTrue', 'ImGuiInputTextFlags_CallbackCompletion', 'ImGuiInputTextFlags_CallbackHistory',
		'ImGuiInputTextFlags_CallbackAlways', 'ImGuiInputTextFlags_CallbackCharFilter', 'ImGuiInputTextFlags_AllowTabInput', 'ImGuiInputTextFlags_CtrlEnterForNewLine',
		'ImGuiInputTextFlags_NoHorizontalScroll', 'ImGuiInputTextFlags_AlwaysInsertMode', 'ImGuiInputTextFlags_ReadOnly', 'ImGuiInputTextFlags_Password'
	], 'int', namespace='')

	gen.bind_named_enum('ImGuiTreeNodeFlags', [
		'ImGuiTreeNodeFlags_Selected', 'ImGuiTreeNodeFlags_Framed', 'ImGuiTreeNodeFlags_AllowItemOverlap', 'ImGuiTreeNodeFlags_NoTreePushOnOpen',
		'ImGuiTreeNodeFlags_NoAutoOpenOnLog', 'ImGuiTreeNodeFlags_DefaultOpen', 'ImGuiTreeNodeFlags_OpenOnDoubleClick', 'ImGuiTreeNodeFlags_OpenOnArrow',
		'ImGuiTreeNodeFlags_Leaf', 'ImGuiTreeNodeFlags_Bullet', 'ImGuiTreeNodeFlags_CollapsingHeader'
	], 'int', namespace='')

	gen.bind_named_enum('ImGuiSelectableFlags', ['ImGuiSelectableFlags_DontClosePopups', 'ImGuiSelectableFlags_SpanAllColumns', 'ImGuiSelectableFlags_AllowDoubleClick'], 'int', namespace='')

	gen.bind_named_enum('ImGuiCol', [
		'ImGuiCol_Text', 'ImGuiCol_TextDisabled', 'ImGuiCol_WindowBg', 'ImGuiCol_ChildBg', 'ImGuiCol_PopupBg', 'ImGuiCol_Border', 'ImGuiCol_BorderShadow',
		'ImGuiCol_FrameBg', 'ImGuiCol_FrameBgHovered', 'ImGuiCol_FrameBgActive', 'ImGuiCol_TitleBg', 'ImGuiCol_TitleBgCollapsed', 'ImGuiCol_TitleBgActive', 'ImGuiCol_MenuBarBg',
		'ImGuiCol_ScrollbarBg', 'ImGuiCol_ScrollbarGrab', 'ImGuiCol_ScrollbarGrabHovered', 'ImGuiCol_ScrollbarGrabActive', 'ImGuiCol_CheckMark',
		'ImGuiCol_SliderGrab', 'ImGuiCol_SliderGrabActive', 'ImGuiCol_Button', 'ImGuiCol_ButtonHovered', 'ImGuiCol_ButtonActive', 'ImGuiCol_Header', 'ImGuiCol_HeaderHovered',
		'ImGuiCol_HeaderActive', 'ImGuiCol_Separator', 'ImGuiCol_SeparatorHovered', 'ImGuiCol_SeparatorActive', 'ImGuiCol_ResizeGrip', 'ImGuiCol_ResizeGripHovered', 'ImGuiCol_ResizeGripActive',
		'ImGuiCol_CloseButton', 'ImGuiCol_CloseButtonHovered', 'ImGuiCol_CloseButtonActive', 'ImGuiCol_PlotLines', 'ImGuiCol_PlotLinesHovered', 'ImGuiCol_PlotHistogram', 'ImGuiCol_PlotHistogramHovered',
		'ImGuiCol_TextSelectedBg', 'ImGuiCol_ModalWindowDarkening', 'ImGuiCol_DragDropTarget'
	], 'int', namespace='')

	gen.bind_named_enum('ImGuiStyleVar', [
		'ImGuiStyleVar_Alpha', 'ImGuiStyleVar_WindowPadding', 'ImGuiStyleVar_WindowRounding', 'ImGuiStyleVar_WindowMinSize', 'ImGuiStyleVar_ChildRounding', 'ImGuiStyleVar_FramePadding',
		'ImGuiStyleVar_FrameRounding', 'ImGuiStyleVar_ItemSpacing', 'ImGuiStyleVar_ItemInnerSpacing', 'ImGuiStyleVar_IndentSpacing', 'ImGuiStyleVar_GrabMinSize', 'ImGuiStyleVar_ButtonTextAlign'
	], 'int', namespace='')

	#gen.bind_function('ImGui::GetIO', 'ImGuiIO &', [], bound_name='ImGuiGetIO')
	#gen.bind_function('ImGui::GetStyle', 'ImGuiStyle &', [], bound_name='ImGuiGetStyle')

	gen.bind_function('ImGui::NewFrame', 'void', [], bound_name='ImGuiNewFrame')
	gen.bind_function('ImGui::Render', 'void', [], bound_name='ImGuiRender')
	gen.bind_function('ImGui::Shutdown', 'void', [], bound_name='ImGuiShutdown')

	gen.bind_function_overloads('ImGui::Begin', [
		('bool', ['const char *name'], []),
		('bool', ['const char *name', 'bool *open', 'ImGuiWindowFlags flags'], {'arg_out': ['open']})
	], bound_name='ImGuiBegin')
	gen.bind_function('ImGui::End', 'void', [], bound_name='ImGuiEnd')

	gen.bind_function('ImGui::BeginChild', 'bool', ['const char *id', '?const ImVec2 &size', '?bool border', '?ImGuiWindowFlags extra_flags'], bound_name='ImGuiBeginChild')
	gen.bind_function('ImGui::EndChild', 'void', [], bound_name='ImGuiEndChild')

	gen.bind_function('ImGui::GetContentRegionMax', 'hg::tVector2<float>', [], bound_name='ImGuiGetContentRegionMax')
	gen.bind_function('ImGui::GetContentRegionAvail', 'hg::tVector2<float>', [], bound_name='ImGuiGetContentRegionAvail')
	gen.bind_function('ImGui::GetContentRegionAvailWidth', 'float', [], bound_name='ImGuiGetContentRegionAvailWidth')
	gen.bind_function('ImGui::GetWindowContentRegionMin', 'hg::tVector2<float>', [], bound_name='ImGuiGetWindowContentRegionMin')
	gen.bind_function('ImGui::GetWindowContentRegionMax', 'hg::tVector2<float>', [], bound_name='ImGuiGetWindowContentRegionMax')
	gen.bind_function('ImGui::GetWindowContentRegionWidth', 'float', [], bound_name='ImGuiGetWindowContentRegionWidth')
	#IMGUI_API ImDrawList*   GetWindowDrawList();                                                // get rendering command-list if you want to append your own draw primitives
	gen.bind_function('ImGui::GetWindowPos', 'hg::tVector2<float>', [], bound_name='ImGuiGetWindowPos')
	gen.bind_function('ImGui::GetWindowSize', 'hg::tVector2<float>', [], bound_name='ImGuiGetWindowSize')
	gen.bind_function('ImGui::GetWindowWidth', 'float', [], bound_name='ImGuiGetWindowWidth')
	gen.bind_function('ImGui::GetWindowHeight', 'float', [], bound_name='ImGuiGetWindowHeight')
	gen.bind_function('ImGui::IsWindowCollapsed', 'bool', [], bound_name='ImGuiIsWindowCollapsed')
	gen.bind_function('ImGui::SetWindowFontScale', 'void', ['float scale'], bound_name='ImGuiSetWindowFontScale')

	gen.bind_function('ImGui::SetNextWindowPos', 'void', ['const hg::tVector2<float> &pos', '?ImGuiCond condition'], bound_name='ImGuiSetNextWindowPos')
	gen.bind_function('ImGui::SetNextWindowPosCenter', 'void', ['?ImGuiCond condition'], bound_name='ImGuiSetNextWindowPosCenter')
	gen.bind_function('ImGui::SetNextWindowSize', 'void', ['const hg::tVector2<float> &size', '?ImGuiCond condition'], bound_name='ImGuiSetNextWindowSize')
	gen.bind_function('ImGui::SetNextWindowContentSize', 'void', ['const hg::tVector2<float> &size'], bound_name='ImGuiSetNextWindowContentSize')
	gen.bind_function('ImGui::SetNextWindowContentWidth', 'void', ['float width'], bound_name='ImGuiSetNextWindowContentWidth')
	gen.bind_function('ImGui::SetNextWindowCollapsed', 'void', ['bool collapsed', 'ImGuiCond condition'], bound_name='ImGuiSetNextWindowCollapsed')
	gen.bind_function('ImGui::SetNextWindowFocus', 'void', [], bound_name='ImGuiSetNextWindowFocus')
	gen.bind_function('ImGui::SetWindowPos', 'void', ['const hg::tVector2<float> &pos', '?ImGuiCond condition'], bound_name='ImGuiSetWindowPos')
	gen.bind_function('ImGui::SetWindowSize', 'void', ['const hg::tVector2<float> &size', '?ImGuiCond condition'], bound_name='ImGuiSetWindowSize')
	gen.bind_function('ImGui::SetWindowCollapsed', 'void', ['bool collapsed', '?ImGuiCond condition'], bound_name='ImGuiSetWindowCollapsed')
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
	gen.bind_function('ImGui::PushStyleColor', 'void', ['ImGuiCol idx', 'const hg::Color &color'], bound_name='ImGuiPushStyleColor')
	gen.bind_function('ImGui::PopStyleColor', 'void', ['?int count'], bound_name='ImGuiPopStyleColor')
	gen.bind_function_overloads('ImGui::PushStyleVar', [
		('void', ['ImGuiStyleVar idx', 'float value'], []),
		('void', ['ImGuiStyleVar idx', 'const hg::tVector2<float> &value'], [])
	], bound_name='ImGuiPushStyleVar')
	gen.bind_function('ImGui::PopStyleVar', 'void', ['?int count'], bound_name='ImGuiPopStyleVar')
	gen.bind_function('ImGui::GetFont', 'ImFont *', [], bound_name='ImGuiGetFont')
	gen.bind_function('ImGui::GetFontSize', 'float', [], bound_name='ImGuiGetFontSize')
	gen.bind_function('ImGui::GetFontTexUvWhitePixel', 'hg::tVector2<float>', [], bound_name='ImGuiGetFontTexUvWhitePixel')
	gen.bind_function_overloads('ImGui::GetColorU32', [
		('uint32_t', ['ImGuiCol idx', '?float alpha_multiplier'], []),
		('uint32_t', ['const hg::Color &color'], [])
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
	gen.bind_function('ImGui::Dummy', 'void', ['const hg::tVector2<float> &size'], bound_name='ImGuiDummy')
	gen.bind_function('ImGui::Indent', 'void', ['?float width'], bound_name='ImGuiIndent')
	gen.bind_function('ImGui::Unindent', 'void', ['?float width'], bound_name='ImGuiUnindent')
	gen.bind_function('ImGui::BeginGroup', 'void', [], bound_name='ImGuiBeginGroup')
	gen.bind_function('ImGui::EndGroup', 'void', [], bound_name='ImGuiEndGroup')
	gen.bind_function('ImGui::GetCursorPos', 'hg::tVector2<float>', [], bound_name='ImGuiGetCursorPos')
	gen.bind_function('ImGui::GetCursorPosX', 'float', [], bound_name='ImGuiGetCursorPosX')
	gen.bind_function('ImGui::GetCursorPosY', 'float', [], bound_name='ImGuiGetCursorPosY')
	gen.bind_function('ImGui::SetCursorPos', 'void', ['const hg::tVector2<float> &local_pos'], bound_name='ImGuiSetCursorPos')
	gen.bind_function('ImGui::SetCursorPosX', 'void', ['float x'], bound_name='ImGuiSetCursorPosX')
	gen.bind_function('ImGui::SetCursorPosY', 'void', ['float y'], bound_name='ImGuiSetCursorPosY')
	gen.bind_function('ImGui::GetCursorStartPos', 'hg::tVector2<float>', [], bound_name='ImGuiGetCursorStartPos')
	gen.bind_function('ImGui::GetCursorScreenPos', 'hg::tVector2<float>', [], bound_name='ImGuiGetCursorScreenPos')
	gen.bind_function('ImGui::SetCursorScreenPos', 'void', ['const hg::tVector2<float> &pos'], bound_name='ImGuiSetCursorScreenPos')
	gen.bind_function('ImGui::AlignTextToFramePadding', 'void', [], bound_name='ImGuiAlignTextToFramePadding')
	gen.bind_function('ImGui::GetTextLineHeight', 'float', [], bound_name='ImGuiGetTextLineHeight')
	gen.bind_function('ImGui::GetTextLineHeightWithSpacing', 'float', [], bound_name='ImGuiGetTextLineHeightWithSpacing')
	gen.bind_function('ImGui::GetFrameHeightWithSpacing', 'float', [], bound_name='ImGuiGetFrameHeightWithSpacing')

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
	gen.bind_function('ImGui::TextColored', 'void', ['const hg::Color &color', 'const char *text'], bound_name='ImGuiTextColored')
	gen.bind_function('ImGui::TextDisabled', 'void', ['const char *text'], bound_name='ImGuiTextDisabled')
	gen.bind_function('ImGui::TextWrapped', 'void', ['const char *text'], bound_name='ImGuiTextWrapped')
	gen.bind_function('ImGui::TextUnformatted', 'void', ['const char *text'], bound_name='ImGuiTextUnformatted')
	gen.bind_function('ImGui::LabelText', 'void', ['const char *label', 'const char *text'], bound_name='ImGuiLabelText')
	gen.bind_function('ImGui::Bullet', 'void', [], bound_name='ImGuiBullet')
	gen.bind_function('ImGui::BulletText', 'void', ['const char *label'], bound_name='ImGuiBulletText')
	gen.bind_function('ImGui::Button', 'bool', ['const char *label', '?const hg::tVector2<float> &size'], bound_name='ImGuiButton')
	gen.bind_function('ImGui::SmallButton', 'bool', ['const char *label'], bound_name='ImGuiSmallButton')
	gen.bind_function('ImGui::InvisibleButton', 'bool', ['const char *text', 'const hg::tVector2<float> &size'], bound_name='ImGuiInvisibleButton')

	gen.bind_function('ImGui::Image', 'void', ['hg::Texture *texture', 'const hg::tVector2<float> &size', '?const hg::tVector2<float> &uv0', '?const hg::tVector2<float> &uv1', '?const hg::Color &tint_col', '?const hg::Color &border_col'], bound_name='ImGuiImage')
	gen.bind_function('ImGui::ImageButton', 'bool', ['hg::Texture *texture', 'const hg::tVector2<float> &size', '?const hg::tVector2<float> &uv0', '?const hg::tVector2<float> &uv1', '?int frame_padding', '?const hg::Color &bg_col', '?const hg::Color &tint_col'], bound_name='ImGuiImageButton')

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
	return ImGui::Combo(label, current_item, item_cb, (void *)&items, hg::numeric_cast<int>(items.size()), height_in_items);
}

static bool _ImGuiColorButton(const char *id, hg::Color &color, ImGuiColorEditFlags flags = 0, const hg::tVector2<float> &size = hg::tVector2<float>(0, 0)) { return ImGui::ColorButton(id, *(ImVec4 *)&color, flags, size); }
static bool _ImGuiColorEdit(const char *label, hg::Color &color, ImGuiColorEditFlags flags = 0) { return ImGui::ColorEdit4(label, &color.r, flags); }
static void _ImGuiProgressBar(float fraction, const hg::tVector2<float> &size = hg::tVector2<float>(-1, 0), const char *overlay = nullptr) { ImGui::ProgressBar(fraction, size, overlay); }
''')

	imgui_combo_protos = [('bool', ['const char *label', 'int *current_item', 'const std::vector<std::string> &items', '?int height_in_items'], {'arg_in_out': ['current_item']})]
	if gen.get_language() == "CPython":
		imgui_combo_protos += [('bool', ['const char *label', 'int *current_item', 'PySequenceOfString items', '?int height_in_items'], {'arg_in_out': ['current_item']})]
	gen.bind_function_overloads('_ImGuiCombo', imgui_combo_protos, bound_name='ImGuiCombo')

	gen.bind_function('_ImGuiColorButton', 'bool', ['const char *id', 'hg::Color &color', '?ImGuiColorEditFlags flags', '?const hg::tVector2<float> &size'], {'arg_in_out': ['color']}, bound_name='ImGuiColorButton')
	gen.bind_function('_ImGuiColorEdit', 'bool', ['const char *label', 'hg::Color &color', '?ImGuiColorEditFlags flags'], {'arg_in_out': ['color']}, bound_name='ImGuiColorEdit')
	gen.bind_function('_ImGuiProgressBar', 'void', ['float fraction', '?const hg::tVector2<float> &size', '?const char *overlay'], bound_name='ImGuiProgressBar')

	gen.insert_binding_code('''\
static bool _ImGuiDragiVector2(const char *label, hg::tVector2<int> &v, float v_speed = 1.f, int v_min = 0, int v_max = 0) { return ImGui::DragInt2(label, &v.x, v_speed, v_min, v_max); }

static bool _ImGuiDragVector2(const char *label, hg::tVector2<float> &v, float v_speed = 1.f, float v_min = 0.f, float v_max = 0.f) { return ImGui::DragFloat2(label, &v.x, v_speed, v_min, v_max); }
static bool _ImGuiDragVector3(const char *label, hg::Vector3 &v, float v_speed = 1.f, float v_min = 0.f, float v_max = 0.f) { return ImGui::DragFloat3(label, &v.x, v_speed, v_min, v_max); }
static bool _ImGuiDragVector4(const char *label, hg::Vector4 &v, float v_speed = 1.f, float v_min = 0.f, float v_max = 0.f) { return ImGui::DragFloat4(label, &v.x, v_speed, v_min, v_max); }
''')

	gen.bind_function_overloads('ImGui::DragFloat', [
		('bool', ['const char *label', 'float *v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float v_speed', 'float v_min', 'float v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragFloat')
	gen.bind_function_overloads('_ImGuiDragVector2', [
		('bool', ['const char *label', 'hg::tVector2<float> &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::tVector2<float> &v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::tVector2<float> &v', 'float v_speed', 'float v_min', 'float v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragVector2')
	gen.bind_function_overloads('_ImGuiDragVector3', [
		('bool', ['const char *label', 'hg::Vector3 &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::Vector3 &v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::Vector3 &v', 'float v_speed', 'float v_min', 'float v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragVector3')
	gen.bind_function_overloads('_ImGuiDragVector4', [
		('bool', ['const char *label', 'hg::Vector4 &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::Vector4 &v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::Vector4 &v', 'float v_speed', 'float v_min', 'float v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragVector4')

	gen.bind_function_overloads('_ImGuiDragiVector2', [
		('bool', ['const char *label', 'hg::tVector2<int> &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::tVector2<int> &v', 'float v_speed'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::tVector2<int> &v', 'float v_speed', 'int v_min', 'int v_max'], {'arg_in_out': ['v']})
	], bound_name='ImGuiDragIntVector2')

	#IMGUI_API bool InputText(const char* label, char* buf, size_t buf_size, ImGuiInputTextFlags flags = 0, ImGuiTextEditCallback callback = NULL, void* user_data = NULL);
	#IMGUI_API bool InputTextMultiline(const char* label, char* buf, size_t buf_size, const ImVec2& size = ImVec2(0,0), ImGuiInputTextFlags flags = 0, ImGuiTextEditCallback callback = NULL, void* user_data = NULL);

	gen.insert_binding_code('''\
static bool _ImGuiInputiVector2(const char *label, hg::tVector2<int> &v, ImGuiInputTextFlags extra_flags = 0) { return ImGui::InputInt2(label, &v.x, extra_flags); }

static bool _ImGuiInputVector2(const char *label, hg::tVector2<float> &v, int decimal_precision = -1, ImGuiInputTextFlags extra_flags = 0) { return ImGui::InputFloat2(label, &v.x, decimal_precision, extra_flags); }
static bool _ImGuiInputVector3(const char *label, hg::Vector3 &v, int decimal_precision = -1, ImGuiInputTextFlags extra_flags = 0) { return ImGui::InputFloat3(label, &v.x, decimal_precision, extra_flags); }
static bool _ImGuiInputVector4(const char *label, hg::Vector4 &v, int decimal_precision = -1, ImGuiInputTextFlags extra_flags = 0) { return ImGui::InputFloat4(label, &v.x, decimal_precision, extra_flags); }
''')

	gen.bind_function_overloads('ImGui::InputFloat', [
		('bool', ['const char *label', 'float *v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float step', 'float step_fast'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float step', 'float step_fast', 'int decimal_precision'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'float *v', 'float step', 'float step_fast', 'int decimal_precision', 'ImGuiInputTextFlags extra_flags'], {'arg_in_out': ['v']})
	], bound_name='ImGuiInputFloat')
	gen.bind_function_overloads('_ImGuiInputVector2', [
		('bool', ['const char *label', 'hg::tVector2<float> &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::tVector2<float> &v', 'int decimal_precision'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::tVector2<float> &v', 'int decimal_precision', 'ImGuiInputTextFlags extra_flags'], {'arg_in_out': ['v']})
	], bound_name='ImGuiInputVector2')
	gen.bind_function_overloads('_ImGuiInputVector3', [
		('bool', ['const char *label', 'hg::Vector3 &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::Vector3 &v', 'int decimal_precision'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::Vector3 &v', 'int decimal_precision', 'ImGuiInputTextFlags extra_flags'], {'arg_in_out': ['v']})
	], bound_name='ImGuiInputVector3')
	gen.bind_function_overloads('_ImGuiInputVector4', [
		('bool', ['const char *label', 'hg::Vector4 &v'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::Vector4 &v', 'int decimal_precision'], {'arg_in_out': ['v']}),
		('bool', ['const char *label', 'hg::Vector4 &v', 'int decimal_precision', 'ImGuiInputTextFlags extra_flags'], {'arg_in_out': ['v']})
	], bound_name='ImGuiInputVector4')

	gen.insert_binding_code('''\
static bool _ImGuiSliderFloat(const char *label, float &v, float v_min, float v_max) { return ImGui::SliderFloat(label, &v, v_min, v_max); }

static bool _ImGuiSlideriVector2(const char *label, hg::tVector2<int> &v, int v_min, int v_max) { return ImGui::SliderInt2(label, &v.x, v_min, v_max); }

static bool _ImGuiSliderVector2(const char *label, hg::tVector2<float> &v, float v_min, float v_max) { return ImGui::SliderFloat2(label, &v.x, v_min, v_max); }
static bool _ImGuiSliderVector3(const char *label, hg::Vector3 &v, float v_min, float v_max) { return ImGui::SliderFloat3(label, &v.x, v_min, v_max); }
static bool _ImGuiSliderVector4(const char *label, hg::Vector4 &v, float v_min, float v_max) { return ImGui::SliderFloat4(label, &v.x, v_min, v_max); }
''')
	
	gen.bind_function('_ImGuiSliderFloat', 'bool', ['const char *label', 'float &v', 'float v_min', 'float v_max'], {'arg_in_out': ['v']}, 'ImGuiSliderFloat')

	gen.bind_function('_ImGuiSlideriVector2', 'bool', ['const char *label', 'hg::tVector2<int> &v', 'int v_min', 'int v_max'], {'arg_in_out': ['v']}, 'ImGuiSliderIntVector2')

	gen.bind_function('_ImGuiSliderVector2', 'bool', ['const char *label', 'hg::tVector2<float> &v', 'float v_min', 'float v_max'], {'arg_in_out': ['v']}, 'ImGuiSliderVector2')
	gen.bind_function('_ImGuiSliderVector3', 'bool', ['const char *label', 'hg::Vector3 &v', 'float v_min', 'float v_max'], {'arg_in_out': ['v']}, 'ImGuiSliderVector3')
	gen.bind_function('_ImGuiSliderVector4', 'bool', ['const char *label', 'hg::Vector4 &v', 'float v_min', 'float v_max'], {'arg_in_out': ['v']}, 'ImGuiSliderVector4')

	gen.bind_function('ImGui::TreeNode', 'bool', ['const char *label'], bound_name='ImGuiTreeNode')
	gen.bind_function('ImGui::TreeNodeEx', 'bool', ['const char *label', 'ImGuiTreeNodeFlags flags'], bound_name='ImGuiTreeNodeEx')
	gen.bind_function('ImGui::TreePush', 'void', ['const char *id'], bound_name='ImGuiTreePush')
	gen.bind_function('ImGui::TreePop', 'void', [], bound_name='ImGuiTreePop')
	gen.bind_function('ImGui::TreeAdvanceToLabelPos', 'void', [], bound_name='ImGuiTreeAdvanceToLabelPos')
	gen.bind_function('ImGui::GetTreeNodeToLabelSpacing', 'float', [], bound_name='ImGuiGetTreeNodeToLabelSpacing')
	gen.bind_function('ImGui::SetNextTreeNodeOpen', 'void', ['bool is_open', '?ImGuiCond condition'], bound_name='ImGuiSetNextTreeNodeOpen')
	gen.bind_function_overloads('ImGui::CollapsingHeader', [
		('bool', ['const char *label', '?ImGuiTreeNodeFlags flags'], []),
		('bool', ['const char *label', 'bool *p_open', '?ImGuiTreeNodeFlags flags'], {'arg_in_out': ['p_open']})
	], bound_name='ImGuiCollapsingHeader')

	gen.insert_binding_code('''\
static bool _ImGuiSelectable(const char *label, bool selected = false, ImGuiSelectableFlags flags = 0, const hg::tVector2<float> &size = hg::tVector2<float>(0.f, 0.f)) { return ImGui::Selectable(label, selected, flags, ImVec2(size)); }

static bool _ImGuiListBox(const char *label, int *current_item, const std::vector<std::string> &items, int height_in_items = -1) {
	auto cb = [](void *data, int idx, const char **out) -> bool {
		auto &items = *(const std::vector<std::string> *)data;
		if (size_t(idx) >= items.size())
			return false;
		*out = items[idx].c_str();
		return true;
	};
	return ImGui::ListBox(label, current_item, cb, (void *)&items, hg::numeric_cast<int>(items.size()), height_in_items);
}
''')

	gen.bind_function('_ImGuiSelectable', 'bool', ['const char *label', '?bool selected', '?ImGuiSelectableFlags flags', '?const hg::tVector2<float> &size'], bound_name='ImGuiSelectable')
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
	gen.bind_function('ImGui::BeginPopupContextWindow', 'bool', ['?const char *id', '?int mouse_button', '?bool also_over_items'], bound_name='ImGuiBeginPopupContextWindow')
	gen.bind_function('ImGui::BeginPopupContextVoid', 'bool', ['?const char *id', '?int mouse_button'], bound_name='ImGuiBeginPopupContextVoid')
	gen.bind_function('ImGui::EndPopup', 'void', [], bound_name='ImGuiEndPopup')
	gen.bind_function('ImGui::CloseCurrentPopup', 'void', [], bound_name='ImGuiCloseCurrentPopup')

	gen.insert_binding_code('''\
static void _ImGuiPushClipRect(const hg::tVector2<float> &clip_rect_min, const hg::tVector2<float> &clip_rect_max, bool intersect_with_current_clip_rect) {
	ImGui::PushClipRect(ImVec2(clip_rect_min), ImVec2(clip_rect_max), intersect_with_current_clip_rect);
}

static hg::tVector2<float> _ImGuiGetItemRectMin() { return hg::tVector2<float>(ImGui::GetItemRectMin()); }
static hg::tVector2<float> _ImGuiGetItemRectMax() { return hg::tVector2<float>(ImGui::GetItemRectMax()); }
static hg::tVector2<float> _ImGuiGetItemRectSize() { return hg::tVector2<float>(ImGui::GetItemRectSize()); }

static bool _ImGuiIsRectVisible(const hg::tVector2<float> &size) { return ImGui::IsRectVisible(size); }
static bool _ImGuiIsRectVisible(const hg::tVector2<float> &min, const hg::tVector2<float> &max) { return ImGui::IsRectVisible(min, max); }

static hg::Vector2 _ImGuiCalcItemRectClosestPoint(const hg::Vector2 &pos, bool on_edge = false, float outward = 0.f) { return ImGui::CalcItemRectClosestPoint(pos, on_edge, outward); }
static hg::Vector2 _ImGuiCalcTextSize(const char *text, bool hide_text_after_double_dash = false, float wrap_width = -1.f) { return ImGui::CalcTextSize(text, NULL, hide_text_after_double_dash, wrap_width); }
''')
	gen.bind_function('_ImGuiPushClipRect', 'void', ['const hg::tVector2<float> &clip_rect_min', 'const hg::tVector2<float> &clip_rect_max', 'bool intersect_with_current_clip_rect'], bound_name='ImGuiPushClipRect')
	gen.bind_function('ImGui::PopClipRect', 'void', [], bound_name='ImGuiPopClipRect')

	gen.bind_function('ImGui::IsItemHovered', 'bool', ['?ImGuiHoveredFlags flags'], bound_name='ImGuiIsItemHovered')
	gen.bind_function('ImGui::IsItemActive', 'bool', [], bound_name='ImGuiIsItemActive')
	gen.bind_function('ImGui::IsItemClicked', 'bool', ['?int mouse_button'], bound_name='ImGuiIsItemClicked')
	gen.bind_function('ImGui::IsItemVisible', 'bool', [], bound_name='ImGuiIsItemVisible')
	gen.bind_function('ImGui::IsAnyItemHovered', 'bool', [], bound_name='ImGuiIsAnyItemHovered')
	gen.bind_function('ImGui::IsAnyItemActive', 'bool', [], bound_name='ImGuiIsAnyItemActive')
	gen.bind_function('_ImGuiGetItemRectMin', 'hg::tVector2<float>', [], bound_name='ImGuiGetItemRectMin')
	gen.bind_function('_ImGuiGetItemRectMax', 'hg::tVector2<float>', [], bound_name='ImGuiGetItemRectMax')
	gen.bind_function('_ImGuiGetItemRectSize', 'hg::tVector2<float>', [], bound_name='ImGuiGetItemRectSize')
	gen.bind_function('ImGui::SetItemAllowOverlap', 'void', [], bound_name='ImGuiSetItemAllowOverlap')
	gen.bind_function('ImGui::IsWindowHovered', 'bool', ['?ImGuiHoveredFlags flags'], bound_name='ImGuiIsWindowHovered')
	gen.bind_function('ImGui::IsWindowFocused', 'bool', ['?ImGuiFocusedFlags flags'], bound_name='ImGuiIsWindowFocused')
	gen.bind_function_overloads('ImGui::IsRectVisible', [
		('bool', ['const hg::tVector2<float> &size'], []),
		('bool', ['const hg::tVector2<float> &rect_min', 'const hg::tVector2<float> &rect_max'], [])
	], bound_name='ImGuiIsRectVisible')
	gen.bind_function('ImGui::GetTime', 'float', [], bound_name='ImGuiGetTime')
	gen.bind_function('ImGui::GetFrameCount', 'int', [], bound_name='ImGuiGetFrameCount')
	#IMGUI_API const char*   GetStyleColName(ImGuiCol idx);
	gen.bind_function('_ImGuiCalcItemRectClosestPoint', 'hg::tVector2<float>', ['const hg::tVector2<float> &pos', '?bool on_edge', '?float outward'], bound_name='ImGuiCalcItemRectClosestPoint')
	gen.bind_function('_ImGuiCalcTextSize', 'hg::tVector2<float>', ['const char *text', '?bool hide_text_after_double_dash', '?float wrap_width'], bound_name='ImGuiCalcTextSize')

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
	#gen.bind_function('ImGui::IsWindowRectHovered', 'bool', [], bound_name='ImGuiIsWindowRectHovered')
	gen.bind_function('ImGui::IsAnyWindowHovered', 'bool', [], bound_name='ImGuiIsAnyWindowHovered')
	gen.bind_function('ImGui::IsMouseHoveringRect', 'bool', ['const hg::tVector2<float> &rect_min', 'const hg::tVector2<float> &rect_max', '?bool clip'], bound_name='ImGuiIsMouseHoveringRect')
	gen.bind_function('ImGui::IsMouseDragging', 'bool', ['?int button', '?float lock_threshold'], bound_name='ImGuiIsMouseDragging')
	gen.bind_function('ImGui::GetMousePos', 'hg::tVector2<float>', [], bound_name='ImGuiGetMousePos')
	gen.bind_function('ImGui::GetMousePosOnOpeningCurrentPopup', 'hg::tVector2<float>', [], bound_name='ImGuiGetMousePosOnOpeningCurrentPopup')
	gen.bind_function('ImGui::GetMouseDragDelta', 'hg::tVector2<float>', ['?int button', '?float lock_threshold'], bound_name='ImGuiGetMouseDragDelta')
	gen.bind_function('ImGui::ResetMouseDragDelta', 'void', ['?int button'], bound_name='ImGuiResetMouseDragDelta')
	#IMGUI_API ImGuiMouseCursor GetMouseCursor();                                                // get desired cursor type, reset in ImGui::NewFrame(), this updated during the frame. valid before Render(). If you use software rendering by setting io.MouseDrawCursor ImGui will render those for you
	#IMGUI_API void          SetMouseCursor(ImGuiMouseCursor type);                              // set desired cursor type
	gen.bind_function('ImGui::CaptureKeyboardFromApp', 'void', ['bool capture'], bound_name='ImGuiCaptureKeyboardFromApp')
	gen.bind_function('ImGui::CaptureMouseFromApp', 'void', ['bool capture'], bound_name='ImGuiCaptureMouseFromApp')

	gen.insert_binding_code('static bool _ImGuiWantCaptureMouse() { return ImGui::GetIO().WantCaptureMouse; }')    
	gen.bind_function('_ImGuiWantCaptureMouse', 'bool', [], bound_name='ImGuiWantCaptureMouse')
	
	gen.bind_function('hg::ImGuiSetOutputSurface', 'void', ['const hg::Surface &surface'], bound_name='ImGuiSetOutputSurface')

	gen.add_include('engine/imgui_renderer_hook.h')

	gen.bind_function('hg::ImGuiLock', 'void', [], {'exception': 'double lock from the same thread, check your program for a missing unlock'})
	gen.bind_function('hg::ImGuiUnlock', 'void', [])


def bind_lua_task_system(gen):
	gen.add_include('engine/lua_task_system.h')

	gen.bind_named_enum('hg::LuaTaskState', ['LuaTaskPending', 'LuaTaskRunning', 'LuaTaskComplete', 'LuaTaskFailed'])

	#
	lua_task_hnd = gen.begin_class('hg::LuaTaskHandle', bound_name='LuaTaskHandle_nobind', noncopyable=True, nobind=True)
	gen.end_class(lua_task_hnd)

	shared_lua_task_hnd = gen.begin_class('std::shared_ptr<hg::LuaTaskHandle>', bound_name='LuaTaskHandle', features={'proxy': lib.stl.SharedPtrProxyFeature(lua_task_hnd)})

	gen.bind_method(shared_lua_task_hnd, 'GetState', 'hg::LuaTaskState', [], ['proxy'])
	gen.bind_method(shared_lua_task_hnd, 'IsCompleteOrFailed', 'bool', [], ['proxy'])

	gen.bind_method(shared_lua_task_hnd, 'GetResults', 'std::vector<hg::TypeValue>', [], ['proxy'])

	gen.end_class(shared_lua_task_hnd)

	#
	lua_task = gen.begin_class('hg::LuaTask', bound_name='LuaTask_nobind', noncopyable=True, nobind=True)
	gen.end_class(lua_task)

	shared_lua_task = gen.begin_class('std::shared_ptr<hg::LuaTask>', bound_name='LuaTask', features={'proxy': lib.stl.SharedPtrProxyFeature(lua_task)})
	gen.end_class(shared_lua_task)

	#
	lua_ts = gen.begin_class('hg::LuaTaskSystem', bound_name='LuaTaskSystem_nobind', noncopyable=True, nobind=True)
	gen.end_class(lua_ts)

	shared_lua_ts = gen.begin_class('std::shared_ptr<hg::LuaTaskSystem>', bound_name='LuaTaskSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(lua_ts)})

	gen.bind_constructor(shared_lua_ts, [], ['proxy'])

	gen.bind_method(shared_lua_ts, 'Start', 'bool', ['?size_t worker_count'], ['proxy'])
	gen.bind_method(shared_lua_ts, 'Stop', 'void', [], ['proxy'])

	gen.bind_method(shared_lua_ts, 'PrepareTask', 'std::shared_ptr<hg::LuaTask>', ['const std::string &source', 'const std::string &name'], ['proxy'])
	gen.bind_method(shared_lua_ts, 'RunTask', 'std::shared_ptr<hg::LuaTaskHandle>', ['std::shared_ptr<hg::LuaTask> task', 'const std::vector<hg::TypeValue> &args'], ['proxy'])

	gen.bind_method(shared_lua_ts, 'GetWorkerCount', 'size_t', [], ['proxy'])

	gen.end_class(shared_lua_ts)


def bind_fast_noise(gen):
	gen.add_include('FastNoise.h')

	gen.bind_named_enum('FastNoise::NoiseType', ['Value', 'ValueFractal', 'Gradient', 'GradientFractal', 'Simplex', 'SimplexFractal', 'Cellular', 'WhiteNoise'], prefix='NoiseType')
	gen.bind_named_enum('FastNoise::Interp', ['InterpLinear', 'InterpHermite', 'InterpQuintic'], prefix='Noise')
	gen.bind_named_enum('FastNoise::FractalType', ['FBM', 'Billow', 'RigidMulti'], prefix='NoiseFractalType')
	gen.bind_named_enum('FastNoise::CellularDistanceFunction', ['Euclidean', 'Manhattan', 'Natural'], prefix='NoiseCellularDistance')
	gen.bind_named_enum('FastNoise::CellularReturnType', ['CellValue', 'NoiseLookup', 'Distance', 'Distance2', 'Distance2Add', 'Distance2Sub', 'Distance2Mul', 'Distance2Div'], prefix='NoiseCellularReturn')

	noise = gen.begin_class('FastNoise')

	gen.bind_constructor(noise, ['?int seed'])

	gen.bind_method(noise, 'SetSeed', 'void', ['int seed'])
	gen.bind_method(noise, 'GetSeed', 'int', [])
	
	gen.bind_method(noise, 'SetFrequency', 'void', ['float fq'])
	gen.bind_method(noise, 'SetInterp', 'void', ['FastNoise::Interp interp'])
	gen.bind_method(noise, 'SetNoiseType', 'void', ['FastNoise::NoiseType type'])

	gen.bind_method(noise, 'SetFractalOctaves', 'void', ['unsigned int octaves'])
	gen.bind_method(noise, 'SetFractalLacunarity', 'void', ['float lacunarity'])
	gen.bind_method(noise, 'SetFractalGain', 'void', ['float gain'])
	gen.bind_method(noise, 'SetFractalType', 'void', ['FastNoise::FractalType type'])

	gen.bind_method(noise, 'SetCellularDistanceFunction', 'void', ['FastNoise::CellularDistanceFunction function'])
	gen.bind_method(noise, 'SetCellularReturnType', 'void', ['FastNoise::CellularReturnType type'])

	gen.bind_method(noise, 'GetValue', 'float', ['float x', 'float y', '?float z'])
	gen.bind_method(noise, 'GetValueFractal', 'float', ['float x', 'float y', '?float z'])

	gen.bind_method(noise, 'GetGradient', 'float', ['float x', 'float y', '?float z'])
	gen.bind_method(noise, 'GetGradientFractal', 'float', ['float x', 'float y', '?float z'])

	gen.bind_method(noise, 'GetSimplex', 'float', ['float x', 'float y', '?float z', '?float w'])
	gen.bind_method(noise, 'GetSimplexFractal', 'float', ['float x', 'float y', '?float z'])

	gen.bind_method(noise, 'GetCellular', 'float', ['float x', 'float y', '?float z'])

	gen.bind_method(noise, 'GetWhiteNoise', 'float', ['float x', 'float y', '?float z', '?float w'])
	gen.bind_method(noise, 'GetWhiteNoiseInt', 'float', ['int x', 'int y', '?int z', '?int w'])

	gen.bind_method(noise, 'GetNoise', 'float', ['float x', 'float y', '?float z'])

	gen.end_class(noise)


def bind_extras(gen):
	gen.add_include('thread', True)
	gen.add_include('foundation/time_chrono.h')

	gen.insert_binding_code('static void SleepThisThread(hg::time_ns duration) { std::this_thread::sleep_for(hg::time_to_chrono(duration)); }\n\n')
	gen.bind_function('SleepThisThread', 'void', ['hg::time_ns duration'], bound_name='Sleep')


def bind(gen):
	gen.start('harfang')

	lib.bind_defaults(gen)

	gen.add_include('foundation/cext.h')

	gen.add_include('engine/engine.h')
	gen.add_include('engine/factories.h')
	gen.add_include('engine/plugin_system.h')

	if gen.get_language() == 'CPython':
		gen.insert_binding_code('''
// Add the Python interpreter module search paths to the engine default plugins search path
void InitializePluginsDefaultSearchPath() {
	if (PyObject *sys_path = PySys_GetObject("path")) {
		if (PyList_Check(sys_path)) {
			Py_ssize_t n = PyList_Size(sys_path);
			for (Py_ssize_t i = 0; i < n; ++i)
				if (PyObject *path = PyList_GetItem(sys_path, i))
					if (PyObject *tmp = PyUnicode_AsUTF8String(path)) {
						std::string path(PyBytes_AsString(tmp));
						hg::g_plugin_system.get().default_search_paths.push_back(path + "/harfang");
					}
		}
	}
}
\n''')
	elif gen.get_language() == 'Lua':
		gen.insert_binding_code('''
#include "foundation/string.h"

// Add the Lua interpreter package.cpath to the engine default plugins search path
static void InitializePluginsDefaultSearchPath(lua_State *L) {
	lua_getglobal(L, "package");
	lua_getfield(L, -1, "cpath");
	std::string package_cpath = lua_tostring(L, -1);
	lua_pop(L, 2);

	std::vector<std::string> paths = hg::split(package_cpath, ";"), out;

	for (size_t i = 0; i < paths.size(); ++i) {
		std::string path = paths[i];
		std::replace(path.begin(), path.end(), '\\\\', '/');

		std::vector<std::string> elms = hg::split(path, "/");
		path = "";
		for (auto &elm : elms)
			if (elm.find('?') == std::string::npos)
				path += elm + "/";

		if (path == "./")
			continue;
		if (hg::ends_with(path, "loadall.dll/"))
			continue;

		out.push_back(path);
	}

	for (auto &path : out)
		hg::g_plugin_system.get().default_search_paths.push_back(path);
}
\n''')

	# setup/free code only for non embedded binding
	if not gen.embedded:
		init_plugins_parm = ''
		if gen.get_language() == 'Lua':
			init_plugins_parm = 'L'

		gen.add_custom_init_code('''\
	hg::Init();
	InitializePluginsDefaultSearchPath(%s);
\n''' % init_plugins_parm)

		gen.add_custom_free_code('hg::Uninit();\n')

	void_ptr = gen.bind_ptr('void *', bound_name='VoidPointer')

	gen.typedef('uint32_t', 'unsigned int')

	lib.stl.bind_future_T(gen, 'void', 'FutureVoid')
	lib.stl.bind_future_T(gen, 'bool', 'FutureBool')
	lib.stl.bind_future_T(gen, 'int', 'FutureInt')
	lib.stl.bind_future_T(gen, 'float', 'FutureFloat')

	lib.stl.bind_future_T(gen, 'uint32_t', 'FutureUInt')
	lib.stl.bind_future_T(gen, 'size_t', 'FutureSize')

	bind_std_vector(gen, gen.get_conv('char'))
	bind_std_vector(gen, gen.get_conv('int'))
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

	bind_task_system(gen)
	bind_log(gen)
	bind_binary_data(gen)
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
	bind_movie(gen)
	bind_scene(gen)
	bind_input(gen)
	bind_plus(gen)
	bind_imgui(gen)
	bind_platform(gen)
	bind_lua_task_system(gen)
	bind_fast_noise(gen)
	bind_extras(gen)

	gen.finalize()
