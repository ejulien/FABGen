# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien


# It declares that the type converter for std::shared_ptr<T> should be a pointer to T, and that it
# should be wrapped in a std::shared_ptr<T> when returned from a function
class SharedPtrProxyFeature:
	def __init__(self, wrapped_conv):
		self.wrapped_conv = wrapped_conv

	def init_type_converter(self, gen, conv):
		# declare shared_ptr<T> to T cast support
		gen.add_cast(conv, self.wrapped_conv, lambda in_var, out_var: '%s = ((%s *)%s)->get();\n' % (out_var, conv.ctype, in_var))
		conv._inline = True  # use inline alloc where possible
		conv._supports_deep_compare = True  # supports deep comparison by default (compare wrapped (T*)'s and not (std::shared_ptr<T>*)'s)
		conv._is_pointer = True  # should be checked against empty return value

	def unwrap(self, in_var, out_var):
		return '%s = %s->get();\n' % (out_var, in_var)

	def wrap(self, in_var, out_var):
		return '%s = new std::shared_ptr<%s>(%s);\n' % (out_var, self.wrapped_conv.ctype, in_var)


def bind_future_T(gen, T, bound_name=None):
    	
	''' It binds the std::future<T> class to Python
	
	:param gen: the generator object
	:param T: The type of the future
	:param bound_name: The name of the class in the generated code
	:return: A future object. '''
	
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


def bind_function_T(gen, type, bound_name=None):
    	
	''' It generates the code to bind a function object to the target language
	
	:param gen: The generator object
	:param type: The type of the function pointer
	:param bound_name: The name of the bound function. If not specified, the name of the function will
	be used '''
	
	gen.add_include('functional', is_system=True)
	gen.add_include('memory', is_system=True)

	if gen.get_language() == 'CPython':
		import lib.cpython.stl
		lib.cpython.stl.bind_function_T(gen, type, bound_name)
	elif gen.get_language() == 'Lua':
		import lib.lua.stl
		lib.lua.stl.bind_function_T(gen, type, bound_name)
	elif gen.get_language() == 'Go':
		import lib.go.stl
		lib.go.stl.bind_function_T(gen, type, bound_name)
  
  	elif gen.get_language() == 'Fsharp':
    	import lib.fsharp.stl
		lib.fsharp.stl.bind_function_T(gen, type, bound_name)
	
	elif gen.get_language() == 'API':
		import lib.xml.stl
		lib.xml.stl.bind_function_T(gen, type, bound_name)
	else:
		raise NameError("Unsupported generator: " + gen.get_language())
