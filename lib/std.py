class SharedPtrProxyFeature:
	def __init__(self, wrapped_conv):
		self.wrapped_conv = wrapped_conv

	def init(self, gen, conv):
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
