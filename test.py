import lua
import python

import lib.std
import lib.stl


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

	gen.bind_method(binary_blob, 'Write<int8_t>', 'void', ['const int8_t &v'], bound_name='WriteInt8')
	gen.bind_method(binary_blob, 'Write<int16_t>', 'void', ['const int16_t &v'], bound_name='WriteInt16')
	gen.bind_method(binary_blob, 'Write<int32_t>', 'void', ['const int32_t &v'], bound_name='WriteInt32')
	gen.bind_method(binary_blob, 'Write<int64_t>', 'void', ['const int64_t &v'], bound_name='WriteInt64')
	gen.bind_method(binary_blob, 'Write<uint8_t>', 'void', ['const uint8_t &v'], bound_name='WriteUInt8')
	gen.bind_method(binary_blob, 'Write<uint16_t>', 'void', ['const uint16_t &v'], bound_name='WriteUInt16')
	gen.bind_method(binary_blob, 'Write<uint32_t>', 'void', ['const uint32_t &v'], bound_name='WriteUInt32')
	gen.bind_method(binary_blob, 'Write<uint64_t>', 'void', ['const uint64_t &v'], bound_name='WriteUInt64')
	gen.bind_method(binary_blob, 'Write<float>', 'void', ['const float &v'], bound_name='WriteFloat')
	gen.bind_method(binary_blob, 'Write<double>', 'void', ['const double &v'], bound_name='WriteDouble')

	gen.bind_method(binary_blob, 'WriteAt<int8_t>', 'void', ['const int8_t &v', 'size_t position'], bound_name='WriteInt8At')
	gen.bind_method(binary_blob, 'WriteAt<int16_t>', 'void', ['const int16_t &v', 'size_t position'], bound_name='WriteInt16At')
	gen.bind_method(binary_blob, 'WriteAt<int32_t>', 'void', ['const int32_t &v', 'size_t position'], bound_name='WriteInt32At')
	gen.bind_method(binary_blob, 'WriteAt<int64_t>', 'void', ['const int64_t &v', 'size_t position'], bound_name='WriteInt64At')
	gen.bind_method(binary_blob, 'WriteAt<uint8_t>', 'void', ['const uint8_t &v', 'size_t position'], bound_name='WriteUInt8At')
	gen.bind_method(binary_blob, 'WriteAt<uint16_t>', 'void', ['const uint16_t &v', 'size_t position'], bound_name='WriteUInt16At')
	gen.bind_method(binary_blob, 'WriteAt<uint32_t>', 'void', ['const uint32_t &v', 'size_t position'], bound_name='WriteUInt32At')
	gen.bind_method(binary_blob, 'WriteAt<uint64_t>', 'void', ['const uint64_t &v', 'size_t position'], bound_name='WriteUInt64At')
	gen.bind_method(binary_blob, 'WriteAt<float>', 'void', ['const float &v', 'size_t position'], bound_name='WriteFloatAt')
	gen.bind_method(binary_blob, 'WriteAt<double>', 'void', ['const double &v', 'size_t position'], bound_name='WriteDoubleAt')

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

	#
	input_device = gen.begin_class('gs::InputDevice', bound_name='InputDevice_hide_me', noncopyable=True, nobind=False)
	gen.end_class(input_device)

	shared_input_device = gen.begin_class('std::shared_ptr<gs::InputDevice>', bound_name='InputDevice', features={'proxy': lib.stl.SharedPtrProxyFeature(input_device)})
	gen.end_class(shared_input_device)


def bind_engine(gen):
	gen.add_include('engine/engine.h')

	gen.bind_function('gs::core::GetExecutablePath', 'std::string', [])

	gen.bind_function('gs::core::EndFrame', 'void', [])

	gen.bind_function('gs::core::GetLastFrameDuration', 'gs::time_ns', [])
	gen.bind_function('gs::core::ResetLastFrameDuration', 'void', [])


def bind_plugins(gen):
	gen.bind_function_overloads('gs::core::LoadPlugins', [('gs::uint', [], []), ('gs::uint', ['const char *path'], [])])
	gen.bind_function('gs::core::UnloadPlugins', 'void', [])


def bind_window_system(gen):
	gen.add_include('platform/window_system.h')

	# gs::Surface
	surface = gen.begin_class('gs::Surface')
	gen.end_class(surface)

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

	#std::vector<Monitor> GetMonitors();

	gen.bind_function('gs::GetWindowPos', 'gs::tVector2<int>', ['const gs::Window &window'])
	gen.bind_function('gs::SetWindowPos', 'bool', ['const gs::Window &window', 'const gs::tVector2<int> position'])


def bind_core(gen):
	# gs::core::Material
	gen.add_include('engine/material.h')

	material = gen.begin_class('gs::core::Material', bound_name='Material_hide_me', noncopyable=True, nobind=True)
	gen.end_class(material)

	shared_material = gen.begin_class('std::shared_ptr<gs::core::Material>', bound_name='Material', features={'proxy': lib.stl.SharedPtrProxyFeature(material)})
	gen.bind_members(shared_material, ['std::string name', 'std::string shader'], ['proxy'])
	gen.end_class(shared_material)

	# gs::core::Geometry
	gen.add_include('engine/geometry.h')

	geometry = gen.begin_class('gs::core::Geometry', bound_name='Geometry_hide_me', noncopyable=True, nobind=True)
	gen.end_class(geometry)

	shared_geometry = gen.begin_class('std::shared_ptr<gs::core::Geometry>', bound_name='Geometry', features={'proxy': lib.stl.SharedPtrProxyFeature(geometry)})
	gen.end_class(shared_geometry)


