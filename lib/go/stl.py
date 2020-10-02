# FABGen - The FABulous binding Generator for CPython and Lua and Go
#	Copyright (C) 2020 Thomas Simonnet

import lang.go


def bind_stl(gen):
	gen.add_include('vector', True)
	gen.add_include('string', True)
	
	# class GoStringConverter(lang.go.GoTypeConverterCommon):
	# 	def get_type_glue(self, gen, module_name):
	# 		return ''

	# gen.bind_type(GoStringConverter('std::string'))


def bind_function_T(gen, type, bound_name=None):
	class GoStdFunctionConverter(lang.go.GoTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
# 			func = self.ctype.scoped_typename.parts[-1].template.function

# 			# check C
# 			check = 'bool %s(PyObject *o) { return PyCallable_Check(o) ? true : false; }\n' % self.check_func

# 			# to C
# 			rval = 'void' if hasattr(func, 'void_rval') else str(func.rval)

# 			args = []
# 			if hasattr(func, 'args'):
# 				args = [str(arg) for arg in func.args]

# 			rbind_helper = '_rbind_' + self.bound_name  # helper to call from C to Lua
# 			parms = ['%s v%d' % (arg, idx) for idx, arg in enumerate(args)]
# 			gen.rbind_function(rbind_helper, rval, parms, True)

# 			to_c = '''\
# void %s(PyObject *o, void *obj) {
# 	auto ref = std::make_shared<PythonValueRef>(o);
# 	*((%s*)obj) = [=](%s) -> %s {
# ''' % (self.to_c_func, self.ctype, ', '.join(['%s v%d' % (parm, idx) for idx, parm in enumerate(args)]), rval)

# 			if rval != 'void':
# 				to_c += '		return '

# 			if len(args) > 0:
# 				to_c += '%s(ref->Get(), %s);\n' % (gen.apply_api_prefix(rbind_helper), ', '.join(['v%d' % idx for idx in range(len(args))]))
# 			else:
# 				to_c += '%s(ref->Get());\n' % gen.apply_api_prefix(rbind_helper)

# 			to_c += ""

# 			# from C
# 			from_c = ""

			return "" #check + to_c + from_c

	return gen.bind_type(GoStdFunctionConverter(type))


class GoSliceToStdVectorConverter(lang.go.GoTypeConverterCommon):
	def __init__(self, type, T_conv):
		native_type = f"std::vector<{T_conv.ctype}>"
		super().__init__(type, native_type, None, native_type)
		self.T_conv = T_conv

	def get_type_glue(self, gen, module_name):
		return ''
	#c	
# WrapVectorOfInt WrapConstructorVectorOfInt1(size_t len, int *buf) { return (void *)(new std::vector<int>(buf, buf + len)); }

	# h	
# extern WrapVectorOfInt WrapConstructorVectorOfInt1(size_t len, int *buf);
	
	# go
	# sh := (*reflect.SliceHeader)(unsafe.Pointer(&sequence))
	# retval := C.WrapConstructorVectorOfInt1(C.size_t(sh.Len), (*C.int)(unsafe.Pointer(sh.Data)))

	def to_c_call(self, in_var, out_var_p, is_pointer):
		if is_pointer:
				out = f"{out_var_p.replace('&', '_')} := (*C.WrapBool)(unsafe.Pointer({in_var}))\n"
		else:
			out = f"{out_var_p.replace('&', '_')} := C.bool({in_var})\n"
		return out

	def from_c_call(self, out_var, expr, ownership):
		return "bool(%s)" % (out_var)