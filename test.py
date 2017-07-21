import lua
import python

import lib.std


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


def bind_plugins(gen):
	gen.bind_function_overloads('gs::core::LoadPlugins', [('bool', [], []), ('bool', ['const char *path'], [])])
	gen.bind_function('gs::core::UnloadPlugins', 'void', [])


def bind_window_system(gen):
	window_conv = gen.begin_class('gs::RenderWindow')
	gen.end_class(window_conv)


def bind_scene(gen):
	gen.add_include('engine/scene.h')

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

	gen.end_class(shared_scene)

	#
	gen.add_include('engine/component.h')

	component = gen.begin_class('gs::core::Component', bound_name='Component_hide_me', noncopyable=True)
	gen.end_class(component)

	shared_component = gen.begin_class('std::shared_ptr<gs::core::Component>', bound_name='Component', features={'proxy': lib.std.SharedPtrProxyFeature(component)})
	gen.end_class(shared_component)

	#
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

	#
	gen.add_include('engine/node.h')

	node = gen.begin_class('gs::core::Node', bound_name='Node_hide_me', noncopyable=True)
	gen.end_class(node)

	shared_node = gen.begin_class('std::shared_ptr<gs::core::Node>', bound_name='Node', features={'proxy': lib.std.SharedPtrProxyFeature(node)})
	gen.bind_method(shared_node, 'GetComponent<gs::core::Transform>', 'std::shared_ptr<gs::core::Transform>', [], ['proxy'], bound_name='GetTransform')
	gen.end_class(shared_node)

	#
	gen.add_include('engine/light.h')

	gen.bind_enum('gs::core::Light::Model', ['Model_Point', 'Model_Linear', 'Model_Spot', 'Model_Last'], prefix='Light')
	gen.bind_enum('gs::core::Light::Shadow', ['Shadow_None', 'Shadow_ProjectionMap', 'Shadow_Map'], prefix='Light')


def bind_gpu(gen):
	gen.add_include('engine/texture.h')

	texture = gen.begin_class('gs::gpu::Texture', bound_name='Texture_hide_me', noncopyable=True)
	gen.end_class(texture)

	shared_texture = gen.begin_class('std::shared_ptr<gs::gpu::Texture>', bound_name='Texture', features={'proxy': lib.std.SharedPtrProxyFeature(texture)})
	gen.end_class(shared_texture)


def bind_render(gen):
	gen.bind_enum('gs::render::CullMode', ['CullBack', 'CullFront', 'CullNever'])
	gen.bind_enum('gs::render::BlendMode', ['BlendOpaque', 'BlendAlpha', 'BlendAdditive'])

	#
	gen.add_include('engine/render_geometry.h')

	geometry = gen.begin_class('gs::render::Geometry', bound_name='Geometry_hide_me', noncopyable=True)
	gen.end_class(geometry)

	shared_geometry = gen.begin_class('std::shared_ptr<gs::render::Geometry>', bound_name='Geometry', features={'proxy': lib.std.SharedPtrProxyFeature(geometry)})
	gen.end_class(shared_geometry)


def bind_plus(gen):
	gen.add_include('plus/plus.h')

	plus_conv = gen.begin_class('gs::Plus', noncopyable=True)

	gen.bind_constructor(plus_conv, [])

	gen.bind_method(plus_conv, 'CreateWorkers', 'void', [])
	gen.bind_method(plus_conv, 'DeleteWorkers', 'void', [])

	gen.bind_method(plus_conv, 'MountFilePath', 'void', ['const char *path'])

	#const gpu::sRenderer &GetRenderer() const { return renderer; }
	#const gpu::sRendererAsync &GetRendererAsync() const { return renderer_async; }

	#const render::sRenderSystem &GetRenderSystem() const { return render_system; }
	#const render::sRenderSystemAsync &GetRenderSystemAsync() const { return render_system_async; }

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

	#void InitExtern(gpu::sRenderer renderer, gpu::sRendererAsync renderer_async, render::sRenderSystem render_system, render::sRenderSystemAsync render_system_async);
	#void UninitExtern();

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

	#
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

	gen.bind_function('MountFileDriver', 'bool', ['std::shared_ptr<gs::io::Driver> driver'])


def bind_color(gen):
	gen.add_include('foundation/color.h')

	color = gen.begin_class('gs::Color')
	gen.end_class(color)


def bind_math(gen):
	gen.add_include('foundation/vector3.h')
	gen.add_include('foundation/vector3_api.h')
	gen.add_include('foundation/vector4.h')
	gen.add_include('foundation/matrix3.h')
	gen.add_include('foundation/matrix4.h')
	gen.add_include('foundation/matrix44.h')

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

	# Vector4
	vector4 = gen.begin_class('gs::Vector4')
	gen.bind_members(vector4, ['float x', 'float y', 'float z', 'float w'])

	gen.bind_constructor_overloads(vector4, [
		([], []),
		(['float x', 'float y', 'float z', 'float w'], [])
	])
	gen.end_class(vector4)

	gen.bind_arithmetic_ops_overloads(vector4, ['+', '-', '/'], [('gs::Vector4', ['gs::Vector4 &v'], []), ('gs::Vector4', ['float k'], [])])
	gen.bind_arithmetic_ops_overloads(vector4, ['*'], [('gs::Vector4', ['gs::Vector4 &v'], []), ('gs::Vector4', ['float k'], []), ('gs::Vector4', ['const gs::Matrix4 &m'], [])])

	gen.bind_inplace_arithmetic_ops_overloads(vector4, ['+=', '-=', '*=', '/='], [('gs::Vector4 &v', []), ('float k', [])])

	gen.bind_method(vector4, 'Abs', 'gs::Vector4', [])

	gen.bind_method(vector4, 'Normalized', 'gs::Vector4', [])

	#
	matrix3 = gen.begin_class('gs::Matrix3')
	gen.end_class(matrix3)

	#
	matrix4 = gen.begin_class('gs::Matrix4')

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

	#
	matrix44 = gen.begin_class('gs::Matrix44')
	gen.end_class(matrix44)

	# Vector3
	vector3 = gen.begin_class('gs::Vector3')

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

	gen.add_custom_init_code('''
	gs::core::Init();
''')

	gen.typedef('gs::uint', 'unsigned int')

	bind_time(gen)
	bind_math(gen)
	bind_color(gen)
	bind_plugins(gen)
	bind_filesystem(gen)
	bind_window_system(gen)
	bind_gpu(gen)
	bind_render(gen)
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

print("DONE")