def bind_scene(gen):
	gen.add_include('engine/scene.h')

	# forward declarations
	scene = gen.begin_class('gs::core::Scene', bound_name='Scene_hide_me', noncopyable=True, nobind=True)
	gen.end_class(scene)

	shared_scene = gen.begin_class('std::shared_ptr<gs::core::Scene>', bound_name='Scene', features={'proxy': lib.stl.SharedPtrProxyFeature(scene)})

	#
	def decl_get_set_method(clss, type, method_suffix, var_name, features=[]):
		gen.bind_method(clss, 'Get' + method_suffix, 'const %s &' % type, [], features)
		gen.bind_method(clss, 'Set' + method_suffix, 'void', ['const %s &%s' % (type, var_name)], features)

	def decl_comp_get_set_method(clss, comp_type, comp_var_name, type, method_suffix, var_name, features=[]):
		gen.bind_method(clss, 'Get' + method_suffix, 'const %s &' % type, ['const %s *%s' % (comp_type, comp_var_name)], features)
		gen.bind_method(clss, 'Set' + method_suffix, 'void', ['%s *%s' % (comp_type, comp_var_name), 'const %s &%s' % (type, var_name)], features)

	# gs::core::Component
	gen.add_include('engine/component.h')

	component = gen.begin_class('gs::core::Component', bound_name='Component_hide_me', noncopyable=True, nobind=True)
	gen.end_class(component)

	shared_component = gen.begin_class('std::shared_ptr<gs::core::Component>', bound_name='Component', features={'proxy': lib.stl.SharedPtrProxyFeature(component)})
	gen.end_class(shared_component)

	std_vector_shared_component = gen.begin_class('std::vector<std::shared_ptr<gs::core::Component>>', bound_name='ComponentList', features={'sequence': lib.std.VectorSequenceFeature(shared_component)})
	gen.end_class(std_vector_shared_component)

	# gs::core::Environment
	gen.add_include('engine/environment.h')

	environment = gen.begin_class('gs::core::Environment', bound_name='Environment_hide_me', noncopyable=True, nobind=True)
	gen.end_class(environment)

	shared_environment = gen.begin_class('std::shared_ptr<gs::core::Environment>', bound_name='Environment', features={'proxy': lib.stl.SharedPtrProxyFeature(environment)})
	gen.end_class(shared_environment)

	# gs::core::Transform
	gen.add_include('engine/transform.h')

	transform = gen.begin_class('gs::core::Transform', bound_name='Transform_hide_me', noncopyable=True, nobind=True)
	gen.end_class(transform)

	shared_transform = gen.begin_class('std::shared_ptr<gs::core::Transform>', bound_name='Transform', features={'proxy': lib.stl.SharedPtrProxyFeature(transform)})
	gen.bind_method(shared_transform, 'GetPreviousWorld', 'gs::Matrix4', [], ['proxy'])
	gen.bind_method(shared_transform, 'GetWorld', 'gs::Matrix4', [], ['proxy'])

	gen.bind_method(shared_transform, 'GetPosition', 'gs::Vector3', [], ['proxy'])
	gen.bind_method(shared_transform, 'SetPosition', 'void', ['const gs::Vector3 &position'], ['proxy'])
	gen.bind_method(shared_transform, 'GetRotation', 'gs::Vector3', [], ['proxy'])
	gen.bind_method(shared_transform, 'SetRotation', 'void', ['const gs::Vector3 &rotation'], ['proxy'])
	gen.bind_method(shared_transform, 'GetScale', 'gs::Vector3', [], ['proxy'])
	gen.bind_method(shared_transform, 'SetScale', 'void', ['const gs::Vector3 &scale'], ['proxy'])

	gen.bind_method(shared_transform, 'SetRotationMatrix', 'void', ['const gs::Matrix3 &rotation'], ['proxy'])
	gen.end_class(shared_transform)

	# gs::core::Light
	gen.add_include('engine/light.h')

	gen.bind_named_enum('gs::core::Light::Model', ['ModelPoint', 'ModelLinear', 'ModelSpot', 'ModelLast'], prefix='Light')
	gen.bind_named_enum('gs::core::Light::Shadow', ['ShadowNone', 'ShadowProjectionMap', 'ShadowMap'], prefix='Light')

	light = gen.begin_class('gs::core::Light', bound_name='Light_hide_me', noncopyable=True, nobind=True)
	gen.end_class(light)

	shared_light = gen.begin_class('std::shared_ptr<gs::core::Light>', bound_name='Light', features={'proxy': lib.stl.SharedPtrProxyFeature(light)})
	gen.end_class(shared_light)

	# gs::core::RigidBody
	gen.add_include('engine/rigid_body.h')

	gen.bind_named_enum('gs::core::RigidBodyType', ['RigidBodyDynamic', 'RigidBodyKinematic', 'RigidBodyStatic'])

	rigid_body = gen.begin_class('gs::core::RigidBody', bound_name='RigidBody_hide_me', noncopyable=True, nobind=True)
	gen.end_class(rigid_body)

	shared_rigid_body = gen.begin_class('std::shared_ptr<gs::core::RigidBody>', bound_name='RigidBody', features={'proxy': lib.stl.SharedPtrProxyFeature(rigid_body)})

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

	# gs::core::Node
	gen.add_include('engine/node.h')

	node = gen.begin_class('gs::core::Node', bound_name='Node_hide_me', noncopyable=True, nobind=True)
	gen.end_class(node)

	shared_node = gen.begin_class('std::shared_ptr<gs::core::Node>', bound_name='Node', features={'proxy': lib.stl.SharedPtrProxyFeature(node)})

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

	gen.bind_method(shared_node, 'GetComponent<gs::core::Transform>', 'std::shared_ptr<gs::core::Transform>', [], {'proxy': None, 'check_rval': lambda rvals, ctx: 'if (!%s) {\n%s}\n' % (rvals[0], gen.proxy_call_error('GetTransform failed, node has no Transform component', ctx))}, bound_name='GetTransform')
	gen.bind_method(shared_node, 'GetComponent<gs::core::Light>', 'std::shared_ptr<gs::core::Light>', [], {'proxy': None, 'check_rval': lambda rvals, ctx: 'if (!%s) {\n%s}\n' % (rvals[0], gen.proxy_call_error('GetLight failed, node has no Light component', ctx))}, bound_name='GetLight')

	gen.bind_method(shared_node, 'HasAspect', 'bool', ['const char *aspect'], ['proxy'])
	gen.bind_method(shared_node, 'IsReady', 'bool', [], ['proxy'])

	gen.bind_method(shared_node, 'IsInstantiated', 'bool', [], ['proxy'])

	decl_get_set_method(shared_node, 'bool', 'Enabled', 'enable', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'IsStatic', 'is_static', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'DoNotSerialize', 'do_not_serialize', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'DoNotInstantiate', 'do_not_instantiate', features=['proxy'])
	decl_get_set_method(shared_node, 'bool', 'UseForNavigation', 'use_for_navigation', features=['proxy'])

	gen.end_class(shared_node)

	std_vector_shared_node = gen.begin_class('std::vector<std::shared_ptr<gs::core::Node>>', bound_name='NodeList', features={'sequence': lib.std.VectorSequenceFeature(shared_node)})
	gen.end_class(std_vector_shared_node)

	# gs::core::SceneSystem
	scene_system = gen.begin_class('gs::core::SceneSystem', bound_name='SceneSystem_hide_me', noncopyable=True, nobind=True)
	gen.end_class(scene_system)

	shared_scene_system = gen.begin_class('std::shared_ptr<gs::core::SceneSystem>', bound_name='SceneSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(scene_system)})
	gen.end_class(shared_scene_system)

	# gs::core::RenderableSystem
	gen.add_include('engine/renderable_system.h')

	renderable_system = gen.begin_class('gs::core::RenderableSystem', bound_name='RenderableSystem_hide_me', noncopyable=True, nobind=True)
	gen.end_class(renderable_system)

	shared_renderable_system = gen.begin_class('std::shared_ptr<gs::core::RenderableSystem>', bound_name='RenderableSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(renderable_system)})

	gen.bind_constructor_overloads(shared_renderable_system, [
		(['std::shared_ptr<gs::render::RenderSystem> render_system'], ['proxy']),
		(['std::shared_ptr<gs::render::RenderSystem> render_system', 'bool async'], ['proxy'])
	])

	gen.bind_method(shared_renderable_system, 'DrawGeometry', 'void', ['std::shared_ptr<gs::render::Geometry> geometry', 'const gs::Matrix4 &world'], ['proxy'])

	gen.end_class(shared_renderable_system)

	# gs::core::IPhysicSystem
	gen.add_include('engine/physic_system.h')

	physic_system = gen.begin_class('gs::core::IPhysicSystem', bound_name='PhysicSystem_hide_me', noncopyable=True, nobind=True)
	gen.end_class(physic_system)

	shared_physic_system = gen.begin_class('std::shared_ptr<gs::core::IPhysicSystem>', bound_name='PhysicSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(physic_system)})

	gen.bind_method(shared_physic_system, 'GetImplementationName', 'const std::string &', [], ['proxy'])

	decl_get_set_method(shared_physic_system, 'float', 'Timestep', 'timestep', ['proxy'])
	decl_get_set_method(shared_physic_system, 'bool', 'ForceRigidBodyToSleepOnCreation', 'force_sleep_body', ['proxy'])
	decl_get_set_method(shared_physic_system, 'gs::uint', 'ForceRigidBodyAxisLockOnCreation', 'force_axis_lock', ['proxy'])

	decl_get_set_method(shared_physic_system, 'gs::Vector3', 'Gravity', 'G', ['proxy'])

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

	# gs::core::Group
	gen.add_include('engine/group.h')

	group = gen.begin_class('gs::core::Group', bound_name='Group_hide_me', noncopyable=True, nobind=True)
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
		('std::shared_ptr<gs::core::Node>', ['uint32_t uid'], ['proxy']),
		('std::shared_ptr<gs::core::Node>', ['const char *name'], ['proxy']),
		('std::shared_ptr<gs::core::Node>', ['const char *name', 'const std::shared_ptr<gs::core::Node> &parent'], ['proxy'])
	])

	gen.bind_method(shared_group, 'AddGroup', 'void', ['std::shared_ptr<gs::core::Group> group'], ['proxy'])
	gen.bind_method(shared_group, 'RemoveGroup', 'void', ['const std::shared_ptr<gs::core::Group> &group'], ['proxy'])

	gen.bind_method(shared_group, 'GetGroup', 'std::shared_ptr<gs::core::Group>', ['const char *name'], ['proxy'])

	gen.bind_method(shared_group, 'AppendGroup', 'void', ['const gs::core::Group &group'], ['proxy'])

	gen.bind_method(shared_group, 'GetName', 'const std::string &', [], ['proxy'])
	gen.bind_method(shared_group, 'SetName', 'void', ['const char *name'], ['proxy'])

	gen.end_class(shared_group)

	# gs::core::Scene
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
		('std::shared_ptr<gs::core::Node>', ['gs::uint uid'], ['proxy']),
		('std::shared_ptr<gs::core::Node>', ['const char *name'], ['proxy']),
		('std::shared_ptr<gs::core::Node>', ['const char *name', 'const std::shared_ptr<gs::core::Node> &parent'], ['proxy'])
	])

	gen.bind_method_overloads(shared_scene, 'GetNodes', [
		('const std::vector<std::shared_ptr<gs::core::Node>> &', [], ['proxy']),
		('std::vector<std::shared_ptr<gs::core::Node>>', ['const char *filter'], ['proxy'])
	])
	gen.bind_method(shared_scene, 'GetNodeChildren', 'std::vector<std::shared_ptr<gs::core::Node>>', ['const gs::core::Node &node'], ['proxy'])
	gen.bind_method(shared_scene, 'GetNodesWithAspect', 'std::vector<std::shared_ptr<gs::core::Node>>', ['const char *aspect'], ['proxy'])

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

	#template <class T> std::shared_ptr<T> GetComponent() const {

	gen.bind_method(shared_scene, 'HasAspect', 'bool', ['const char *aspect'], ['proxy'])
	gen.bind_method(shared_scene, 'GetMinMax', 'gs::MinMax', [], ['proxy'])

	gen.end_class(shared_scene)


