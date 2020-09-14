# FABGen - The FABulous binding Generator for Go and Go
#	Copyright (C) 2020 Thomas Simonnet

import lang.go


def bind_std(gen):
	class GoConstCharPtrConverter(lang.go.GoTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return ''

		def get_type_api(self, module_name):
			return ''

		def to_c_call(self, in_var, out_var_p, is_pointer=False):
			out = f"{out_var_p.replace('&', '_')}, idFin{out_var_p.replace('&', '_')} := wrapString({in_var})\n"
			out += f"defer idFin{out_var_p.replace('&', '_')}()\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return "C.GoString(%s)" % (out_var)

	gen.bind_type(GoConstCharPtrConverter("string")).nobind = True
	gen.typedef('const char *', 'string')

	class GoIntConverter(lang.go.GoTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
			self.go_type = "C.int"

		def get_type_glue(self, gen, module_name):
			return ''

		def get_type_api(self, module_name):
			return ''

		def to_c_call(self, in_var, out_var_p, is_pointer):
			if is_pointer:
				out = f"{out_var_p.replace('&', '_')}, idFin{out_var_p.replace('&', '_')} := wrapInt({in_var})\n"
				out += f"defer idFin{out_var_p.replace('&', '_')}()\n"
			else:
				out = f"{out_var_p.replace('&', '_')} := C.int({in_var})\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return "int(%s)" % (out_var)

	gen.bind_type(GoIntConverter('int')).nobind = True
	gen.typedef('int32_t', 'int')
	gen.typedef('int64_t', 'int')
	gen.typedef('char32_t', 'int')
	gen.typedef('unsigned int32_t', 'int')
	gen.typedef('uint32_t', 'int')
	gen.typedef('size_t', 'int')


	class GoFloatConverter(lang.go.GoTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
			self.go_type = "C.float"

		def get_type_glue(self, gen, module_name):
			return ''

		def get_type_api(self, module_name):
			return ''

		def to_c_call(self, in_var, out_var_p, is_pointer):
			if is_pointer:
				out = f"{out_var_p.replace('&', '_')}, idFin{out_var_p.replace('&', '_')} := wrapFloat32({in_var})\n"
				out += f"defer idFin{out_var_p.replace('&', '_')}()\n"
			else:
				out = f"{out_var_p.replace('&', '_')} := C.float({in_var})\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return "float32(%s)" % (out_var)

	gen.bind_type(GoFloatConverter('float32')).nobind = True	
	gen.typedef('float', 'float32')