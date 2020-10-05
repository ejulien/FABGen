# FABGen - The FABulous binding Generator for Go and Go
#	Copyright (C) 2020 Thomas Simonnet

import lang.go


def bind_std(gen):
	class GoConstCharPtrConverter(lang.go.GoTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
			self.go_to_c_type = "*C.char"
			
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
	gen.typedef('char *', 'string')
	gen.typedef('const char *', 'string')
	gen.typedef('std::string', 'string')

	class GoIntConverter(lang.go.GoTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
			self.go_to_c_type = "C.int"
			self.go_type = "int32"

		def get_type_glue(self, gen, module_name):
			return ''

		def get_type_api(self, module_name):
			return ''

		def to_c_call(self, in_var, out_var_p, is_pointer):
			if is_pointer:
				out = f"{out_var_p.replace('&', '_')} := (*C.int)(unsafe.Pointer({in_var}))\n"
			else:
				out = f"{out_var_p.replace('&', '_')} := C.int({in_var})\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return "int32(%s)" % (out_var)

	gen.bind_type(GoIntConverter('int32'))
	gen.bind_type(GoIntConverter('int'))
	gen.bind_type(GoIntConverter('int16_t'))
	gen.bind_type(GoIntConverter('int32_t'))
	gen.bind_type(GoIntConverter('int64_t'))
	gen.bind_type(GoIntConverter('char32_t'))
	gen.bind_type(GoIntConverter('unsigned int32_t'))
	gen.bind_type(GoIntConverter('unsigned int'))
	gen.bind_type(GoIntConverter('uint32_t'))

	class GoSizeTConverter(lang.go.GoTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
			self.go_to_c_type = "C.size_t"
			self.go_type = "int32"

		def get_type_glue(self, gen, module_name):
			return ''

		def get_type_api(self, module_name):
			return ''

		def to_c_call(self, in_var, out_var_p, is_pointer):
			if is_pointer:
				out = f"{out_var_p.replace('&', '_')} := (*C.size_t)(unsafe.Pointer({in_var}))\n"
			else:
				out = f"{out_var_p.replace('&', '_')} := C.size_t({in_var})\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return "int32(%s)" % (out_var)

	gen.bind_type(GoSizeTConverter('size_t'))

	class GoFloatConverter(lang.go.GoTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
			self.go_to_c_type = "C.float"
			self.go_type = "float32"

		def get_type_glue(self, gen, module_name):
			return ''

		def get_type_api(self, module_name):
			return ''

		def to_c_call(self, in_var, out_var_p, is_pointer):
			if is_pointer:
				out = f"{out_var_p.replace('&', '_')} := (*C.float)(unsafe.Pointer({in_var}))\n"
			else:
				out = f"{out_var_p.replace('&', '_')} := C.float({in_var})\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return "float32(%s)" % (out_var)

	gen.bind_type(GoFloatConverter('float32'))
	gen.bind_type(GoFloatConverter('float'))
	
	class GoBoolConverter(lang.go.GoTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
			self.go_to_c_type = "C.bool"

		def get_type_glue(self, gen, module_name):
			return ''

		def get_type_api(self, module_name):
			return ''

		def to_c_call(self, in_var, out_var_p, is_pointer):
			if is_pointer:
				out = f"{out_var_p.replace('&', '_')} := (*C.WrapBool)(unsafe.Pointer({in_var}))\n"
			else:
				out = f"{out_var_p.replace('&', '_')} := C.bool({in_var})\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return "bool(%s)" % (out_var)

	gen.bind_type(GoBoolConverter('bool')).nobind = True