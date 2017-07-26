def bind_future_T(gen, T, bound_name=None):
	gen.add_include('future', is_system=True)

	gen.bind_named_enum('std::future_status', ['deferred', 'ready', 'timeout'], prefix='future_')

	future = gen.begin_class('std::future<%s>' % T, bound_name=bound_name, noncopyable=True, moveable=True)

	gen.bind_method(future, 'get', T, [])
	gen.bind_method(future, 'valid', 'bool', [])
	gen.bind_method(future, 'wait', 'void', [])
	#gen.bind_method(future, 'wait_for', 'std::future_status', ['const std::chrono::duration<Rep,Period> &timeout_duration'])
	#gen.bind_method(future, 'wait_until', 'std::future_status', ['const std::chrono::time_point<Clock,Duration> &timeout_time'])

	gen.end_class(future)
	return future
