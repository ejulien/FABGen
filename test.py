import lua
import python

import lib.std


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
	float_ptr = gen.bind_ptr('float *', bound_name='PointerToFloat')
	gen.add_cast(binary_blob, float_ptr, lambda in_var, out_var: '%s = ((gs::BinaryBlob *)%s)->GetData();\n' % (out_var, in_var))

	#
	gen.bind_function('BinaryBlobBlur3d', 'void', ['gs::BinaryBlob &data', 'uint32_t width', 'uint32_t height', 'uint32_t depth'])


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


def bind_input(gen):
	gen.bind_enum('gs::InputDevice::Type', [
		'TypeAny', 'TypeKeyboard', 'TypeMouse', 'TypePad', 'TypeTouch', 'TypeHMD', 'TypeController'
	], bound_name='InputType', prefix='Input')

	gen.bind_enum('gs::InputDevice::KeyCode', [
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

	gen.bind_enum('gs::InputDevice::ButtonCode', [
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

	gen.bind_enum('gs::InputDevice::InputCode', [
		'InputAxisX', 'InputAxisY', 'InputAxisZ', 'InputAxisS', 'InputAxisT', 'InputAxisR',
		'InputRotX', 'InputRotY', 'InputRotZ', 'InputRotS', 'InputRotT', 'InputRotR',
		'InputButton0', 'InputButton1', 'InputButton2', 'InputButton3', 'InputButton4', 'InputButton5', 'InputButton6', 'InputButton7', 'InputButton8', 'InputButton9', 'InputButton10', 'InputButton11', 'InputButton12', 'InputButton13', 'InputButton14', 'InputButton15',
		'InputLast'
	])

	gen.bind_enum('gs::InputDevice::Effect', ['Vibrate', 'VibrateLeft', 'VibrateRight', 'ConstantForce'], bound_name='InputEffect', prefix='Input')
	gen.bind_enum('gs::InputDevice::MatrixCode', ['MatrixHead'], bound_name='InputMatrixCode', prefix='Input')

	#
	input_device = gen.begin_class('gs::InputDevice', bound_name='InputDevice_hide_me', noncopyable=True)
	gen.end_class(input_device)

	shared_input_device = gen.begin_class('std::shared_ptr<gs::InputDevice>', bound_name='InputDevice', features={'proxy': lib.std.SharedPtrProxyFeature(input_device)})
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
	window_conv = gen.begin_class('gs::RenderWindow')
	gen.end_class(window_conv)


def bind_core(gen):
	# core::Geometry
	gen.add_include('engine/geometry.h')

	geometry = gen.begin_class('gs::core::Geometry', bound_name='Geometry_hide_me', noncopyable=True)
	gen.end_class(geometry)

	shared_geometry = gen.begin_class('std::shared_ptr<gs::core::Geometry>', bound_name='Geometry', features={'proxy': lib.std.SharedPtrProxyFeature(geometry)})
	gen.end_class(shared_geometry)

	#


def bind_scene(gen):
	gen.add_include('engine/scene.h')

	# gs::core::Component
	gen.add_include('engine/component.h')

	component = gen.begin_class('gs::core::Component', bound_name='Component_hide_me', noncopyable=True)
	gen.end_class(component)

	shared_component = gen.begin_class('std::shared_ptr<gs::core::Component>', bound_name='Component', features={'proxy': lib.std.SharedPtrProxyFeature(component)})
	gen.end_class(shared_component)

	# gs::core::Transform
	gen.add_include('engine/transform.h')

	transform = gen.begin_class('gs::core::Transform', bound_name='Transform_hide_me', noncopyable=True)
	gen.end_class(transform)

	shared_transform = gen.begin_class('std::shared_ptr<gs::core::Transform>', bound_name='Transform', features={'proxy': lib.std.SharedPtrProxyFeature(transform)})
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

	gen.bind_enum('gs::core::Light::Model', ['Model_Point', 'Model_Linear', 'Model_Spot', 'Model_Last'], prefix='Light')
	gen.bind_enum('gs::core::Light::Shadow', ['Shadow_None', 'Shadow_ProjectionMap', 'Shadow_Map'], prefix='Light')

	# gs::core::RigidBody
	gen.add_include('engine/rigid_body.h')

	rigid_body = gen.begin_class('gs::core::RigidBody', bound_name='RigidBody_hide_me', noncopyable=True)
	gen.end_class(rigid_body)

	shared_rigid_body = gen.begin_class('std::shared_ptr<gs::core::RigidBody>', bound_name='RigidBody', features={'proxy': lib.std.SharedPtrProxyFeature(rigid_body)})
	gen.end_class(shared_rigid_body)

	# gs::core::Node
	gen.add_include('engine/node.h')

	node = gen.begin_class('gs::core::Node', bound_name='Node_hide_me', noncopyable=True)
	gen.end_class(node)

	shared_node = gen.begin_class('std::shared_ptr<gs::core::Node>', bound_name='Node', features={'proxy': lib.std.SharedPtrProxyFeature(node)})
	gen.bind_method(shared_node, 'GetComponent<gs::core::Transform>', 'std::shared_ptr<gs::core::Transform>', [], ['proxy'], bound_name='GetTransform')
	gen.end_class(shared_node)

	# gs::core::SceneSystem
	scene_system = gen.begin_class('gs::core::SceneSystem', bound_name='SceneSystem_hide_me', noncopyable=True)
	gen.end_class(scene_system)

	# gs::core::RenderableSystem
	gen.add_include('engine/renderable_system.h')

	renderable_system = gen.begin_class('gs::core::RenderableSystem', bound_name='RenderableSystem_hide_me', noncopyable=True)
	gen.end_class(renderable_system)

	shared_renderable_system = gen.begin_class('std::shared_ptr<gs::core::RenderableSystem>', bound_name='RenderableSystem', features={'proxy': lib.std.SharedPtrProxyFeature(renderable_system)})

	gen.bind_constructor_overloads(shared_renderable_system, [
		(['std::shared_ptr<gs::render::RenderSystem> render_system'], ['proxy']),
		(['std::shared_ptr<gs::render::RenderSystem> render_system', 'bool async'], ['proxy'])
	])

	gen.bind_method(shared_renderable_system, 'DrawGeometry', 'void', ['std::shared_ptr<gs::render::Geometry> geometry', 'const gs::Matrix4 &world'], ['proxy'])

	gen.end_class(shared_renderable_system)

	# gs::core::IPhysicSystem
	gen.add_include('engine/physic_system.h')

	physic_system = gen.begin_class('gs::core::IPhysicSystem', bound_name='PhysicSystem_hide_me', noncopyable=True)
	gen.end_class(physic_system)

	shared_physic_system = gen.begin_class('std::shared_ptr<gs::core::IPhysicSystem>', bound_name='PhysicSystem', features={'proxy': lib.std.SharedPtrProxyFeature(physic_system)})

	gen.bind_method(shared_physic_system, 'GetImplementationName', 'const std::string &', [], ['proxy'])

	def decl_get_set_method(clss, type, method_suffix, var_name, features=[]):
		gen.bind_method(clss, 'Get' + method_suffix, 'const %s &' % type, [], features)
		gen.bind_method(clss, 'Set' + method_suffix, 'void', ['const %s &%s' % (type, var_name)], features)

	decl_get_set_method(shared_physic_system, 'float', 'Timestep', 'timestep', ['proxy'])
	decl_get_set_method(shared_physic_system, 'bool', 'ForceRigidBodyToSleepOnCreation', 'force_sleep_body', ['proxy'])
	decl_get_set_method(shared_physic_system, 'gs::uint', 'ForceRigidBodyAxisLockOnCreation', 'force_axis_lock', ['proxy'])

	decl_get_set_method(shared_physic_system, 'gs::Vector3', 'Gravity', 'G', ['proxy'])

	def decl_comp_get_set_method(clss, comp_type, comp_var_name, type, method_suffix, var_name, features=[]):
		gen.bind_method(clss, 'Get' + method_suffix, 'const %s &' % type, ['const %s *%s' % (comp_type, comp_var_name)], features)
		gen.bind_method(clss, 'Set' + method_suffix, 'void', ['%s *%s' % (comp_type, comp_var_name), 'const %s &%s' % (type, var_name)], features)

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

	# gs::core::Scene
	scene = gen.begin_class('gs::core::Scene', bound_name='Scene_hide_me', noncopyable=True)
	gen.end_class(scene)

	shared_scene = gen.begin_class('std::shared_ptr<gs::core::Scene>', bound_name='Scene', features={'proxy': lib.std.SharedPtrProxyFeature(scene)})

	gen.bind_method(shared_scene, 'Clear', 'void', [], ['proxy'])
	gen.bind_method(shared_scene, 'Dispose', 'void', [], ['proxy'])
	gen.bind_method(shared_scene, 'IsReady', 'bool', [], ['proxy'])

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

	gen.bind_method(shared_scene, 'GetSystem<gs::core::RenderableSystem>', 'std::shared_ptr<gs::core::RenderableSystem>', [], ['proxy'], bound_name='GetRenderableSystem')
	gen.bind_method(shared_scene, 'GetSystem<gs::core::IPhysicSystem>', 'std::shared_ptr<gs::core::IPhysicSystem>', [], ['proxy'], bound_name='GetPhysicSystem')

	gen.end_class(shared_scene)


def bind_gpu(gen):
	gen.add_include('engine/texture.h')

	# gpu::Texture
	texture = gen.begin_class('gs::gpu::Texture', bound_name='Texture_hide_me', noncopyable=True)
	gen.end_class(texture)

	shared_texture = gen.begin_class('std::shared_ptr<gs::gpu::Texture>', bound_name='Texture', features={'proxy': lib.std.SharedPtrProxyFeature(texture)})
	gen.end_class(shared_texture)

	# gpu::Renderer
	gen.add_include('engine/renderer.h')

	renderer = gen.begin_class('gs::gpu::Renderer', bound_name='Renderer_hide_me', noncopyable=True)
	gen.end_class(renderer)

	shared_renderer = gen.begin_class('std::shared_ptr<gs::gpu::Renderer>', bound_name='Renderer', features={'proxy': lib.std.SharedPtrProxyFeature(renderer)})
	gen.end_class(shared_renderer)

	# gpu::RendererAsync
	gen.add_include('engine/renderer_async.h')

	renderer_async = gen.begin_class('gs::gpu::RendererAsync', bound_name='RendererAsync_hide_me', noncopyable=True)
	gen.end_class(renderer_async)

	shared_renderer_async = gen.begin_class('std::shared_ptr<gs::gpu::RendererAsync>', bound_name='RendererAsync', features={'proxy': lib.std.SharedPtrProxyFeature(renderer_async)})
	gen.end_class(shared_renderer_async)


def bind_render(gen):
	gen.bind_enum('gs::render::CullMode', ['CullBack', 'CullFront', 'CullNever'])
	gen.bind_enum('gs::render::BlendMode', ['BlendOpaque', 'BlendAlpha', 'BlendAdditive'])

	# render::Material
	gen.add_include('engine/render_material.h')

	material = gen.begin_class('gs::render::Material', bound_name='RenderMaterial_hide_me', noncopyable=True)
	gen.end_class(material)

	shared_material = gen.begin_class('std::shared_ptr<gs::render::Material>', bound_name='RenderMaterial', features={'proxy': lib.std.SharedPtrProxyFeature(material)})
	gen.end_class(shared_material)

	# render::Geometry
	gen.add_include('engine/render_geometry.h')

	geometry = gen.begin_class('gs::render::Geometry', bound_name='RenderGeometry_hide_me', noncopyable=True)
	gen.end_class(geometry)

	shared_geometry = gen.begin_class('std::shared_ptr<gs::render::Geometry>', bound_name='RenderGeometry', features={'proxy': lib.std.SharedPtrProxyFeature(geometry)})
	gen.bind_constructor_overloads(shared_geometry, [
		([], ['proxy']),
		(['const char *name'], ['proxy']),
	])
	gen.end_class(shared_geometry)

	# render::RenderSystem
	gen.add_include('engine/render_system.h')

	render_system = gen.begin_class('gs::render::RenderSystem', bound_name='RenderSystem_hide_me', noncopyable=True)
	gen.end_class(render_system)

	shared_render_system = gen.begin_class('std::shared_ptr<gs::render::RenderSystem>', bound_name='RenderSystem', features={'proxy': lib.std.SharedPtrProxyFeature(render_system)})
	gen.end_class(shared_render_system)

	# render::RenderSystem
	gen.add_include('engine/render_system_async.h')

	render_system_async = gen.begin_class('gs::render::RenderSystemAsync', bound_name='RenderSystemAsync_hide_me', noncopyable=True)
	gen.end_class(render_system_async)

	shared_render_system_async = gen.begin_class('std::shared_ptr<gs::render::RenderSystemAsync>', bound_name='RenderSystemAsync', features={'proxy': lib.std.SharedPtrProxyFeature(render_system_async)})
	gen.end_class(shared_render_system_async)


def bind_iso_surface(gen):
	gen.add_include('engine/iso_surface.h')

	iso_surface = gen.begin_class('gs::core::IsoSurface', bound_name='IsoSurface_hide_me')
	gen.end_class(iso_surface)

	shared_iso_surface = gen.begin_class('std::shared_ptr<gs::core::IsoSurface>', bound_name='IsoSurface', features={'proxy': lib.std.SharedPtrProxyFeature(iso_surface)})
	gen.bind_constructor(shared_iso_surface, [], ['proxy'])
	gen.bind_method(shared_iso_surface, 'Clear', 'void', [], ['proxy'])
	gen.bind_method(shared_iso_surface, 'AddTriangle', 'void', ['const gs::Vector3 &p0', 'const gs::Vector3 &p1', 'const gs::Vector3 &p2'], ['proxy'])
	gen.bind_method(shared_iso_surface, 'GetTriangleCount', 'gs::uint', [], ['proxy'])
	gen.end_class(shared_iso_surface)

	#
	lib.std.bind_future_T(gen, 'void', 'FutureVoid')

	gen.bind_ptr('float *')

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

	plus_conv = gen.begin_class('gs::Plus', noncopyable=True)

	gen.bind_constructor(plus_conv, [])

	gen.bind_method(plus_conv, 'CreateWorkers', 'void', [])
	gen.bind_method(plus_conv, 'DeleteWorkers', 'void', [])

	gen.bind_method(plus_conv, 'MountFilePath', 'void', ['const char *path'])

	gen.bind_method(plus_conv, 'GetRenderer', 'std::shared_ptr<gs::gpu::Renderer>', [])
	gen.bind_method(plus_conv, 'GetRendererAsync', 'std::shared_ptr<gs::gpu::RendererAsync>', [])

	gen.bind_method(plus_conv, 'GetRenderSystem', 'std::shared_ptr<gs::render::RenderSystem>', [])
	gen.bind_method(plus_conv, 'GetRenderSystemAsync', 'std::shared_ptr<gs::render::RenderSystemAsync>', [])

	gen.bind_enum('gs::Plus::AppEndCondition', ['EndOnEscapePressed', 'EndOnDefaultWindowClosed', 'EndOnAny'], prefix='App')

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

	#
	gen.bind_method(plus_conv, 'GetMouse', 'std::shared_ptr<gs::InputDevice>', [])
	gen.bind_method(plus_conv, 'GetKeyboard', 'std::shared_ptr<gs::InputDevice>', [])

	#void GetMousePos(float &x, float &y) const;
	#void GetMouseDt(float &x, float &y) const;

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

	# binding specific API
	gen.insert_binding_code('''static bool MountFileDriver(gs::io::sDriver driver) {
	return gs::g_fs.get().Mount(driver);
}
static bool MountFileDriver(gs::io::sDriver driver, const char *prefix) {
	return gs::g_fs.get().Mount(driver, prefix);
}
	''', 'Filesystem custom API')

	#
	io_driver = gen.begin_class('gs::io::Driver', bound_name='IODriver_hide_me', noncopyable=True)
	gen.end_class(io_driver)

	shared_io_driver = gen.begin_class('std::shared_ptr<gs::io::Driver>', bound_name='IODriver', features={'proxy': lib.std.SharedPtrProxyFeature(io_driver)})
	gen.end_class(shared_io_driver)

	#
	io_cfile = gen.begin_class('gs::io::CFile', bound_name='CFile_hide_me')  # TODO do not expose this type in the module
	gen.end_class(io_cfile)

	shared_io_cfile = gen.begin_class('std::shared_ptr<gs::io::CFile>', bound_name='StdFileDriver', features={'proxy': lib.std.SharedPtrProxyFeature(io_cfile)})
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


def bind_math(gen):
	gen.decl_class('gs::Vector3')
	gen.decl_class('gs::Vector4')
	gen.decl_class('gs::Matrix3')
	gen.decl_class('gs::Matrix4')
	gen.decl_class('gs::Matrix44')

	#
	gen.bind_enum('gs::math::RotationOrder', [
		'RotationOrderZYX',
		'RotationOrderYZX',
		'RotationOrderZXY',
		'RotationOrderXZY',
		'RotationOrderYXZ',
		'RotationOrderXYZ',
		'RotationOrderXY',
		'RotationOrder_Default'
		], storage_type='uint8_t')

	gen.bind_enum('gs::math::Axis', ['AxisX', 'AxisY', 'AxisZ', 'AxisNone'], storage_type='uint8_t')

	# gs::Vector4
	gen.add_include('foundation/vector4.h')

	vector4 = gen.begin_class('gs::Vector4')
	gen.bind_members(vector4, ['float x', 'float y', 'float z', 'float w'])

	gen.bind_constructor_overloads(vector4, [
		([], []),
		(['float x', 'float y', 'float z', 'float w'], [])
	])

	gen.bind_arithmetic_ops_overloads(vector4, ['+', '-', '/'], [('gs::Vector4', ['gs::Vector4 &v'], []), ('gs::Vector4', ['float k'], [])])
	gen.bind_arithmetic_ops_overloads(vector4, ['*'], [('gs::Vector4', ['gs::Vector4 &v'], []), ('gs::Vector4', ['float k'], []), ('gs::Vector4', ['const gs::Matrix4 &m'], [])])

	gen.bind_inplace_arithmetic_ops_overloads(vector4, ['+=', '-=', '*=', '/='], [('gs::Vector4 &v', []), ('float k', [])])

	gen.bind_method(vector4, 'Abs', 'gs::Vector4', [])

	gen.bind_method(vector4, 'Normalized', 'gs::Vector4', [])

	gen.end_class(vector4)

	# gs::Matrix3
	gen.add_include('foundation/matrix3.h')

	matrix3 = gen.begin_class('gs::Matrix3')
	gen.bind_static_members(matrix3, ['const gs::Matrix3 Zero', 'const gs::Matrix3 Identity'])
	gen.end_class(matrix3)

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

	#static Matrix4 LerpAsOrthonormalBase(const Matrix4 &a, const Matrix4 &b, float k, bool fast = false);

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


def bind_mixer(gen):
	gen.add_include('engine/engine_factories.h')
	gen.add_include('engine/mixer.h')

	# gs::AudioFormat
	gen.bind_enum('gs::AudioFormat::Encoding', ['PCM', 'WiiADPCM'], 'uint8_t', bound_name='AudioFormatEncoding', prefix='AudioFormat')
	gen.bind_enum('gs::AudioFormat::Type', ['Integer', 'Float'], 'uint8_t', bound_name='AudioFormatType', prefix='AudioType')

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
	gen.bind_enum('gs::AudioData::State', ['Ready', 'Ended', 'Disconnected'], bound_name='AudioDataState', prefix='AudioData')

	audio_data = gen.begin_class('gs::AudioData', bound_name='AudioData_hide_me', noncopyable=True)
	gen.end_class(audio_data)

	shared_audio_data = gen.begin_class('std::shared_ptr<gs::AudioData>', bound_name='AudioData', features={'proxy': lib.std.SharedPtrProxyFeature(audio_data)})

	gen.bind_method(shared_audio_data, 'GetFormat', 'gs::AudioFormat', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'Open', 'bool', ['const char *path'], ['proxy'])
	gen.bind_method(shared_audio_data, 'Close', 'void', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'GetState', 'gs::AudioData::State', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'Seek', 'bool', ['gs::time_ns t'], ['proxy'])

	#gen.bind_method(shared_audio_data, 'GetFrame', 'size_t', ['void *data', 'gs::time_ns &frame_t'], ['proxy']) TODO
	gen.bind_method(shared_audio_data, 'GetFrameSize', 'size_t', [], ['proxy'])

	gen.bind_method(shared_audio_data, 'SetTransform', 'void', ['const gs::Matrix4 &m'], ['proxy'])
	gen.bind_method(shared_audio_data, 'GetDataSize', 'size_t', [], ['proxy'])

	gen.end_class(shared_audio_data)

	# binding specific API
	gen.insert_binding_code('''static std::shared_ptr<gs::audio::Mixer> CreateMixer(const char *name) { return gs::core::g_mixer_factory.get().Instantiate(name); }
static std::shared_ptr<gs::audio::Mixer> CreateMixer() { return gs::core::g_mixer_factory.get().Instantiate(); }
	''', 'Mixer custom API')

	#
	gen.bind_enum('gs::audio::MixerLoopMode', ['MixerNoLoop', 'MixerRepeat', 'MixerLoopInvalidChannel'], 'uint8_t')
	gen.bind_enum('gs::audio::MixerPlayState', ['MixerStopped', 'MixerPlaying', 'MixerPaused', 'MixerStateInvalidChannel'], 'uint8_t')

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
	sound = gen.begin_class('gs::audio::Sound', bound_name='Sound_hide_me', noncopyable=True)
	gen.end_class(sound)

	shared_sound = gen.begin_class('std::shared_ptr<gs::audio::Sound>', bound_name='Sound', features={'proxy': lib.std.SharedPtrProxyFeature(sound)})
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

	audio_mixer = gen.begin_class('gs::audio::Mixer', bound_name='Mixer_hide_me', noncopyable=True)
	gen.end_class(audio_mixer)

	shared_audio_mixer = gen.begin_class('std::shared_ptr<gs::audio::Mixer>', bound_name='Mixer', features={'proxy': lib.std.SharedPtrProxyFeature(audio_mixer)})
	bind_mixer_api(shared_audio_mixer, ['proxy'])
	gen.end_class(shared_audio_mixer)

	gen.bind_function_overloads('CreateMixer', [('std::shared_ptr<gs::audio::Mixer>', [], []), ('std::shared_ptr<gs::audio::Mixer>', ['const char *name'], [])])


def bind_gs(gen):
	gen.start('gs')

	gen.add_include('engine/engine.h')
	gen.add_include('engine/engine_plugins.h')

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

	gen.typedef('gs::uint', 'unsigned int')

	gen.insert_code('void out_values_function_call(int &a, int *b) { a = 8; *b = 14; }\n\n')

	gen.bind_function('out_values_function_call', 'void', ['int &a', 'int *b'])

	if 0:
		bind_binary_blob(gen)
		bind_time(gen)
		bind_math(gen)
		bind_color(gen)
		bind_engine(gen)
		bind_plugins(gen)
		bind_filesystem(gen)
		bind_window_system(gen)
		bind_core(gen)
		bind_gpu(gen)
		bind_render(gen)
		bind_iso_surface(gen)
		bind_scene(gen)
		bind_input(gen)
		bind_plus(gen)
		bind_mixer(gen)

	gen.finalize()

	return gen.get_output()


hdr, src = bind_gs(python.PythonGenerator())

with open('d:/gs-fabgen-test/bind_gs.h', mode='w', encoding='utf-8') as f:
	f.write(hdr)
with open('d:/gs-fabgen-test/bind_gs.cpp', mode='w', encoding='utf-8') as f:
	f.write(src)
