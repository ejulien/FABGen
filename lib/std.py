class SharedPtrProxyFeature:
	def __init__(self, wrapped_conv):
		self.wrapped_conv = wrapped_conv

	def init_type_converter(self, gen, conv):
		# declare shared_ptr<T> to T cast support
		cast_function_name = 'cast_%s_to_%s' % (conv.bound_name, self.wrapped_conv.bound_name)

		gen.insert_code('''static void *%s(void *ptr) { return ((%s *)ptr)->get(); }\n
''' % (cast_function_name, conv.fully_qualified_name), True, False)

		def cast_delegate(in_var, out_var):
			return '%s = %s(%s);\n' % (out_var, cast_function_name, in_var)

		gen.add_cast(conv, self.wrapped_conv, cast_delegate)

	def unwrap(self, in_var, out_var):
		return '%s = %s->get();\n' % (out_var, in_var)

	def wrap(self, in_var, out_var):
		return '%s = new std::shared_ptr<%s>(%s);\n' % (out_var, self.wrapped_conv.fully_qualified_name, in_var)


class VectorSequenceFeature:
	def __init__(self, wrapped_conv):
		self.wrapped_conv = wrapped_conv

	def init_type_converter(self, gen, conv):
		pass

	def get_size(self, self_var, out_var):
		return '%s = %s->size();\n' % (out_var, self_var)

	def get_item(self, self_var, idx, out_var, error_var):
		out = 'if (%s < %s->size())\n' % (idx, self_var)
		out += '	%s = (*%s)[%s];\n' % (out_var, self_var, idx)
		out += 'else\n'
		out += '	%s = true;\n' % error_var
		return out

	def set_item(self, self_var, idx, in_var, error_var):
		out = 'if (%s < %s->size())\n' % (idx, self_var)
		out += '	(*%s)[%s] = %s;\n' % (self_var, idx, in_var)
		out += 'else\n'
		out += '	%s = true;\n' % error_var
		return out


def bind_future_T(gen, T, bound_name=None):
	gen.add_include('future', is_system=True)

	gen.bind_enum('std::future_status', ['deferred', 'ready', 'timeout'], prefix='future_')

	future = gen.begin_class('std::future<%s>' % T, bound_name=bound_name, noncopyable=True)

	gen.bind_method(future, 'get', T, [])
	gen.bind_method(future, 'valid', 'bool', [])
	gen.bind_method(future, 'wait', 'void', [])
	#gen.bind_method(future, 'wait_for', 'std::future_status', ['const std::chrono::duration<Rep,Period> &timeout_duration'])
	#gen.bind_method(future, 'wait_until', 'std::future_status', ['const std::chrono::time_point<Clock,Duration> &timeout_time'])

	gen.end_class(future)
	return future
