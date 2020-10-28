# FABGen - The FABulous binding Generator for Go and Go
#	Copyright (C) 2020 Thomas Simonnet

import lang.go


def bind_std(gen):
	class GoConstCharPtrConverter(lang.go.GoTypeConverterCommon):
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

	gen.bind_type(GoConstCharPtrConverter("const char *"))

	class GoBasicTypeConverter(lang.go.GoTypeConverterCommon):
		def __init__(self, type, c_type, go_type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
			self.go_to_c_type = c_type
			self.go_type = go_type

		def get_type_glue(self, gen, module_name):
			return ''

		def get_type_api(self, module_name):
			return ''

		def to_c_call(self, in_var, out_var_p, is_pointer):
			if is_pointer:
				out = f"{out_var_p.replace('&', '_')} := (*{self.go_to_c_type})(unsafe.Pointer({in_var}))\n"
			else:
				out = f"{out_var_p.replace('&', '_')} := {self.go_to_c_type}({in_var})\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return f"{self.go_type}({out_var})"

	gen.bind_type(GoBasicTypeConverter("char", "C.char", "int8"))

	gen.bind_type(GoBasicTypeConverter("unsigned char", "C.uchar", "uint8"))
	gen.bind_type(GoBasicTypeConverter("uint8_t", "C.uchar", "uint8"))

	gen.bind_type(GoBasicTypeConverter("short", "C.short", "int16"))
	gen.bind_type(GoBasicTypeConverter("int16_t", "C.short", "int16"))
	gen.bind_type(GoBasicTypeConverter("char16_t", "C.short", "int16"))

	gen.bind_type(GoBasicTypeConverter("uint16_t", "C.ushort", "uint16"))
	gen.bind_type(GoBasicTypeConverter("unsigned short", "C.ushort ", "uint16"))
	
	gen.bind_type(GoBasicTypeConverter("int32", "C.int", "int32"))
	gen.bind_type(GoBasicTypeConverter("int", "C.int", "int32"))
	gen.bind_type(GoBasicTypeConverter("int32_t", "C.int", "int32"))
	gen.bind_type(GoBasicTypeConverter("char32_t", "C.int", "int32"))
	gen.bind_type(GoBasicTypeConverter("size_t", "C.size_t", "int32"))

	gen.bind_type(GoBasicTypeConverter("uint32_t", "C.uint", "uint32"))
	gen.bind_type(GoBasicTypeConverter("unsigned int32_t", "C.uint", "uint32"))
	gen.bind_type(GoBasicTypeConverter("unsigned int", "C.uint", "uint32"))

	gen.bind_type(GoBasicTypeConverter("int64_t", "C.longlong", "int64"))
	gen.bind_type(GoBasicTypeConverter("long", "C.long", "int64"))

	gen.bind_type(GoBasicTypeConverter("float32", "C.float", "float32"))
	gen.bind_type(GoBasicTypeConverter("float", "C.float", "float32"))
	
	gen.bind_type(GoBasicTypeConverter("intptr_t", "C.longlong", "uintptr"))

	gen.bind_type(GoBasicTypeConverter("unsigned long", "C.ulong", "uint64"))
	gen.bind_type(GoBasicTypeConverter("uint64_t", "C.ulonglong ", "uint64"))
	gen.bind_type(GoBasicTypeConverter("double", "C.double", "float64"))	
	
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
				out = f"{out_var_p.replace('&', '_')} := (*C.bool)(unsafe.Pointer({in_var}))\n"
			else:
				out = f"{out_var_p.replace('&', '_')} := C.bool({in_var})\n"
			return out

		def from_c_call(self, out_var, expr, ownership):
			return "bool(%s)" % (out_var)

	gen.bind_type(GoBoolConverter('bool')).nobind = True