def bind_gpu(gen):
	# gs::gpu::Buffer
	gen.add_include('engine/gpu_buffer.h')

	gen.bind_named_enum('gs::gpu::Buffer::Usage', ['Static', 'Dynamic'], bound_name='GpuBufferUsage', prefix='GpuBuffer')
	gen.bind_named_enum('gs::gpu::Buffer::Type', ['Index', 'Vertex'], bound_name='GpuBufferType', prefix='GpuBuffer')

	buffer = gen.begin_class('gs::gpu::Buffer', bound_name='Buffer_hide_me', noncopyable=True, nobind=True)
	gen.end_class(buffer)

	shared_buffer = gen.begin_class('std::shared_ptr<gs::gpu::Buffer>', bound_name='GpuBuffer', features={'proxy': lib.stl.SharedPtrProxyFeature(buffer)})
	gen.end_class(shared_buffer)

	# gs::gpu::Texture
	gen.add_include('engine/texture.h')

	gen.bind_named_enum('gs::gpu::TextureUsage::Type', ['IsRenderTarget', 'IsShaderResource'], prefix='Texture', bound_name='TextureUsageFlags', namespace='gs::gpu::TextureUsage')
	gen.bind_named_enum('gs::gpu::Texture::Format', ['RGBA8', 'BGRA8', 'RGBA16', 'RGBAF', 'Depth', 'DepthF', 'R8', 'R16', 'InvalidFormat'], 'uint8_t', 'TextureFormat', 'Texture')
	gen.bind_named_enum('gs::gpu::Texture::AA', ['NoAA', 'MSAA2x', 'MSAA4x', 'MSAA8x', 'MSAA16x', 'AALast'], 'uint8_t', 'TextureAA', 'Texture')

	texture = gen.begin_class('gs::gpu::Texture', bound_name='Texture_hide_me', noncopyable=True, nobind=True)
	gen.end_class(texture)

	shared_texture = gen.begin_class('std::shared_ptr<gs::gpu::Texture>', bound_name='Texture', features={'proxy': lib.stl.SharedPtrProxyFeature(texture)})

	gen.bind_method(shared_texture, 'GetWidth', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_texture, 'GetHeight', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_texture, 'GetDepth', 'gs::uint', [], ['proxy'])
	gen.bind_method(shared_texture, 'GetRect', 'gs::Rect<float>', [], ['proxy'])

	gen.end_class(shared_texture)

	# gs::gpu::RenderTarget
	render_target = gen.begin_class('gs::gpu::RenderTarget', bound_name='RenderTarget_hide_me', noncopyable=True, nobind=True)
	gen.end_class(render_target)

	shared_render_target = gen.begin_class('std::shared_ptr<gs::gpu::RenderTarget>', bound_name='RenderTarget', features={'proxy': lib.stl.SharedPtrProxyFeature(render_target)})
	gen.end_class(shared_render_target)

	# gs::gpu::HardwareInfo
	hw_info = gen.begin_class('gs::gpu::HardwareInfo')
	gen.bind_members(hw_info, ['std::string name', 'std::string vendor'])
	gen.end_class(hw_info)

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

	# gs::gpu::Renderer
	gen.add_include('engine/renderer.h')

	gen.bind_named_enum('gs::gpu::Renderer::FillMode', ['FillSolid', 'FillWireframe', 'FillLast'], bound_name='RendererFillMode', prefix='Renderer')
	gen.bind_named_enum('gs::gpu::Renderer::CullFunc', ['CullFront', 'CullBack', 'CullLast'], bound_name='RendererCullMode', prefix='Renderer')
	gen.bind_named_enum('gs::gpu::Renderer::DepthFunc', ['DepthNever', 'DepthLess', 'DepthEqual', 'DepthLessEqual', 'DepthGreater', 'DepthNotEqual', 'DepthGreaterEqual', 'DepthAlways', 'DepthFuncLast'], bound_name='RendererDepthFunc', prefix='Renderer')

	gen.bind_named_enum('gs::gpu::Renderer::ClearFunction', ['ClearColor', 'ClearDepth', 'ClearAll'], bound_name='RendererClearFlags')

	renderer = gen.begin_class('gs::gpu::Renderer', bound_name='Renderer_hide_me', noncopyable=True, nobind=True)
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
	#gen.bind_method(shared_renderer, 'GetShaderCache', 'const gs::TCache<gs::gpu::Shader> &', [], ['proxy'])

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
	gen.bind_method(shared_renderer, 'FreeBuffer', 'void', ['gs::gpu::Buffer &buffer'], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'NewTexture', [
		('std::shared_ptr<gs::gpu::Texture>', [], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'int width', 'int height'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa', 'gs::gpu::TextureUsage::Type usage'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa', 'gs::gpu::TextureUsage::Type usage', 'bool mipmapped'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'const gs::Picture &picture'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'const gs::Picture &picture', 'gs::gpu::TextureUsage::Type usage'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name', 'const gs::Picture &picture', 'gs::gpu::TextureUsage::Type usage', 'bool mipmapped'], ['proxy'])
	])
	gen.bind_method_overloads(shared_renderer, 'NewShadowMap', [
		('std::shared_ptr<gs::gpu::Texture>', ['int width', 'int height'], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['int width', 'int height', 'const char *name'], ['proxy'])
	])
	gen.bind_method_overloads(shared_renderer, 'NewExternalTexture', [
		('std::shared_ptr<gs::gpu::Texture>', [], ['proxy']),
		('std::shared_ptr<gs::gpu::Texture>', ['const char *name'], ['proxy'])
	])
	gen.bind_method_overloads(shared_renderer, 'CreateTexture', [
		('bool', ['gs::gpu::Texture &texture', 'const void *data', 'size_t data_size', 'int width', 'int height'], ['proxy']),
		('bool', ['gs::gpu::Texture &texture', 'const void *data', 'size_t data_size', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa'], ['proxy']),
		('bool', ['gs::gpu::Texture &texture', 'const void *data', 'size_t data_size', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa', 'gs::gpu::TextureUsage::Type usage'], ['proxy']),
		('bool', ['gs::gpu::Texture &texture', 'const void *data', 'size_t data_size', 'int width', 'int height', 'gs::gpu::Texture::Format format', 'gs::gpu::Texture::AA aa', 'gs::gpu::TextureUsage::Type usage', 'bool mipmapped'], ['proxy']),
		('bool', ['gs::gpu::Texture &texture', 'const gs::Picture &picture'], ['proxy']),
		('bool', ['gs::gpu::Texture &texture', 'const gs::Picture &picture', 'gs::gpu::TextureUsage::Type usage'], ['proxy']),
		('bool', ['gs::gpu::Texture &texture', 'const gs::Picture &picture', 'gs::gpu::TextureUsage::Type usage', 'bool mipmapped'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'FreeTexture', 'void', ['gs::gpu::Texture &texture'], ['proxy'])

	gen.bind_method(shared_renderer, 'LoadNativeTexture', 'bool', ['gs::gpu::Texture &texture', 'const char *path'], ['proxy'])
	gen.bind_method(shared_renderer, 'GetNativeTextureExt', 'const char *', [], ['proxy'])

	gen.bind_method_overloads(shared_renderer, 'BlitTexture', [
		('void', ['gs::gpu::Texture &texture', 'const void *data', 'size_t data_size', 'gs::uint width', 'gs::uint height'], ['proxy']),
		('void', ['gs::gpu::Texture &texture', 'const void *data', 'size_t data_size', 'gs::uint width', 'gs::uint height', 'gs::uint x', 'gs::uint y'], ['proxy'])
	])
	gen.bind_method(shared_renderer, 'ResizeTexture', 'void', ['gs::gpu::Texture &texture', 'gs::uint width', 'gs::uint height'], ['proxy'])

	#
	# ...
	#

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

	def check_create_renderer_rval(rvals, ctx):
		return 'if (!%s) {\n%s}\n' % (rvals[0], gen.proxy_call_error('CreateRenderer failed, was gs.LoadPlugins called succesfully?', ctx))

	gen.bind_function_overloads('CreateRenderer', [
		('std::shared_ptr<gs::gpu::Renderer>', [], {'check_rval': check_create_renderer_rval}),
		('std::shared_ptr<gs::gpu::Renderer>', ['const char *name'], {'check_rval': check_create_renderer_rval})
	])

	# gs::gpu::RendererAsync
	gen.add_include('engine/renderer_async.h')

	renderer_async = gen.begin_class('gs::gpu::RendererAsync', bound_name='RendererAsync_hide_me', noncopyable=True, nobind=True)
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

	gen.end_class(shared_renderer_async)


def bind_render(gen):
	gen.add_include('engine/render_system.h')

	gen.bind_named_enum('gs::render::Eye', ['EyeMono', 'EyeStereoLeft', 'EyeStereoRight'])
	gen.bind_named_enum('gs::render::CullMode', ['CullBack', 'CullFront', 'CullNever'])
	gen.bind_named_enum('gs::render::BlendMode', ['BlendOpaque', 'BlendAlpha', 'BlendAdditive'])

	# gs::render::SurfaceShader
	gen.add_include('engine/surface_shader.h')

	surface_shader = gen.begin_class('gs::render::SurfaceShader', bound_name='SurfaceShader_hide_me', noncopyable=True, nobind=True)
	gen.end_class(surface_shader)

	shared_surface_shader = gen.begin_class('std::shared_ptr<gs::render::SurfaceShader>', bound_name='SurfaceShader', features={'proxy': lib.stl.SharedPtrProxyFeature(surface_shader)})
	gen.bind_method_overloads(shared_surface_shader, 'SetUserUniformValue', [
		('bool', ['const char *name', 'gs::Vector4 value'], ['proxy']),
		('bool', ['const char *name', 'std::shared_ptr<gs::gpu::Texture> texture'], ['proxy'])
	])
	gen.end_class(shared_surface_shader)

	# gs::render::Material
	gen.add_include('engine/render_material.h')

	material = gen.begin_class('gs::render::Material', bound_name='RenderMaterial_hide_me', noncopyable=True, nobind=True)
	gen.end_class(material)

	shared_material = gen.begin_class('std::shared_ptr<gs::render::Material>', bound_name='RenderMaterial', features={'proxy': lib.stl.SharedPtrProxyFeature(material)})
	gen.end_class(shared_material)

	# gs::render::Geometry
	gen.add_include('engine/render_geometry.h')

	geometry = gen.begin_class('gs::render::Geometry', bound_name='RenderGeometry_hide_me', noncopyable=True, nobind=True)
	gen.end_class(geometry)

	shared_geometry = gen.begin_class('std::shared_ptr<gs::render::Geometry>', bound_name='RenderGeometry', features={'proxy': lib.stl.SharedPtrProxyFeature(geometry)})
	gen.bind_constructor_overloads(shared_geometry, [
		([], ['proxy']),
		(['const char *name'], ['proxy']),
	])
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

	render_system = gen.begin_class('gs::render::RenderSystem', bound_name='RenderSystem_hide_me', noncopyable=True, nobind=True)
	gen.end_class(render_system)

	shared_render_system = gen.begin_class('std::shared_ptr<gs::render::RenderSystem>', bound_name='RenderSystem', features={'proxy': lib.stl.SharedPtrProxyFeature(render_system)})

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
	gen.bind_method_overloads(shared_render_system, 'DrawLine', [
		('void', ['gs::uint count', 'gs::Vector3 *pos'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const gs::tVector2<float> *uv'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const gs::tVector2<float> *uv', 'uint16_t *idx', 'gs::uint vtx_count'], ['proxy'])
	])
	gen.bind_method_overloads(shared_render_system, 'DrawTriangle', [
		('void', ['gs::uint count', 'gs::Vector3 *pos'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const gs::tVector2<float> *uv'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const gs::tVector2<float> *uv', 'uint16_t *idx', 'gs::uint vtx_count'], ['proxy'])
	])
	gen.bind_method_overloads(shared_render_system, 'DrawSprite', [
		('void', ['gs::uint count', 'gs::Vector3 *pos'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const float *size'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const float *size', 'float global_size'], ['proxy'])
	])

	gen.bind_method_overloads(shared_render_system, 'DrawLineAuto', [
		('void', ['gs::uint count', 'gs::Vector3 *pos'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const gs::tVector2<float> *uv', 'const gs::gpu::Texture *texture'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const gs::tVector2<float> *uv', 'const gs::gpu::Texture *texture', 'uint16_t *idx', 'gs::uint vtx_count'], ['proxy'])
	])
	gen.bind_method_overloads(shared_render_system, 'DrawTriangleAuto', [
		('void', ['gs::uint count', 'gs::Vector3 *pos'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const gs::tVector2<float> *uv', 'const gs::gpu::Texture *texture'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'gs::Color *col', 'const gs::tVector2<float> *uv', 'const gs::gpu::Texture *texture', 'uint16_t *idx', 'gs::uint vtx_count'], ['proxy'])
	])
	gen.bind_method_overloads(shared_render_system, 'DrawSpriteAuto', [
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'const gs::gpu::Texture &texture'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'const gs::gpu::Texture &texture', 'gs::Color *col'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'const gs::gpu::Texture &texture', 'gs::Color *col', 'const float *size'], ['proxy']),
		('void', ['gs::uint count', 'gs::Vector3 *pos', 'const gs::gpu::Texture &texture', 'gs::Color *col', 'const float *size', 'float global_size'], ['proxy'])
	])

	gen.bind_method(shared_render_system, 'DrawQuad2D', 'void', ['const gs::Rect<float> &src_rect', 'const gs::Rect<float> &dst_rect'], ['proxy'])
	gen.bind_method(shared_render_system, 'DrawFullscreenQuad', 'void', ['const gs::tVector2<float> &uv'], ['proxy'])

	gen.bind_method(shared_render_system, 'DrawGeometrySimple', 'void', ['const gs::render::Geometry &geometry'], ['proxy'])
	#gen.bind_method(shared_render_system, 'DrawSceneSimple', 'void', ['const gs::core::Scene &scene'], ['proxy'])

	gen.bind_method(shared_render_system, 'GetShadowMap', 'const std::shared_ptr<gs::gpu::Texture> &', [], ['proxy'])
	gen.end_class(shared_render_system)

	# render::RenderSystem
	gen.add_include('engine/render_system_async.h')

	render_system_async = gen.begin_class('gs::render::RenderSystemAsync', bound_name='RenderSystemAsync_hide_me', noncopyable=True, nobind=True)
	gen.end_class(render_system_async)

	shared_render_system_async = gen.begin_class('std::shared_ptr<gs::render::RenderSystemAsync>', bound_name='RenderSystemAsync', features={'proxy': lib.stl.SharedPtrProxyFeature(render_system_async)})
	gen.end_class(shared_render_system_async)


def bind_iso_surface(gen):
	gen.add_include('engine/iso_surface.h')

	iso_surface = gen.begin_class('gs::core::IsoSurface', bound_name='IsoSurface_hide_me', nobind=True)
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
	gen.add_include('plus/plus.h')

	# gs::RenderWindow
	window_conv = gen.begin_class('gs::RenderWindow')
	gen.end_class(window_conv)

	# gs::Plus
	plus_conv = gen.begin_class('gs::Plus', noncopyable=True)

	gen.bind_constructor(plus_conv, [])

	gen.bind_method(plus_conv, 'CreateWorkers', 'void', [])
	gen.bind_method(plus_conv, 'DeleteWorkers', 'void', [])

	gen.bind_method(plus_conv, 'MountFilePath', 'void', ['const char *path'])

	gen.bind_method(plus_conv, 'GetRenderer', 'std::shared_ptr<gs::gpu::Renderer>', [])
	gen.bind_method(plus_conv, 'GetRendererAsync', 'std::shared_ptr<gs::gpu::RendererAsync>', [])

	gen.bind_method(plus_conv, 'GetRenderSystem', 'std::shared_ptr<gs::render::RenderSystem>', [])
	gen.bind_method(plus_conv, 'GetRenderSystemAsync', 'std::shared_ptr<gs::render::RenderSystemAsync>', [])

	gen.bind_named_enum('gs::Plus::AppEndCondition', ['EndOnEscapePressed', 'EndOnDefaultWindowClosed', 'EndOnAny'], prefix='App')

	gen.bind_method_overloads(plus_conv, 'IsAppEnded', [
		('bool', [], []),
		('bool', ['gs::Plus::AppEndCondition flags'], [])
	])

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

	gen.bind_method_overloads(plus_conv, 'NewScene', [
		('std::shared_ptr<gs::core::Scene>', [], []),
		('std::shared_ptr<gs::core::Scene>', ['bool use_physics'], []),
		('std::shared_ptr<gs::core::Scene>', ['bool use_physics', 'bool use_lua'], [])
	])
	gen.bind_method_overloads(plus_conv, 'UpdateScene', [
		('void', ['gs::core::Scene &scene'], []),
		('void', ['gs::core::Scene &scene', 'gs::time_ns dt'], [])
	])

	gen.bind_method_overloads(plus_conv, 'AddDummy', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddCamera', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'bool orthographic'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'bool orthographic', 'bool set_as_current'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddLight', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'gs::core::Light::Model model'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'gs::core::Light::Model model', 'float range'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'gs::core::Light::Model model', 'float range', 'bool shadow'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'gs::core::Light::Model model', 'float range', 'bool shadow', 'gs::Color diffuse'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'gs::core::Light::Model model', 'float range', 'bool shadow', 'gs::Color diffuse', 'gs::Color specular'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddObject', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'std::shared_ptr<gs::render::Geometry> geometry'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'std::shared_ptr<gs::render::Geometry> geometry', 'gs::Matrix4 matrix'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'std::shared_ptr<gs::render::Geometry> geometry', 'gs::Matrix4 matrix', 'bool is_static'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddGeometry', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'const char *geometry_path'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'const char *geometry_path', 'gs::Matrix4 matrix'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddPlane', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float size_x', 'float size_z'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float size_x', 'float size_z', 'const char *material_path'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddCube', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float size_x', 'float size_y', 'float size_z'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float size_x', 'float size_z', 'float size_z', 'const char *material_path'], [])
	])
	gen.bind_method_overloads(plus_conv, 'AddSphere', [
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float radius'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float radius', 'int subdiv_x', 'int subdiv_y'], []),
		('std::shared_ptr<gs::core::Node>', ['gs::core::Scene &scene', 'gs::Matrix4 matrix', 'float radius', 'int subdiv_x', 'int subdiv_y', 'const char *material_path'], [])
	])

	gen.bind_method_overloads(plus_conv, 'AddEnvironment', [
		('std::shared_ptr<gs::core::Environment>', ['gs::core::Scene &scene'], []),
		('std::shared_ptr<gs::core::Environment>', ['gs::core::Scene &scene', 'gs::Color background_color', 'gs::Color ambient_color'], []),
		('std::shared_ptr<gs::core::Environment>', ['gs::core::Scene &scene', 'gs::Color background_color', 'gs::Color ambient_color', 'gs::Color fog_color', 'float fog_near', 'float fog_far'], [])
	])

	gen.bind_method_overloads(plus_conv, 'AddPhysicCube', [
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float width', 'float height', 'float depth'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float width', 'float height', 'float depth', 'float mass'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float width', 'float height', 'float depth', 'float mass', 'const char *material_path'], {'arg_out': ['rigid_body']})
	])
	gen.bind_method_overloads(plus_conv, 'AddPhysicPlane', [
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float width', 'float length'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float width', 'float length', 'float mass'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float width', 'float length', 'float mass', 'const char *material_path'], {'arg_out': ['rigid_body']})
	])
	gen.bind_method_overloads(plus_conv, 'AddPhysicSphere', [
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float radius', 'int subdiv_x', 'int subdiv_y'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float radius', 'int subdiv_x', 'int subdiv_y', 'float mass'], {'arg_out': ['rigid_body']}),
		('std::shared_ptr<gs::core::Node>', ['std::shared_ptr<gs::core::RigidBody> &rigid_body', 'gs::core::Scene &scene', 'gs::Matrix4 m', 'float radius', 'int subdiv_x', 'int subdiv_y', 'float mass', 'const char *material_path'], {'arg_out': ['rigid_body']})
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

	gen.bind_named_enum('gs::SeekRef', ['SeekStart', 'SeekCurrent', 'SeekEnd'])
	gen.bind_named_enum('gs::io::Mode', ['ModeRead', 'ModeWrite'], bound_name='IOMode', prefix='IO')

	# forward declarations
	io_driver = gen.begin_class('gs::io::Driver', bound_name='IODriver_hide_me', noncopyable=True, nobind=True)
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
	gen.end_class(io_driver)
	gen.end_class(shared_io_driver)

	# gs::io::CFile
	io_cfile = gen.begin_class('gs::io::CFile', bound_name='CFile_hide_me', nobind=True)
	gen.end_class(io_cfile)

	shared_io_cfile = gen.begin_class('std::shared_ptr<gs::io::CFile>', bound_name='StdFileDriver', features={'proxy': lib.stl.SharedPtrProxyFeature(io_cfile)})
	gen.add_upcast(shared_io_cfile, shared_io_driver)
	gen.bind_constructor_overloads(shared_io_cfile, [
		([], ['proxy']),
		(['const std::string &root_path'], ['proxy']),
		(['const std::string &root_path', 'bool sandbox'], ['proxy'])
		])
	gen.bind_method_overloads(shared_io_cfile, 'SetRootPath', [('void', ['const std::string &path'], ['proxy']), ('void', ['const std::string &path', 'bool sandbox'], ['proxy'])])
	gen.end_class(shared_io_cfile)

	gen.bind_function_overloads('MountFileDriver', [
		('bool', ['std::shared_ptr<gs::io::Driver> driver'], []),
		('bool', ['std::shared_ptr<gs::io::Driver> driver', 'const char *prefix'], [])
	])

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

	gen.bind_static_members(color, ['const gs::Color Zero', 'const gs::Color One', 'const gs::Color White', 'const gs::Color Grey', 'const gs::Color Black', 'const gs::Color Red', 'const gs::Color Green', 'const gs::Color Blue', 'const gs::Color Yellow', 'const gs::Color Orange', 'const gs::Color Purple', 'const gs::Color Transparent'])
	gen.bind_members(color, ['float r', 'float g', 'float b', 'float a'])

	gen.bind_constructor_overloads(color, [
		([], []),
		(['float r', 'float g', 'float b'], []),
		(['float r', 'float g', 'float b', 'float a'], [])
	])

	gen.bind_arithmetic_ops_overloads(color, ['+', '-', '/', '*'], [('gs::Color', ['const gs::Color &color'], []), ('gs::Color', ['float k'], [])])
	gen.bind_inplace_arithmetic_ops_overloads(color, ['+=', '-=', '*=', '/='], [('gs::Color &color', []), ('float k', [])])
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
	picture = gen.begin_class('gs::Picture', bound_name='Picture_hide_me', nobind=True)
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


def bind_math(gen):
	gen.begin_class('gs::Vector3')
	gen.begin_class('gs::Vector4')
	gen.begin_class('gs::Matrix3')
	gen.begin_class('gs::Matrix4')
	gen.begin_class('gs::Matrix44')

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
			('const gs::tVector2<%s> &v'%T, []),
			('const %s k'%T, [])
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

		gen.end_class(vector2)

	bind_vector2_T('float', 'Vector2')
	bind_vector2_T('int', 'IntVector2')

	# gs::Vector4
	gen.add_include('foundation/vector4.h')

	vector4 = gen.begin_class('gs::Vector4')
	gen.bind_members(vector4, ['float x', 'float y', 'float z', 'float w'])

	gen.bind_constructor_overloads(vector4, [
		([], []),
		(['float x', 'float y', 'float z', 'float w'], [])
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
		('gs::Vector4 &v', []),
		('float k', [])
	])

	gen.bind_method(vector4, 'Abs', 'gs::Vector4', [])

	gen.bind_method(vector4, 'Normalized', 'gs::Vector4', [])

	gen.end_class(vector4)

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
		('gs::Vector3', ['const gs::Vector3 &v'], []),
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

	gen.bind_method(matrix4, 'GetRow', 'gs::Vector3', ['gs::uint n'])
	gen.bind_method(matrix4, 'GetColumn', 'gs::Vector4', ['gs::uint n'])
	gen.bind_method(matrix4, 'SetRow', 'void', ['gs::uint n', 'const gs::Vector3 &v'])
	gen.bind_method(matrix4, 'SetColumn', 'void', ['gs::uint n', 'const gs::Vector4 &v'])

	gen.bind_method(matrix4, 'GetX', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetY', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetZ', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetT', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetTranslation', 'gs::Vector3', [])
	#gen.bind_method(matrix4, 'GetRotation', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetScale', 'gs::Vector3', [])
	gen.bind_method(matrix4, 'GetRotationMatrix', 'gs::Matrix3', [])

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
	#void Decompose(Vector3 *position, Vector3 *scale, Vector3 *rotation, math::RotationOrder order = math::RotationOrder_Default) const;

	#void Transform(Vector3 * __restrict out, const Vector3 * __restrict in, uint count = 1) const __restrict;
	#void Transform(Vector4 * __restrict out, const Vector3 * __restrict in, uint count = 1) const __restrict;
	#void Rotate(Vector3 * __restrict out, const Vector3 * __restrict in, uint count = 1) const __restrict;

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

	gen.bind_static_members(vector3, ['const gs::Vector3 Zero', 'const gs::Vector3 One', 'const gs::Vector3 Left', 'const gs::Vector3 Right', 'const gs::Vector3 Up', 'const gs::Vector3 Down', 'const gs::Vector3 Front', 'const gs::Vector3 Back'])
	gen.bind_members(vector3, ['float x', 'float y', 'float z'])

	gen.bind_constructor_overloads(vector3, [
		([], []),
		(['float x', 'float y', 'float z'], [])
	])

	gen.bind_function('gs::Vector3FromVector4', 'gs::Vector3', ['const gs::Vector4 &v'])

	gen.bind_arithmetic_ops_overloads(vector3, ['+', '-', '/'], [('gs::Vector3', ['gs::Vector3 &v'], []), ('gs::Vector3', ['float k'], [])])
	gen.bind_arithmetic_ops_overloads(vector3, ['*'], [('gs::Vector3', ['gs::Vector3 &v'], []), ('gs::Vector3', ['float k'], []), ('gs::Vector3', ['gs::Matrix3 m'], []), ('gs::Vector3', ['gs::Matrix4 m'], [])])

	gen.bind_inplace_arithmetic_ops_overloads(vector3, ['+=', '-=', '*=', '/='], [('gs::Vector3 &v', []), ('float k', [])])
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

	gen.end_class(vector3)

	# gs::Rect<T>
	def bind_rect_T(T, bound_name):
		rect = gen.begin_class('gs::Rect<%s>'%T, bound_name=bound_name)

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
	lib.stl.bind_future_T(gen, 'gs::Vector3', 'FutureVector3')
	lib.stl.bind_future_T(gen, 'gs::Vector4', 'FutureVector4')
	lib.stl.bind_future_T(gen, 'gs::Matrix3', 'FutureMatrix3')
	lib.stl.bind_future_T(gen, 'gs::Matrix4', 'FutureMatrix4')

	# math std::vector
	lib.python.stl.register_PySequence_to_std_vector(gen, 'PySequenceOfVector3', vector3)

	std_vector_vector3 = gen.begin_class('std::vector<gs::Vector3>', bound_name='Vector3List', features={'sequence': lib.std.VectorSequenceFeature(vector3)})
	gen.bind_constructor(std_vector_vector3, ['PySequenceOfVector3 sequence'], ['lang': 'CPython'])
	gen.end_class(std_vector_vector3)
	
	gen.insert_binding_code('static std::vector<gs::Vector3> pof() { return {gs::Vector3(1, 0, 2), gs::Vector3(5, 4, 8)}; }\n')

	gen.bind_function('pof', 'PySequenceOfVector3', [])


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

	audio_data = gen.begin_class('gs::AudioData', bound_name='AudioData_hide_me', noncopyable=True, nobind=True)
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

	gen.typedef('gs::audio::MixerChannel', 'int')
	gen.typedef('gs::audio::MixerPriority', 'int')

	#
	mixer_channel_state = gen.begin_class('gs::audio::MixerChannelState')
	gen.bind_constructor_overloads(mixer_channel_state, [
		([], []),
		(['float volume'], []),
		(['float volume', 'bool direct'], [])
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
	sound = gen.begin_class('gs::audio::Sound', bound_name='Sound_hide_me', noncopyable=True, nobind=True)
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

	#
	def bind_mixer_api(conv, features=[]):
		gen.bind_static_members(conv, [
			'const gs::audio::MixerChannelState DefaultState', 'const gs::audio::MixerChannelState RepeatState', 'const gs::audio::MixerChannelLocation DefaultLocation',
			'const gs::audio::MixerPriority DefaultPriority', 'const gs::audio::MixerChannel ChannelError'], features)

		gen.bind_method(conv, 'Open', 'bool', [], features)
		gen.bind_method(conv, 'Close', 'void', [], features)

		gen.bind_method(conv, 'GetMasterVolume', 'float', [], features)
		gen.bind_method(conv, 'SetMasterVolume', 'void', ['float volume'], features)

		gen.bind_method(conv, 'EnableSpatialization', 'bool', ['bool enable'], features)

		gen.bind_method_overloads(conv, 'Start', [
			('gs::audio::MixerChannel', ['gs::audio::Sound &sound'], features),
			('gs::audio::MixerChannel', ['gs::audio::Sound &sound', 'gs::audio::MixerChannelState state'], features),
			('gs::audio::MixerChannel', ['gs::audio::Sound &sound', 'gs::audio::MixerChannelLocation location'], features),
			('gs::audio::MixerChannel', ['gs::audio::Sound &sound', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state'], features)
		])
		gen.bind_method_overloads(conv, 'StreamData', [
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'bool paused'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'bool paused', 'gs::time_ns t_start'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelState state'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelState state', 'bool paused'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'bool paused'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'bool paused', 'gs::time_ns t_start'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused'], features),
			('gs::audio::MixerChannel', ['std::shared_ptr<gs::AudioData> data', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], features)
		])

		gen.bind_method(conv, 'GetPlayState', 'gs::audio::MixerPlayState', ['gs::audio::MixerChannel channel'], features)

		gen.bind_method(conv, 'GetChannelState', 'gs::audio::MixerChannelState', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'SetChannelState', 'void', ['gs::audio::MixerChannel channel', 'gs::audio::MixerChannelState state'], features)

		gen.bind_method(conv, 'GetChannelLocation', 'gs::audio::MixerChannelLocation', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'SetChannelLocation', 'void', ['gs::audio::MixerChannel channel', 'gs::audio::MixerChannelLocation location'], features)

		gen.bind_method(conv, 'GetChannelTimestamp', 'gs::time_ns', ['gs::audio::MixerChannel channel'], features)

		gen.bind_method(conv, 'Stop', 'void', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'Pause', 'void', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'Resume', 'void', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'StopAll', 'void', [], features)

		gen.bind_method(conv, 'SetStreamLoopPoint', 'void', ['gs::audio::MixerChannel channel', 'gs::time_ns t'], features)
		gen.bind_method(conv, 'SeekStream', 'void', ['gs::audio::MixerChannel channel', 'gs::time_ns t'], features)
		gen.bind_method(conv, 'GetStreamBufferingPercentage', 'int', ['gs::audio::MixerChannel channel'], features)

		gen.bind_method(conv, 'SetChannelStreamDataTransform', 'void', ['gs::audio::MixerChannel channel', 'const gs::Matrix4 &transform'], features)
		gen.bind_method(conv, 'FlushChannelBuffers', 'void', ['gs::audio::MixerChannel channel'], features)

		gen.bind_method(conv, 'GetListener', 'gs::Matrix4', [], features)
		gen.bind_method(conv, 'SetListener', 'void', ['const gs::Matrix4 &transform'], features)

		gen.bind_method_overloads(conv, 'Stream', [
			('gs::audio::MixerChannel', ['const char *path'], features),
			('gs::audio::MixerChannel', ['const char *path', 'bool paused'], features),
			('gs::audio::MixerChannel', ['const char *path', 'bool paused', 'gs::time_ns t_start'], features),
			('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelState state'], features),
			('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelState state', 'bool paused'], features),
			('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], features),
			('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location'], features),
			('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'bool paused'], features),
			('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'bool paused', 'gs::time_ns t_start'], features),
			('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state'], features),
			('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused'], features),
			('gs::audio::MixerChannel', ['const char *path', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state', 'bool paused', 'gs::time_ns t_start'], features)
		])

		gen.bind_method_overloads(conv, 'LoadSoundData', [
			('std::shared_ptr<gs::audio::Sound>', ['std::shared_ptr<gs::AudioData> data'], features),
			('std::shared_ptr<gs::audio::Sound>', ['std::shared_ptr<gs::AudioData> data', 'const char *path'], features)
		])

		gen.bind_method(conv, 'LoadSound', 'std::shared_ptr<gs::audio::Sound>', ['const char *path'], features)
		gen.bind_method(conv, 'FreeSound', 'void', ['gs::audio::Sound &sound'], features)

	audio_mixer = gen.begin_class('gs::audio::Mixer', bound_name='Mixer_hide_me', noncopyable=True, nobind=True)
	gen.end_class(audio_mixer)

	shared_audio_mixer = gen.begin_class('std::shared_ptr<gs::audio::Mixer>', bound_name='Mixer', features={'proxy': lib.stl.SharedPtrProxyFeature(audio_mixer)})
	bind_mixer_api(shared_audio_mixer, ['proxy'])
	gen.end_class(shared_audio_mixer)

	gen.insert_binding_code('''static std::shared_ptr<gs::audio::Mixer> CreateMixer(const char *name) { return gs::core::g_mixer_factory.get().Instantiate(name); }
static std::shared_ptr<gs::audio::Mixer> CreateMixer() { return gs::core::g_mixer_factory.get().Instantiate(); }
	''', 'Mixer custom API')

	gen.bind_function_overloads('CreateMixer', [('std::shared_ptr<gs::audio::Mixer>', [], []), ('std::shared_ptr<gs::audio::Mixer>', ['const char *name'], [])])

	# gs::audio::MixerAsync
	mixer_async = gen.begin_class('gs::audio::MixerAsync', bound_name='MixerAsync_hide_me', noncopyable=True, nobind=True)
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

	gen.bind_method(shared_mixer_async, 'LoadSound', 'std::shared_ptr<gs::audio::Sound>', ['const char *path'], ['proxy'])
	gen.bind_method(shared_mixer_async, 'FreeSound', 'void', ['const std::shared_ptr<gs::audio::Sound> &sound'], ['proxy'])

	gen.end_class(shared_mixer_async)


def bind_gs(gen):
	gen.start('gs')

	gen.add_include('engine/engine.h')
	gen.add_include('engine/engine_plugins.h')
	gen.add_include('engine/engine_factories.h')

	gen.insert_code('''
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

	gen.add_custom_init_code('''
	gs::core::Init();

	InitializePluginsDefaultSearchPath();
''')

	float_ptr = gen.bind_ptr('float *', bound_name='FloatPointer')
	void_ptr = gen.bind_ptr('void *', bound_name='VoidPointer')

	gen.typedef('gs::uint', 'unsigned int')

	lib.stl.bind_future_T(gen, 'void', 'FutureVoid')
	lib.stl.bind_future_T(gen, 'bool', 'FutureBool')
	lib.stl.bind_future_T(gen, 'int', 'FutureInt')
	lib.stl.bind_future_T(gen, 'float', 'FutureFloat')

	lib.stl.bind_future_T(gen, 'gs::uint', 'FutureUInt')
	lib.stl.bind_future_T(gen, 'size_t', 'FutureSize')

	"""
	bind_binary_blob(gen)
	bind_time(gen)
	bind_task_system(gen)
	"""
	bind_math(gen)
	"""
	bind_frustum(gen)
	bind_window_system(gen)
	bind_color(gen)
	bind_font_engine(gen)
	bind_picture(gen)
	bind_engine(gen)
	bind_plugins(gen)
	bind_filesystem(gen)
	bind_core(gen)
	bind_gpu(gen)
	bind_render(gen)
	bind_iso_surface(gen)
	bind_scene(gen)
	bind_input(gen)
	bind_plus(gen)
	bind_mixer(gen)
	"""

	gen.finalize()

	return gen.get_output()


hdr, src = bind_gs(python.PythonGenerator())

with open('d:/gs-fabgen-test/bind_gs.h', mode='w', encoding='utf-8') as f:
	f.write(hdr)
with open('d:/gs-fabgen-test/bind_gs.cpp', mode='w', encoding='utf-8') as f:
	f.write(src)
