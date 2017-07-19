class StdSharedPtrProxyProtocol:
	def __init__(self, wrapped_conv):
		self.wrapped_conv = wrapped_conv

	def unwrap(self, in_var, out_var):
		return '%s = %s->get();\n' % (out_var, in_var)
