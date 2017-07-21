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


def bind_plugins(gen):
	gen.bind_function_overloads('gs::core::LoadPlugins', [('bool', [], []), ('bool', ['const char *path'], [])])
	gen.bind_function('gs::core::UnloadPlugins', 'void', [])


def bind_window_system(gen):
	window_conv = gen.begin_class('gs::RenderWindow')
	gen.end_class(window_conv)


def bind_plus(gen):
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
	gen.add_include("foundation/filesystem.h")
	gen.add_include("foundation/io_cfile.h")

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


def bind_mixer(gen):
	gen.add_include('engine/engine_factories.h')
	gen.add_include('engine/mixer.h')

	# binding specific API
	gen.insert_binding_code('''static std::shared_ptr<gs::audio::Mixer> CreateMixer(const char *name) { return gs::core::g_mixer_factory.get().Instantiate(name); }
static std::shared_ptr<gs::audio::Mixer> CreateMixer() { return gs::core::g_mixer_factory.get().Instantiate(); }
	''', 'Mixer custom API')

	#
	gen.bind_enum('gs::audio::MixerLoopMode', ['MixerNoLoop', 'MixerRepeat', 'MixerLoopInvalidChannel'], 'uint8_t');
	gen.bind_enum('gs::audio::MixerPlayState', ['MixerStopped', 'MixerPlaying', 'MixerPaused', 'MixerStateInvalidChannel'], 'uint8_t');

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

		gen.bind_method(conv, 'LoadSound', 'std::shared_ptr<gs::audio::Sound>', ['const char *path'], features)
		gen.bind_method_overloads(conv, 'Start', [
			('gs::audio::MixerChannel', ['gs::audio::Sound &sound'], features),
			('gs::audio::MixerChannel', ['gs::audio::Sound &sound', 'gs::audio::MixerChannelState state'], features),
			('gs::audio::MixerChannel', ['gs::audio::Sound &sound', 'gs::audio::MixerChannelLocation location'], features),
			('gs::audio::MixerChannel', ['gs::audio::Sound &sound', 'gs::audio::MixerChannelLocation location', 'gs::audio::MixerChannelState state'], features)
		])

		gen.bind_method(conv, 'GetPlayState', 'gs::audio::MixerPlayState', ['gs::audio::MixerChannel channel'], features)

		gen.bind_method(conv, 'GetChannelState', 'gs::audio::MixerChannelState', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'SetChannelState', 'void', ['gs::audio::MixerChannel channel', 'gs::audio::MixerChannelState state'], features)

		gen.bind_method(conv, 'GetChannelLocation', 'gs::audio::MixerChannelLocation', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'SetChannelLocation', 'void', ['gs::audio::MixerChannel channel', 'gs::audio::MixerChannelLocation location'], features)

		gen.bind_method(conv, 'Stop', 'void', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'Pause', 'void', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'Resume', 'void', ['gs::audio::MixerChannel channel'], features)
		gen.bind_method(conv, 'StopAll', 'void', [], features)

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

	bind_time(gen)
	bind_plugins(gen)
	bind_filesystem(gen)
	bind_window_system(gen)
	bind_plus(gen)
	bind_math(gen)
	bind_mixer(gen)

	gen.finalize()

	return gen.get_output()


hdr, src = bind_gs(python.PythonGenerator())

with open('d:/gs-fabgen-test/bind_gs.h', mode='w', encoding='utf-8') as f:
	f.write(hdr)
with open('d:/gs-fabgen-test/bind_gs.cpp', mode='w', encoding='utf-8') as f:
	f.write(src)

print("DONE")
