# FABGen - The FABulous binding Generator for CPython and Lua and Go
#	Copyright (C) 2020 Thomas Simonnet

import lang.go


def bind_stl(gen):
	gen.add_include('vector', True)
	gen.add_include('string', True)
	
	class GoStringConverter(lang.go.GoTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
			self.go_to_c_type = "*C.char"
			self.go_type = "string"
			
		def get_type_glue(self, gen, module_name):
			return ''

		def get_type_api(self, module_name):
			return ''

		def to_c_call(self, in_var, out_var_p, is_pointer=False):
			if is_pointer:
				out = f"{out_var_p.replace('&', '_')}1 := C.CString(*{in_var})\n"
				out += f"{out_var_p.replace('&', '_')} := &{out_var_p.replace('&', '_')}1\n"
			else:
				out = f"{out_var_p.replace('&', '_')}, idFin{out_var_p.replace('&', '_')} := wrapString({in_var})\n"
				out += f"defer idFin{out_var_p.replace('&', '_')}()\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return "C.GoString(%s)" % (out_var)

	gen.bind_type(GoStringConverter("std::string"))


def bind_function_T(gen, type, bound_name=None):
	class GoStdFunctionConverter(lang.go.GoTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return ""

	return gen.bind_type(GoStdFunctionConverter(type))


class GoSliceToStdVectorConverter(lang.go.GoTypeConverterCommon):
	def __init__(self, type, T_conv):
		native_type = f"std::vector<{T_conv.ctype}>"
		super().__init__(type, native_type, None, native_type)
		self.T_conv = T_conv

	def get_type_glue(self, gen, module_name):
		return ''
		
	def to_c_call(self, in_var, out_var_p, is_pointer):
		return ""

	def from_c_call(self, out_var, expr, ownership):
		return ""