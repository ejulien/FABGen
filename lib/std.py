class StdSharedPtrProxyProtocol:
	def __init__(self, wrapped_conv):
		self.wrapped_conv = wrapped_conv

	def unwrap(self, conv, in_var, out_var):
		return '%s = %s->get();\n' % (out_var, in_var)

	def wrap(self, conv, in_var, out_var):
		return '%s = new std::shared_ptr<%s>(%s);\n' % (out_var, self.wrapped_conv.fully_qualified_name, in_var)
