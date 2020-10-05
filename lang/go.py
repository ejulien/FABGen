# Harfang - The Fabulous binding Generator for CPython and Go
# 	Copyright (C) 2020 Thomas Simonnet

import os
import sys
import time
import importlib

import argparse

import gen
import lib


def route_lambda(name):
	return lambda args: "%s(%s);" % (name, ", ".join(args))


def clean_name(name):
	new_name = str(name).strip().replace("_", "").replace(":", "")
	if new_name in ["type"]:
		return new_name + "Go"
	return new_name


def clean_name_with_title(name):
	new_name = ""
	if "_" in name:
		# redo a special string.title()
		next_is_forced_uppercase = True
		for c in name:
			if c in ["*", "&"]:
				new_name += c
			elif c in ["_", "-"]:
				next_is_forced_uppercase = True
			else:
				if next_is_forced_uppercase:
					next_is_forced_uppercase = False
					new_name += c.capitalize()
				else:
					new_name += c
	else:
		# make sur the first letter is captialize
		first_letter_checked = False
		for c in name:
			if c in ["*", "&"] or first_letter_checked:
				new_name += c
			elif not first_letter_checked:
				first_letter_checked = True
				new_name += c.capitalize()
	return new_name.strip().replace("_", "").replace(":", "")


class GoTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
		super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
		self.go_to_c_type = None
		self.go_type = None

	def get_type_api(self, module_name):
		out = "// type API for %s\n" % self.ctype
		if self.c_storage_class:
			out += "struct %s;\n" % self.c_storage_class
		if self.c_storage_class:
			out += "void %s(int idx, void *obj, %s &storage);\n" % (self.to_c_func, self.c_storage_class)
		else:
			out += "void %s(int idx, void *obj);\n" % self.to_c_func
		out += "int %s(void *obj, OwnershipPolicy);\n" % self.from_c_func
		out += "\n"
		return out

	def to_c_call(self, in_var, out_var_p, is_pointer):
		out = ""
		if self.c_storage_class:
			c_storage_var = "storage_%s" % out_var_p.replace("&", "_")
			out += "%s %s;\n" % (self.c_storage_class, c_storage_var)
			out += "%s(%s, (void *)%s, %s);\n" % (self.to_c_func, in_var, out_var_p, c_storage_var)
		else:
			out += "%s(%s, %s);\n" % (self.to_c_func, in_var, out_var_p)
		return out

	def from_c_call(self, out_var, expr, ownership):
		return "%s((void *)%s, %s);\n" % (self.from_c_func, expr, ownership)


class DummyTypeConverter(gen.TypeConverter):
	def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
		super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)

	def get_type_api(self, module_name):
		return ""

	def to_c_call(self, in_var, out_var_p, is_pointer):
		return ""

	def from_c_call(self, out_var, expr, ownership):
		return ""

	def check_call(self, in_var):
		return ""

	def get_type_glue(self, gen, module_name):
		return ""


class GoPtrTypeConverter(gen.TypeConverter):
	def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
		super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)

	def get_type_api(self, module_name):
		return ""

	def to_c_call(self, in_var, out_var_p, is_pointer):
		return ""

	def from_c_call(self, out_var, expr, ownership):
		return ""

	def check_call(self, in_var):
		return ""

	def get_type_glue(self, gen, module_name):
		return ""


#

class GoClassTypeDefaultConverter(GoTypeConverterCommon):
	def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
		super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)

	def is_type_class(self):
		return True

	def get_type_api(self, module_name):
		return ""

	def to_c_call(self, in_var, out_var_p, is_pointer):
		out = f"{out_var_p.replace('&', '_')} := {in_var}.h\n"
		return out

	def from_c_call(self, out_var, expr, ownership):
		return ""

	def check_call(self, in_var):
		return ""

	def get_type_glue(self, gen, module_name):
		return ""


class GoExternTypeConverter(GoTypeConverterCommon):
	def __init__(self, type, to_c_storage_type, bound_name, module):
		super().__init__(type, to_c_storage_type, bound_name)
		self.module = module

	def get_type_api(self, module_name):
		return ''

	def to_c_call(self, in_var, out_var_p):
		out = ''
		if self.c_storage_class:
			c_storage_var = 'storage_%s' % out_var_p.replace('&', '_')
			out += '%s %s;\n' % (self.c_storage_class, c_storage_var)
			out += '(*%s)(%s, (void *)%s, %s);\n' % (self.to_c_func, in_var, out_var_p, c_storage_var)
		else:
			out += '(*%s)(%s, (void *)%s);\n' % (self.to_c_func, in_var, out_var_p)
		return out

	def from_c_call(self, out_var, expr, ownership):
		return "%s = (*%s)((void *)%s, %s);\n" % (out_var, self.from_c_func, expr, ownership)

	def check_call(self, in_var):
		return "(*%s)(%s)" % (self.check_func, in_var)

	def get_type_glue(self, gen, module_name):
		out = '// extern type API for %s\n' % self.ctype
		if self.c_storage_class:
			out += 'struct %s;\n' % self.c_storage_class
		out += 'bool (*%s)(void *o) = nullptr;\n' % self.check_func
		if self.c_storage_class:
			out += 'void (*%s)(void *o, void *obj, %s &storage) = nullptr;\n' % (self.to_c_func, self.c_storage_class)
		else:
			out += 'void (*%s)(void *o, void *obj) = nullptr;\n' % self.to_c_func
		out += 'void *(*%s)(void *obj, OwnershipPolicy) = nullptr;\n' % self.from_c_func
		out += '\n'
		return out



class GoGenerator(gen.FABGen):
	default_ptr_converter = GoPtrTypeConverter
	default_class_converter = GoClassTypeDefaultConverter
	default_extern_converter = GoExternTypeConverter

	def __init__(self):
		super().__init__()
		self.check_self_type_in_ops = True
		self.go = ""

	def get_language(self):
		return "Go"

	def output_includes(self):
		pass

	def start(self, module_name):
		super().start(module_name)

		# std
		self.bind_type(DummyTypeConverter("char")).nobind = True
		self.bind_type(DummyTypeConverter("short")).nobind = True
		self.bind_type(DummyTypeConverter("long")).nobind = True
		self.bind_type(DummyTypeConverter("char16_t")).nobind = True
		self.bind_type(DummyTypeConverter("unsigned char")).nobind = True
		self.bind_type(DummyTypeConverter("unsigned short")).nobind = True
		self.bind_type(DummyTypeConverter("unsigned long")).nobind = True
		self.bind_type(DummyTypeConverter("uint8_t")).nobind = True
		self.bind_type(DummyTypeConverter("uint16_t")).nobind = True
		self.bind_type(DummyTypeConverter("uint64_t")).nobind = True
		self.bind_type(DummyTypeConverter("intptr_t")).nobind = True
		self.bind_type(DummyTypeConverter("double", bound_name="float64")).nobind = True

		self._source += self.get_binding_api_declaration()
		# self._header += '#include "fabgen.h"\n'
		# self._header += self.get_binding_api_declaration()

	# kill a bunch of functions we don't care about
	def set_error(self, type, reason):
		return ""

	def get_self(self, ctx):
		return ""

	def get_var(self, i, ctx):
		return ""

	def open_proxy(self, name, max_arg_count, ctx):
		return ""

	def _proto_call(self, self_conv, proto, expr_eval, ctx, fixed_arg_count=None):
		return ""

	def _bind_proxy(self, name, self_conv, protos, desc, expr_eval, ctx, fixed_arg_count=None):
		return ""

	def close_proxy(self, ctx):
		return ""

	def proxy_call_error(self, msg, ctx):
		return ""

	def return_void_from_c(self):
		return ""

	def rval_from_nullptr(self, out_var):
		return ""

	def rval_from_c_ptr(self, conv, out_var, expr, ownership):
		return ""

	def commit_from_c_vars(self, rvals, ctx="default"):
		return ""

	def rbind_function(self, name, rval, args, internal=False):
		return ""

	#
	def get_binding_api_declaration(self):
		type_info_name = gen.apply_api_prefix("type_info")

		out = '''\
struct %s {
	uint32_t type_tag;
	const char *c_type;
	const char *bound_name;

	bool (*check)(void* p);
	void (*to_c)(void *p, void *out);
	int (*from_c)(void *obj, OwnershipPolicy policy);
};\n
''' % type_info_name

		out += "// return a type info from its type tag\n"
		out += "%s *%s(uint32_t type_tag);\n" % (type_info_name, gen.apply_api_prefix("get_bound_type_info"))

		out += "// return a type info from its type name\n"
		out += "%s *%s(const char *type);\n" % (type_info_name, gen.apply_api_prefix("get_c_type_info"))

		out += "// returns the typetag of a userdata object, nullptr if not a Fabgen object\n"
		out += "uint32_t %s(void* p);\n\n" % gen.apply_api_prefix("get_wrapped_object_type_tag")

		return out

	def output_binding_api(self):
		type_info_name = gen.apply_api_prefix("type_info")

		# self._source += '// Note: Types using a storage class for conversion are not listed here.\n'
		# self._source += 'static std::map<uint32_t, %s> __type_tag_infos;\n\n' % type_info_name

		# self._source += 'static void __initialize_type_tag_infos() {\n'
		# for type in self._bound_types:
		# 	if not type.c_storage_class:
		# 		self._source += '	__type_tag_infos[%s] = {%s, "%s", "%s", %s, %s, %s};\n' % (type.type_tag, type.type_tag, str(type.ctype), type.bound_name, type.check_func, type.to_c_func, type.from_c_func)
		# self._source += '};\n\n'

		self._source += """\
%s *%s(uint32_t type_tag) {
	return nullptr;
	//auto i = __type_tag_infos.find(type_tag);
	//return i == __type_tag_infos.end() ? nullptr : &i->second;
}\n\n""" % (
			type_info_name,
			gen.apply_api_prefix("get_bound_type_info"),
		)

		# self._source += 'static std::map<std::string, %s> __type_infos;\n\n' % type_info_name

		# self._source += 'static void __initialize_type_infos() {\n'
		# for type in self._bound_types:
		# 	if not type.c_storage_class:
		# 		self._source += '	__type_infos["%s"] = {%s, "%s", "%s", %s, %s, %s};\n' % (str(type.ctype), type.type_tag, str(type.ctype), type.bound_name, type.check_func, type.to_c_func, type.from_c_func)
		# self._source += '};\n\n'

		self._source += """
%s *%s(const char *type) {
	return nullptr;
	//auto i = __type_infos.find(type);
	//return i == __type_infos.end() ? nullptr : &i->second;
}\n\n""" % (
			type_info_name,
			gen.apply_api_prefix("get_c_type_info"),
		)

		self._source += """\
uint32_t %s(void* p) {
	return 0;
	//auto o = cast_to_wrapped_Object_safe(L, idx);
	//return o ? o->type_tag : 0;
}\n\n""" % gen.apply_api_prefix("get_wrapped_object_type_tag")

	#
	def get_output(self):
		return {"wrapper.cpp": self.go_c, "wrapper.h": self.go_h, "bind.go": self.go_bind}

	def _get_type(self, name):
		for type in self._bound_types:
			if type:
				return type
		return None

	def _get_conv(self, conv_name):
		if conv_name in self._FABGen__type_convs:
			return self.get_conv(conv_name)
		return None

	def __arg_from_cpp_to_c(self, val, retval_name, just_copy):
		src = ""
		# type class, not a pointer
		if val['conv'] is not None and val['conv'].is_type_class() and \
			not val['conv'].ctype.is_pointer() and ('storage_ctype' not in val or not hasattr(val['storage_ctype'], 'ref') or not any(s in val['storage_ctype'].ref for s in ["&", "*"])):
				# special shared ptr
				if 'proxy' in val['conv']._features:
					src += "	if(!{retval_name})\n" \
						"		return nullptr;\n"
					
					# go += "	auto " + val['conv']._features['proxy'].unwrap("(&ret)", "retPointerFromProxy")
					src += "	auto " + val['conv']._features['proxy'].wrap("ret", "retPointer")
				# special std::future 
				elif val["conv"] is not None and "std::future" in str(val["conv"].ctype):
			 		src += f"	auto retPointer = new std::future<int>(std::move({retval_name}));\n"
				else:
					# class, not pointer, but static
					if just_copy:
						src += f"	auto retPointer = {retval_name};\n"
					else:
						src += f"	auto retPointer = new {val['conv'].ctype}({retval_name});\n"
				retval_name = f"(Wrap{clean_name_with_title(val['conv'].bound_name)})(retPointer)"
		else:
			# special std::string (convert to const char*)
			if val["conv"] is not None and "std::string" in str(val["conv"].ctype):
				retval_name = f"{retval_name}.c_str()"
			else:
				retval_name = f"{retval_name}"
		return src, retval_name

	def __arg_from_c_to_cpp(self, val, retval_name):
		src = ""
		# check if there is special slice to convert
		if isinstance(val["conv"], lib.go.stl.GoSliceToStdVectorConverter):
			arg_bound_name = self.__get_arg_bound_name_to_c({"conv": val["conv"].T_conv})
			src += f"std::vector<{arg_bound_name}> {retval_name}(buf, buf + len);\n"

		retval = ""
		if val["conv"].is_type_class():
			if not val["conv"].ctype.is_pointer() and ("carg" not in val or ("carg" in val and not val["carg"].ctype.is_pointer())):
				retval += "*"
			retval += f"({val['conv'].ctype}*)"

		elif "carg" in val and hasattr(val["carg"].ctype, "ref") and any(s in val["carg"].ctype.ref for s in ["&"]):
			retval += "*"
		retval += retval_name
		return src, retval

	def __arg_from_c_to_go(self, val, retval_name):
		src = ""
		# check if need convert from c
		if ('storage_ctype' in val and (not val['storage_ctype'].is_pointer() and not (hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&", "*"])))) or \
		   ('storage_ctype' not in val and not val['conv']._is_pointer and not val['conv'].ctype.is_pointer()) or \
			val['conv'].bound_name == "string":
			conversion_ret = val['conv'].from_c_call(retval_name, "", "") 
			if conversion_ret != "":
				retval_name = conversion_ret

			# if it's a class, not a pointer, only out, create the class special
			if val["conv"].is_type_class():
				retval_boundname = val["conv"].bound_name
				retval_boundname = clean_name_with_title(retval_boundname)

				retval_name = f"{retval_boundname}{{h:{retval_name}}}\n"

		# if val['conv'].is_type_class():
		# 	retval_name = retval_name.title()

		# if pointer or ref
		elif (('storage_ctype' in val and (val['storage_ctype'].is_pointer() or (hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&", "*"])))) or \
			('storage_ctype' not in val and (val['conv']._is_pointer or val['conv'].ctype.is_pointer()))) and \
			val['conv'].bound_name != "string":
			
			# if it's a class, a pointer, only out, create the class special
			if val['conv'].is_type_class():
				retval_boundname = val['conv'].bound_name
				retval_boundname = clean_name_with_title(retval_boundname)

				src += f"if {retval_name} == nil {{\n" \
					"	return nil\n" \
					"}\n"
				src += f"rGO := new({retval_boundname})\n" \
							f"rGO.h = {retval_name}\n"
				retval_name = "rGO"
			else:
				retval_name = f"({self.__get_arg_bound_name_to_go(val)})(unsafe.Pointer({retval_name}))\n"

		return src, retval_name

	def __arg_from_go_to_c(self, val, arg_name, arg_out_name, start_stars=0):
		stars = "*" * start_stars
		if "carg" in val and hasattr(val["carg"].ctype, "ref"):
			stars += "*" * (len(val["carg"].ctype.ref))
		elif "storage_ctype" in val and hasattr(val["storage_ctype"], "ref"):
			stars += "*" * (len(val["conv"]["storage_ctype"].ref))
		elif hasattr(val["conv"].ctype, "ref"):
			stars += "*" * (len(val["conv"].ctype.ref))

		# get base conv (without pointer)
		base_conv = self._get_conv(str(val["conv"].ctype.scoped_typename))
		if base_conv is None:
			c_call = f"{clean_name(arg_out_name).replace('&', '_')} := ({stars}{str(val['conv'].bound_name)})(unsafe.Pointer({clean_name(arg_name)}))\n"
		elif hasattr(base_conv, "go_to_c_type") and base_conv.go_to_c_type is not None:
			c_call = f"{clean_name(arg_out_name).replace('&', '_')} := ({stars}{base_conv.go_to_c_type})(unsafe.Pointer({clean_name(arg_name)}))\n"
		else:
			c_call = f"{clean_name(arg_out_name).replace('&', '_')} := ({stars}{base_conv.bound_name})(unsafe.Pointer({clean_name(arg_name)}))\n"
		return c_call

	def __get_arg_bound_name_to_go(self, val):
		if val["conv"].is_type_class():
			arg_bound_name = val["conv"].bound_name
		else:
			# check the convert from the base (in case of ptr)
			if  ('carg' in val and (val['carg'].ctype.is_pointer() or (hasattr(val['carg'].ctype, 'ref') and any(s in val['carg'].ctype.ref for s in ["&", "*"]))) and val['conv'].bound_name != "string") or \
				('storage_ctype' in val and (val['storage_ctype'].is_pointer() or (hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&", "*"]))) and val['conv'].bound_name != "string") or \
				isinstance(val['conv'], GoPtrTypeConverter):
				base_conv = self._get_conv(str(val['conv'].ctype.scoped_typename))
				if base_conv is None:
					if hasattr(val["conv"], "go_type") and val["conv"].go_type is not None:
						arg_bound_name = str(val["conv"].go_type)
					else:
						arg_bound_name = str(val["conv"].bound_name)
				else:
					if hasattr(base_conv, "go_type") and base_conv.go_type is not None:
						arg_bound_name = base_conv.go_type
					else:
						arg_bound_name = base_conv.bound_name
			else:
				if hasattr(val["conv"], "go_type") and val["conv"].go_type is not None:
					arg_bound_name = val["conv"].go_type
				else:
					arg_bound_name = val["conv"].bound_name

		if arg_bound_name.endswith("_nobind") and val["conv"].nobind:
			arg_bound_name = arg_bound_name[:-len("_nobind")]

		# if it's a pointer
		if  ('carg' in val and (val['carg'].ctype.is_pointer() or (hasattr(val['carg'].ctype, 'ref') and any(s in val['carg'].ctype.ref for s in ["&", "*"]))) and val['conv'].bound_name != "string") or \
			('storage_ctype' in val and (val['storage_ctype'].is_pointer() or (hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&", "*"]))) and val['conv'].bound_name != "string") or \
			isinstance(val['conv'], GoPtrTypeConverter):
			# find how many * we need to ass
			stars = "*"
			if "carg" in val and hasattr(val["carg"].ctype, "ref"):
				stars += "*" * (len(val["carg"].ctype.ref) - 1)
			if "storage_ctype" in val and hasattr(val["storage_ctype"], "ref"):
				stars += "*" * (len(val["storage_ctype"].ref) - 1)
			arg_bound_name = stars + arg_bound_name

		if val['conv'].is_type_class() or \
			isinstance(val['conv'], lib.go.stl.GoSliceToStdVectorConverter):
			arg_bound_name = clean_name_with_title(arg_bound_name)
		return arg_bound_name

	def __get_arg_bound_name_to_c(self, val):
		arg_bound_name = ""
		if val["conv"].is_type_class():
			arg_bound_name = f"Wrap{clean_name_with_title(val['conv'].bound_name)} "
		else:
			# check the convert from the base (in case of ptr)
			if  ('carg' in val and (val['carg'].ctype.is_pointer() or (hasattr(val['carg'].ctype, 'ref') and any(s in val['carg'].ctype.ref for s in ["&", "*"]))) and val['conv'].bound_name != "string") or \
				('storage_ctype' in val and (val['storage_ctype'].is_pointer() or (hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&", "*"]))) and val['conv'].bound_name != "string") or \
				isinstance(val['conv'], GoPtrTypeConverter):
				base_conv = self._get_conv(str(val['conv'].ctype.scoped_typename))
				if base_conv is None:
					arg_bound_name = str(val["conv"].bound_name)
				else:
					arg_bound_name = str(base_conv.ctype)
				arg_bound_name += "*"
				if "carg" in val and hasattr(val["carg"].ctype, "ref"):
					arg_bound_name += "*" * (len(val["carg"].ctype.ref) - 1)
				if "storage_ctype" in val and hasattr(val["storage_ctype"], "ref"):
					arg_bound_name += "*" * (len(val["storage_ctype"].ref) - 1)
			else:
				arg_bound_name = f"{val['conv'].ctype} "
				
		return arg_bound_name

	def __extract_sequence_go(self, conv):
		go = ""

		classname = clean_name_with_title(conv.bound_name)

		internal_conv = conv._features["sequence"].wrapped_conv

		arg_bound_name = self.__get_arg_bound_name_to_go({"conv": internal_conv})

		# GET
		go += f"// Get ...\n" \
				f"func (pointer {classname}) Get(id int) {arg_bound_name} {{\n"
		go += f"v := C.Wrap{classname}GetOperator(pointer.h, C.int(id))\n"

		src, retval_go = self.__arg_from_c_to_go({"conv": internal_conv}, "v")
		go += src
		go += f"return {retval_go}\n"
		go += "}\n"

		# SET
		go += f"// Set ...\n" \
				f"func (pointer {classname}) Set(id int, v {arg_bound_name}) {{\n"
		# convert to c
		if isinstance(internal_conv, GoPtrTypeConverter):
			c_call = self.__arg_from_go_to_c({"conv": internal_conv}, "v", f"vToC")
		else:
			c_call = internal_conv.to_c_call("v", f"vToC", internal_conv.ctype.is_pointer() or (hasattr(internal_conv.ctype, "ref") and any(s in internal_conv.ctype.ref for s in ["&", "*"])))
		if c_call != "":
			go += c_call
		else:
			go += "vToC := v\n"

		go += f"	C.Wrap{classname}SetOperator(pointer.h, C.int(id), vToC)\n"
		go += "}\n"

		# Len
		go += f"// Len ...\n" \
				f"func (pointer {classname}) Len() int32 {{\n"
		go += f"return int32(C.Wrap{classname}LenOperator(pointer.h))\n"
		go += "}\n"

		return go

	def __extract_sequence(self, conv, is_in_header=False):
		go = ""

		cleanClassname = clean_name_with_title(conv.bound_name)

		internal_conv = conv._features["sequence"].wrapped_conv

		arg_bound_name = self.__get_arg_bound_name_to_c({"conv": internal_conv})

		# special std::string (convert to const char*)
		c_arg_bound_name = arg_bound_name.replace("std::string", "const char*")

		# GET
		go += f"{c_arg_bound_name} Wrap{cleanClassname}GetOperator(Wrap{cleanClassname} h, int id)"

		if is_in_header:
			go += ";\n"
		else:
			go += f"{{\n" \
				"	bool error;\n" \
				f"	{arg_bound_name} v;\n	"
			go += conv._features['sequence'].get_item(f"(({conv.ctype}*)h)", "id", "v", "error")

			src, retval_c = self.__arg_from_cpp_to_c({"conv": internal_conv}, "v", True)
			go += src
			go += f"	return {retval_c};\n}}\n"

		# SET
		go += f"void Wrap{cleanClassname}SetOperator(Wrap{cleanClassname} h, int id, {c_arg_bound_name} v)"

		if is_in_header:
			go += ";\n"
		else:
			go += f"{{\n" \
				"	bool error;\n"

			src, inval = self.__arg_from_c_to_cpp({"conv": internal_conv}, "v")
			go += src

			go += conv._features['sequence'].set_item(f"(({conv.ctype}*)h)", "id", inval, "error")
			go += f"\n}}\n"

		# LEN
		go += f"int Wrap{cleanClassname}LenOperator(Wrap{cleanClassname} h)"

		if is_in_header:
			go += ";\n"
		else:
			go += f"{{\n" \
				"	int size;\n	"
			go += conv._features['sequence'].get_size(f"(({conv.ctype}*)h)", "size")
			go += f"	return size;\n}}\n"

		return go

	def __extract_get_set_member_go(self, classname, member, static=False, name=None, bound_name=None, is_global=False):
		go = ""
		conv = self.select_ctype_conv(member["ctype"])

		if "bound_name" in member:
			bound_name = str(member["bound_name"])
		elif bound_name is None:
			bound_name = str(member["name"])
		if name is None:
			name = bound_name

		name = name.replace(":", "")

		arg_bound_name = self.__get_arg_bound_name_to_go({"conv": conv})

		def create_get_set(do_static):
			# GET
			go = f"// Get{name} ...\n" \
					f"func "
			if do_static:
				go += f"{clean_name_with_title(classname)}"
			else:
				go += f"(pointer {clean_name_with_title(classname)}) "

			go += f"Get{name}() {arg_bound_name} {{\n"
			go += f"v := C.Wrap{clean_name_with_title(classname)}Get{name}("
			if not static and not is_global:
				go += "pointer.h"
			go += ")\n"

			# check if need convert from c
			src, retval_go = self.__arg_from_c_to_go({"conv": conv}, "v")
			go += src
			go += f"return {retval_go}\n"

			go += "}\n"

			# SET
			# add set only if the member is not const
			if not member["ctype"].const:
				go += f"// Set{name} ...\n" \
						f"func "
						
				if do_static:
					go += f"{clean_name_with_title(classname)}"
				else:
					go += f"(pointer {clean_name_with_title(classname)}) "

				go += f"Set{name}(v {arg_bound_name}) {{\n"

				# convert to c
				if isinstance(conv, GoPtrTypeConverter):
					c_call = self.__arg_from_go_to_c({"conv": conv}, "v", f"vToC")
				else:
					c_call = conv.to_c_call("v", f"vToC", conv.ctype.is_pointer() or (hasattr(conv.ctype, "ref") and any(s in conv.ctype.ref for s in ["&", "*"])))
				if c_call != "":
					go += c_call
				else:
					go += "vToC := v\n"

				go += f"	C.Wrap{clean_name_with_title(classname)}Set{name}("
				if not static and not is_global:
					go += "pointer.h, "
				go += "vToC)\n"
				go += "}\n"
			return go

		# create twice, with and without static, to use it with the class and standalone
		if not is_global:
			go += create_get_set(False)
		if static or is_global:
			go += create_get_set(True)

		return go

	def __extract_get_set_member(self, classname, convClass, member, static=False, name=None, bound_name=None, is_global=False, is_in_header=False):
		go = ""
		conv = self.select_ctype_conv(member["ctype"])

		if "bound_name" in member:
			bound_name = str(member["bound_name"])
		elif bound_name is None:
			bound_name = str(member["name"])
		if name is None:
			name = bound_name

		c_name = str(member["name"])

		cleanClassname = clean_name_with_title(classname)

		# special Slice
		if isinstance(conv, lib.go.stl.GoSliceToStdVectorConverter):
			arg_bound_name = self.__get_arg_bound_name_to_c({"conv": conv.T_conv})
		else:
			arg_bound_name = self.__get_arg_bound_name_to_c({"conv": conv})
		
		# special std::string (convert to const char*)
		c_arg_bound_name = arg_bound_name.replace("std::string", "const char*")

		# GET
		go += f"{c_arg_bound_name} Wrap{cleanClassname}Get{name.replace(':', '')}("
		if not static and not is_global:
			go += f"Wrap{cleanClassname} h"
		go += ")"

		if is_in_header:
			go += ";\n"
		else:
			go += "{"
			# check if the value is a ref
			prefix = ""
			if (hasattr(conv.ctype, "ref") and conv.ctype.ref in ["&", "*&"]) or \
				conv.is_type_class():
				prefix = "&"

			if static or is_global:
				go += f"	auto ret = {prefix}{classname}::{c_name};\n"
			else:
				if convClass is not None and "proxy" in convClass._features:
					go += f"\n	auto v = _type_tag_cast(h, {convClass.type_tag}, {convClass._features['proxy'].wrapped_conv.type_tag});\n"
					go += f"	auto ret = {prefix}(({convClass._features['proxy'].wrapped_conv.ctype}*)v)->{c_name};\n"
				else:
					go += f"	auto ret = {prefix}(({convClass.ctype}*)h)->{c_name};\n"

			src, retval_c = self.__arg_from_cpp_to_c({"conv": conv}, "ret", True)
			go += src
			go += f"return {retval_c};\n}}\n"

		# SET
		# add set only if the member is not const
		if not member["ctype"].const:
			go += f"void Wrap{cleanClassname}Set{name.replace(':', '')}("
			if not static and not is_global:
				go += f"Wrap{cleanClassname} h, "
			go += f"{c_arg_bound_name} v)"

			if is_in_header:
				go += ";\n"
			else:

				src, inval = self.__arg_from_c_to_cpp({"conv": conv}, "v")
				go += src

				if static or is_global:
					go += f"{{ {classname}::{c_name} = {inval};\n}}\n"
				else:
					if convClass is not None and "proxy" in convClass._features:
						go += f"{{\n	auto w = _type_tag_cast(h, {convClass.type_tag}, {convClass._features['proxy'].wrapped_conv.type_tag});\n"
						go += f"	(({convClass._features['proxy'].wrapped_conv.bound_name}*)w)->{c_name} = {inval};\n}}\n"
					else:
						go += f"{{ (({convClass.ctype}*)h)->{c_name} = {inval};}}\n"
		return go

	def __extract_method_go(self, classname, convClass, method, static=False, name=None, bound_name=None, is_global=False, is_constructor=False):
		go = ""

		if bound_name is None:
			bound_name = method["bound_name"]
		if name is None:
			name = bound_name

		if bound_name == "OpenVRStateToViewState":
			bound_name = bound_name

		name_go = name
		if is_constructor:
			name_go = "new_" + name_go

		uid = classname + bound_name if classname else bound_name

		protos = self._build_protos(method["protos"])
		for id_proto, proto in enumerate(protos):
			retval = ""

			if proto["rval"]["conv"]:
				retval = proto["rval"]["conv"].bound_name

			go += "// " + clean_name_with_title(name_go)
			# add number in case of multiple proto, in go, you can't have overload or default parameter
			if len(protos) > 1:
				go += f"{id_proto}"
			go += " ...\n"

			go += "func "
			if not is_global:
				go += f"(pointer {clean_name_with_title(classname)}) "
			go += f"{clean_name_with_title(name_go)}"

			# add number in case of multiple proto, in go, you can't have overload or default parameter
			if len(protos) > 1:
				go += f"{id_proto}"

			# add input(s) declaration
			go += "("
			if len(proto["args"]):
				has_previous_arg = False
				for argin in proto["argsin"]:
					if has_previous_arg:
						go += " ,"
					go += f"{clean_name(argin['carg'].name)} {self.__get_arg_bound_name_to_go(argin)}"
					has_previous_arg = True

			go += ")"

			# add output(s) declaration
			go += "("
			has_previous_ret_arg = False
			if proto["rval"]["conv"]:
				go += self.__get_arg_bound_name_to_go(proto["rval"])
				has_previous_ret_arg = True
			
			if len(proto['args']):
				for arg in proto['args']:
					if ('arg_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_out']) or \
						('arg_in_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_in_out']):
						if has_previous_ret_arg:
							go += " ,"

						go += self.__get_arg_bound_name_to_go(arg)
						has_previous_ret_arg = True
			go += ")"

			# begin function declaration
			go += "{\n"

			# convert arg in to c
			if len(proto["args"]):
				for arg in proto["args"]:
					# if arg out only, declare this value
					if "arg_out" in proto["features"] and str(arg["carg"].name) in proto["features"]["arg_out"]:
						arg_bound_name = arg["conv"].bound_name
						if arg_bound_name.endswith("_nobind") and arg["conv"].nobind:
							arg_bound_name = arg_bound_name[:-len("_nobind")]
						if (arg["carg"].ctype.is_pointer() or (hasattr(arg["carg"].ctype, "ref") and arg["carg"].ctype.ref == "&")) and arg["conv"].bound_name != "string":
							arg_bound_name = f"new({arg_bound_name})"
						go += f"{clean_name(arg['carg'].name)} := {arg_bound_name}\n"

					c_call = ""
					if arg["conv"]:
						src = ""
						# special Slice
						if isinstance(arg["conv"], lib.go.stl.GoSliceToStdVectorConverter):
							c_call = f"{clean_name(arg['carg'].name)}ToC := (*reflect.SliceHeader)(unsafe.Pointer(&{clean_name(arg['carg'].name)}))\n"
							c_call += f"{clean_name(arg['carg'].name)}ToCSize := C.size_t({clean_name(arg['carg'].name)}ToC.Len)\n"

							c_call += self.__arg_from_go_to_c({"conv": arg["conv"].T_conv}, f"{clean_name(arg['carg'].name)}ToC.Data", f"{clean_name(arg['carg'].name)}ToCBuf", 1)
						elif isinstance(arg["conv"], GoPtrTypeConverter):
							c_call = self.__arg_from_go_to_c(arg, arg["carg"].name, f"{arg['carg'].name}ToC")
						else:
							c_call = arg["conv"].to_c_call(clean_name(arg["carg"].name), f"{clean_name(arg['carg'].name)}ToC", arg["carg"].ctype.is_pointer() or (hasattr(arg["carg"].ctype, "ref") and arg["carg"].ctype.ref == "&"))
					if c_call != "":
						go += c_call
					else:
						go += f"{clean_name(arg['carg'].name)}ToC := {clean_name(arg['carg'].name)}\n"

			# declare arg out
			if retval != "":
				go += "retval := "

			if is_constructor:
				go += f"C.WrapConstructor{clean_name_with_title(name)}"
			else:
				go += f"C.Wrap{clean_name_with_title(name)}"

			# is global, add the Name of the class to be sure to avoid double name function name
			if not is_global:
				go += f"{clean_name_with_title(convClass.bound_name)}"

			# add number in case of multiple proto, in go, you can't have overload or default parameter
			if len(protos) > 1:
				go += f"{id_proto}"

			go += "("
			if not is_global and not is_constructor:
				go += "pointer.h, "

			if len(proto["args"]):
				has_previous_arg = False
				for arg in proto["args"]:
					if has_previous_arg:
						go += " ,"

					# special Slice
					if isinstance(arg["conv"], lib.go.stl.GoSliceToStdVectorConverter):
						go += f"{clean_name(arg['carg'].name)}ToCSize, {clean_name(arg['carg'].name)}ToCBuf"
					else:
						# if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and \
						# 	arg['conv'].bound_name != "string" and not arg['conv'].is_type_class():
						# 	go += "&"
						go += f"{clean_name(arg['carg'].name)}ToC"

					has_previous_arg = True
			go += ")\n"
			if retval != "":
				src, retval_go = self.__arg_from_c_to_go(proto["rval"], "retval")
				go += src

				go += f"return {retval_go}"

			# return arg out
			if "arg_out" in proto["features"] or "arg_in_out" in proto["features"]:
				if retval == "":
					go += "return "
				has_previous_arg = False

				for arg in proto['args']:
					if ('arg_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_out']) or \
						('arg_in_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_in_out']):
						if retval != '' or has_previous_arg:
							# check and remove \n just in case
							if go[-1] == "\n":
								go = go[:-1]
							go += ", "
						has_previous_arg = True

						# add name
						# in var name if it's in arg in out
						if "arg_in_out" in proto["features"] and str(arg["carg"].name) in proto["features"]["arg_in_out"]:
							retval_go = clean_name(str(arg["carg"].name))
						else:
							retval_go = clean_name(str(arg["carg"].name)) + "ToC"

						# if class and return nil, return nil go
						# if arg['conv'].is_type_class():
						# 	retval_boundname = arg['conv'].bound_name
						# 	retval_boundname = clean_name_with_title(retval_boundname)

						# 	go += f"if {retval_go} == nil {{\n" \
						# 		"	return nil\n" \
						# 		"}\n"
						# 	go += f"rGO := new({retval_boundname})\n" \
						# 				f"rGO.h = {retval_go}\n"
						# 	retval_go = "rGO"

						# check if need convert from c

						# check if need convert from c
						if (not arg['carg'].ctype.is_pointer() and \
							not (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) or \
							arg['conv'].bound_name == "string":
							conversion_ret = arg['conv'].from_c_call("retval", "", "") 
							if conversion_ret != "":
								retval_go = conversion_ret

						if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and \
							arg['conv'].bound_name != "string":
							
							if not arg['conv'].is_type_class():
								retval_go = f"(*{arg['conv'].bound_name})(unsafe.Pointer({retval_go}))"
							else:
								# special arg out pointer class
								if "arg_out" in proto["features"] and str(arg["carg"].name) in proto["features"]["arg_out"]:
									arg_bound_name = arg["conv"].bound_name
									if arg_bound_name.endswith("_nobind") and arg["conv"].nobind:
										arg_bound_name = arg_bound_name[:-len("_nobind")]
									arg_bound_name = arg_bound_name.title()

									retval_go = f"(*{arg_bound_name})(unsafe.Pointer({retval_go}))"

						go += retval_go

			go += "\n}\n"

		return go

	def __extract_method(self, classname, convClass, method, static=False, name=None, bound_name=None, is_global=False, is_in_header=False, is_constructor=False):
		go = ""

		if bound_name is None:
			bound_name = method["bound_name"]
		if name is None:
			name = bound_name
		wrap_name = bound_name

		if bound_name == "OpenVRStateToViewState":
			bound_name = bound_name

		uid = classname + bound_name if classname else bound_name

		protos = self._build_protos(method["protos"])
		for id_proto, proto in enumerate(protos):
			retval = "void"

			if str(proto["rval"]["storage_ctype"]) != "void":
				if proto["rval"]["conv"] is not None and proto["rval"]["conv"].is_type_class():
					retval = "Wrap" + clean_name_with_title(proto["rval"]["conv"].bound_name)
				# transform & to *
				elif hasattr(proto["rval"]["storage_ctype"], "ref") and "&" in proto["rval"]["storage_ctype"].ref:
					retval = str(proto["rval"]["conv"].ctype) + " *"
				else:
					retval = str(proto["rval"]["storage_ctype"])

				# special std::string (convert to const char*)
				retval = retval.replace("std::string", "const char*")

			if is_in_header:
				go += "extern "
			go += "%s Wrap%s" % (retval, clean_name_with_title(wrap_name))

			# not global, add the Name of the class to be sure to avoid double name function name
			if not is_global:
				go += f"{clean_name_with_title(convClass.bound_name)}"

			# add number in case of multiple proto, in go, you can't have overload or default parameter
			if len(protos) > 1:
				go += f"{id_proto}"

			go += "("

			has_previous_arg = False
			# not global, member class, include the "this" pointer first
			if not is_global:
				has_previous_arg = True
				go += f"Wrap{clean_name_with_title(convClass.bound_name)} this_"

			if len(proto["args"]):
				for argin in proto["args"]:
					if has_previous_arg:
						go += " ,"

					# get arg name
					# special Slice
					if isinstance(argin["conv"], lib.go.stl.GoSliceToStdVectorConverter):
						arg_bound_name = self.__get_arg_bound_name_to_c({"conv": argin["conv"].T_conv})
					else:
						arg_bound_name = self.__get_arg_bound_name_to_c(argin)

					# special std::string (convert to const char*)
					arg_bound_name = arg_bound_name.replace("std::string", "const char*")

					# special Slice
					if isinstance(argin["conv"], lib.go.stl.GoSliceToStdVectorConverter):
						go += f"size_t len, {arg_bound_name} *buf"
					else:
						# normal argument
						go += f"{arg_bound_name} {argin['carg'].name}"
					has_previous_arg = True

			go += ")"

			if is_in_header:
				go += ";\n"
			else:
				go += "{\n"

				args = []
				# if another route is set
				if "route" in proto["features"] and convClass is not None:
					args.append(f"({convClass.ctype}*)this_")

				if len(proto["args"]):
					has_previous_arg = False
					for argin in proto["args"]:
						src, retval_c = self.__arg_from_c_to_cpp(argin, str(argin["carg"].name))
						go += src
						args.append(retval_c)
						has_previous_arg = True

				if is_constructor:
					if "proxy" in convClass._features:
						go += "	auto " + convClass._features["proxy"].wrap(f"new {convClass._features['proxy'].wrapped_conv.bound_name}({','.join(args)})", "v")
						go += "	return v;\n"
					elif "sequence" in convClass._features:
						go += f"	return (void*)(new {convClass.ctype}({','.join(args)}));\n"
					else:
						go += f"	return (void*)(new {convClass.ctype}({','.join(args)}));\n"
				else:
					# if there is return value
					if retval != "void":
						go += "	auto ret = "

					# transform & to *
					if hasattr(proto["rval"]["storage_ctype"], "ref") and any(s in proto["rval"]["storage_ctype"].ref for s in ["&"]):
						go += "&"

					# if another route is set
					if "route" in proto["features"]:
						go += proto["features"]["route"](args) + "\n"
					else:
						# not global, member class, include the "this" pointer first
						if not is_global:
							go += f"(*({convClass.ctype}*)this_)"
							if convClass.ctype.is_pointer():
								go += "->"
							else:
								go += "."
								
						go += name

						# add function's arguments
						go += f"({','.join(args)});\n"

					if retval != "void":
						src, retval_c = self.__arg_from_cpp_to_c(proto["rval"], "ret", static)
						go += src
						go += f"return {retval_c};\n"
				go += "}\n"

		return go

	def finalize(self):

		# add class global
		for conv in self._bound_types:
			if conv.nobind:
				continue

			if conv.is_type_class():
				# add equal of deep copy
				if conv._supports_deep_compare:
					go = ""
					if "proxy" in conv._features:
						go += f"bool _{conv.bound_name}_Equal({conv.ctype} *a, {conv.ctype} *b){{\n"
						go += f"	auto cast_a = _type_tag_cast(a, {conv.type_tag}, {conv._features['proxy'].wrapped_conv.type_tag});\n"
						go += f"	auto cast_b = _type_tag_cast(b, {conv.type_tag}, {conv._features['proxy'].wrapped_conv.type_tag});\n"

						wrapped_conv = conv._features["proxy"].wrapped_conv
						if wrapped_conv.is_type_class():
							go += f"	return ({wrapped_conv.bound_name}*)cast_a == ({wrapped_conv.bound_name}*)cast_b;\n"
						else:
							# check the convert from the base (in case of ptr)
							if wrapped_conv.ctype.is_pointer() or (hasattr(wrapped_conv.ctype, "ref") and any(s in wrapped_conv.ctype.ref for s in ["&", "*"])):
								base_conv = self._get_conv(str(wrapped_conv.ctype.scoped_typename))
								if base_conv is None:
									type_bound_name = str(wrapped_conv.bound_name)
								else:
									type_bound_name = str(base_conv.ctype)
							else:
								type_bound_name = str(wrapped_conv.ctype)
							go += f"	return ({type_bound_name}*)cast_a == ({type_bound_name}*)cast_b;\n"
					else:
						go += f"bool _{conv.bound_name}_Equal({conv.bound_name} *a, {conv.bound_name} *b){{\n"
						go += f"	return *a == *b;\n"
					go += "}\n"

					self.insert_code(go)
					if "proxy" in conv._features:
						self.bind_method(conv, "Equal", "bool", [f"{conv.ctype} *b"], {"route": route_lambda(f"_{conv.bound_name}_Equal")})
					else:
						self.bind_method(conv, "Equal", "bool", [f"{conv.bound_name} *b"], {"route": route_lambda(f"_{conv.bound_name}_Equal")})

			# add down cast
			for base in conv._bases:
				self.add_cast(base, conv, lambda in_var, out_var: "%s = (%s *)((%s *)%s);\n" % (out_var, conv.ctype, base.ctype, in_var))

		super().finalize()

		self.output_binding_api()

		# helper to add from itself and from parent class
		def extract_conv_and_bases(convs_to_extract, extract_func, bases_convs_to_extract):
			go = ""
			saved_names = []
			for conv_to_extract in convs_to_extract:
				if "name" in conv_to_extract:
					saved_names.append(conv_to_extract["name"])
				elif "op" in conv_to_extract:
					saved_names.append(conv_to_extract["op"])
				go += extract_func(conv_to_extract)

			# add static member get set for base class
			for base_convs_to_extract in bases_convs_to_extract:
				for conv_to_extract in base_convs_to_extract:
					# add only if it's not already in the current class
					n = ""
					if "name" in conv_to_extract:
						n = conv_to_extract["name"]
					elif "op" in conv_to_extract:
						n = conv_to_extract["op"]
					if n not in saved_names:
						saved_names.append(n)
						go += extract_func(conv_to_extract)
			return go

		# .h
		go_h = '#pragma once\n' \
				'#ifdef __cplusplus\n'\
				'extern "C" {\n'\
				'#endif\n'

		go_h += '#include <stdint.h>\n' \
			'#include <stdbool.h>\n' \
			'#include <stddef.h>\n' \
			'#include <memory.h>\n' \
			'#include <string.h>\n' \
			'#include <stdlib.h>\n' \
			'#include "fabgen.h"\n\n'
			
		go_h += 'typedef int WrapBool;\n'

		for conv in self._bound_types:
			if conv.nobind:
				continue

			cleanBoundName = clean_name_with_title(conv.bound_name)
			if conv.is_type_class():
				go_h += f"typedef void* Wrap{cleanBoundName};\n"

			if "sequence" in conv._features:
				go_h += self.__extract_sequence(conv, is_in_header=True)

			# static members
			go_h += extract_conv_and_bases(conv.static_members, \
									lambda member: self.__extract_get_set_member(conv.bound_name, conv, member, static=True, is_in_header=True), \
									[base_class.static_members for base_class in conv._bases])

			# members
			go_h += extract_conv_and_bases(conv.members, \
									lambda member: self.__extract_get_set_member(conv.bound_name, conv, member, is_in_header=True), \
									[base_class.members for base_class in conv._bases])

			# constructors
			if conv.constructor:
				go_h += self.__extract_method(cleanBoundName, conv, conv.constructor, bound_name=f"constructor_{conv.bound_name}", is_in_header=True, is_global=True, is_constructor=True)
				go_h += f"void Wrap{cleanBoundName}Free(Wrap{cleanBoundName});\n"

			# arithmetic operators
			go_h += extract_conv_and_bases(conv.arithmetic_ops, \
									lambda arithmetic: self.__extract_method(conv.bound_name, conv, arithmetic, is_in_header=True, name='operator'+arithmetic['op'], bound_name='operator_' + gen.get_clean_symbol_name(arithmetic['op'])), \
									[base_class.arithmetic_ops for base_class in conv._bases])

			# comparison_ops
			go_h += extract_conv_and_bases(conv.comparison_ops, \
									lambda comparison: self.__extract_method(conv.bound_name, conv, comparison, is_in_header=True, name='operator'+comparison['op'], bound_name='operator_' + gen.get_clean_symbol_name(comparison['op'])), \
									[base_class.comparison_ops for base_class in conv._bases])

			# static methods
			go_h += extract_conv_and_bases(conv.static_methods, \
									lambda method: self.__extract_method(conv.bound_name, conv, method, static=True, is_in_header=True), \
									[base_class.static_methods for base_class in conv._bases])
			# methods
			go_h += extract_conv_and_bases(conv.methods, \
									lambda method: self.__extract_method(conv.bound_name, conv, method, is_in_header=True), \
									[base_class.methods for base_class in conv._bases])
				
			
		# enum
		for bound_name, enum in self._enums.items():
			go_h += f"extern int Get{bound_name}(const int id);\n"

		# functions
		for func in self._bound_functions:
			go_h += self.__extract_method("", None, func, name=func["name"], is_global=True, is_in_header=True)

		# global variables
		for var in self._bound_variables:
			go_h += self.__extract_get_set_member("", None, var, is_global=True, is_in_header=True)

		go_h += '#ifdef __cplusplus\n' \
				'}\n' \
				'#endif\n'
		self.go_h = go_h


		# cpp
		go_c = '// go wrapper c\n' \
				'#include \"wrapper.h\"\n' \
				'#include <memory>\n'
				
		if len(self._FABGen__system_includes) > 0:
			go_c += "".join(['#include "%s"\n' % path for path in self._FABGen__system_includes])

		go_c += self._source

		for conv in self._bound_types:
			if conv.nobind:
				continue

			cleanBoundName = clean_name_with_title(conv.bound_name)
			if conv.is_type_class():
				go_c += f"// bind Wrap{cleanBoundName} methods\n"

			if "sequence" in conv._features:
				go_c += self.__extract_sequence(conv)
			
			# static members
			go_c += extract_conv_and_bases(conv.static_members, \
									lambda member: self.__extract_get_set_member(conv.bound_name, conv, member, static=True), \
									[base_class.static_members for base_class in conv._bases])

			# members
			go_c += extract_conv_and_bases(conv.members, \
									lambda member: self.__extract_get_set_member(conv.bound_name, conv, member), \
									[base_class.members for base_class in conv._bases])

			# constructors
			if conv.constructor:
				go_c += self.__extract_method(conv.bound_name, conv, conv.constructor, bound_name=f"constructor_{conv.bound_name}", is_global=True, is_constructor=True)
				
				# delete
				go_c += f"void Wrap{cleanBoundName}Free(Wrap{cleanBoundName} h){{" \
						f"delete ({conv.ctype}*)h;" \
						f"}}\n" 

			# arithmetic operators
			go_c += extract_conv_and_bases(conv.arithmetic_ops, \
									lambda arithmetic: self.__extract_method(conv.bound_name, conv, arithmetic, name="operator" + arithmetic["op"], bound_name="operator_" + gen.get_clean_symbol_name(arithmetic["op"])), \
									[base_class.arithmetic_ops for base_class in conv._bases])

			# comparison_ops
			go_c += extract_conv_and_bases(conv.comparison_ops, \
									lambda comparison: self.__extract_method(conv.bound_name, conv, comparison, name="operator" + comparison["op"], bound_name="operator_" + gen.get_clean_symbol_name(comparison["op"])), \
									[base_class.comparison_ops for base_class in conv._bases])

			# static methods
			go_c += extract_conv_and_bases(conv.static_methods, \
									lambda method: self.__extract_method(conv.bound_name, conv, method, static=True), \
									[base_class.static_methods for base_class in conv._bases])
			# methods
			go_c += extract_conv_and_bases(conv.methods, \
									lambda method: self.__extract_method(conv.bound_name, conv, method), \
									[base_class.methods for base_class in conv._bases])

		# enum
		for bound_name, enum in self._enums.items():
			enum_vars = []
			for name, value in enum.items():
				enum_vars.append(f"(int){value}")
			go_c += f"static const int Wrap{bound_name} [] = {{ {', '.join(enum_vars)} }};\n"
			go_c += f"int Get{bound_name}(const int id) {{ return Wrap{bound_name}[id];}}\n"

		# functions
		for func in self._bound_functions:
			go_c += self.__extract_method("", None, func, name=func["name"], is_global=True)

		# global variables
		for var in self._bound_variables:
			go_c += self.__extract_get_set_member("", None, var, is_global=True, static=True)

		self.go_c = go_c

		# .go
		go_bind = 'package harfang\n' \
				'// #include "wrapper.h"\n' \
				'// #cgo CFLAGS: -I . -g3 -Wall -Wno-unused-variable -Wno-unused-function\n' \
				'// #cgo CXXFLAGS: -std=c++14\n' \
				'import "C"\n\n' \
				'import (\n'
		
		# check if reflect package is needed
		for conv in self._FABGen__type_convs.values():
			# special Slice
			if isinstance(conv, lib.go.stl.GoSliceToStdVectorConverter):
				go_bind += '	"reflect"\n'
				break

		go_bind += '	"unsafe"\n' \
				')\n'

		with open("lib/go/WrapperConverter.go_", "r") as file:
			lines = file.readlines()
			go_bind += "".join(lines)
			go_bind += "\n"

		# // #cgo CFLAGS: -Iyour-include-path
		# // #cgo LDFLAGS: -Lyour-library-path -lyour-library-name-minus-the-lib-part

		for conv in self._bound_types:
			if conv.nobind:
				continue

			cleanBoundName = clean_name_with_title(conv.bound_name)

			# special Slice
			if isinstance(conv, lib.go.stl.GoSliceToStdVectorConverter):
				arg_boung_name = self.__get_arg_bound_name_to_go({"conv":conv.T_conv})
				go_bind += f"// {clean_name_with_title(conv.bound_name)} ...\n" \
							f"type {clean_name_with_title(conv.bound_name)} []{arg_boung_name}\n\n"

			if conv.is_type_class():
				go_bind += f"// {cleanBoundName} ...\n" \
							f"type {cleanBoundName} struct{{\n" \
							f"	h C.Wrap{cleanBoundName}\n" \
							"}\n"
			
			if "sequence" in conv._features:
				go_bind += self.__extract_sequence_go(conv)

			# static members
			go_bind += extract_conv_and_bases(conv.static_members, \
									lambda member: self.__extract_get_set_member_go(conv.bound_name, member, static=True), \
									[base_class.static_members for base_class in conv._bases])

			# members
			go_bind += extract_conv_and_bases(conv.members, \
									lambda member: self.__extract_get_set_member_go(conv.bound_name, member, static=False), \
									[base_class.members for base_class in conv._bases])

			# constructors
			if conv.constructor:
				go_bind += self.__extract_method_go(conv.bound_name, conv, conv.constructor, bound_name=f"{conv.bound_name}", is_global=True, is_constructor=True)
				go_bind += f"// Free ...\n" \
				f"func (pointer {cleanBoundName}) Free(){{\n" \
				f"	C.Wrap{cleanBoundName}Free(pointer.h)\n" \
				f"}}\n"
				
				go_bind += f"// IsNil ...\n" \
				f"func (pointer {cleanBoundName}) IsNil() bool{{\n" \
				f"	return pointer.h == C.Wrap{cleanBoundName}(nil)\n" \
				f"}}\n"

				# runtime.SetFinalizer(funcret, func(ctx *Ret) { C.free(ctx.bufptr) })
			# arithmetic operators
			go_bind += extract_conv_and_bases(conv.arithmetic_ops, \
									lambda arithmetic: self.__extract_method_go(conv.bound_name, conv, arithmetic, bound_name='operator_' + gen.get_clean_symbol_name(arithmetic['op'])), \
									[base_class.arithmetic_ops for base_class in conv._bases])
			# comparison_ops
			go_bind += extract_conv_and_bases(conv.comparison_ops, \
									lambda comparison: self.__extract_method_go(conv.bound_name, conv, comparison, bound_name='operator_' + gen.get_clean_symbol_name(comparison['op'])), \
									[base_class.comparison_ops for base_class in conv._bases])

			# static methods
			go_bind += extract_conv_and_bases(conv.static_methods, \
									lambda method: self.__extract_method_go(conv.bound_name, conv, method, static=True), \
									[base_class.static_methods for base_class in conv._bases])
			# methods
			go_bind += extract_conv_and_bases(conv.methods, \
									lambda method: self.__extract_method_go(conv.bound_name, conv, method), \
									[base_class.methods for base_class in conv._bases])

		# enum
		for bound_name, enum in self._enums.items():
			go_bind += f"type {bound_name} int\n" \
						"var (\n"
			for id, name in enumerate(enum.keys()):
				go_bind += f"	{clean_name(name)} =  {bound_name}(C.Get{bound_name}({id}))\n"
			go_bind += ")\n"

		# functions
		for func in self._bound_functions:
			go_bind += self.__extract_method_go("", None, func, is_global=True)

		# global variables
		for var in self._bound_variables:
			go_bind += self.__extract_get_set_member_go("", var, is_global=True)

		self.go_bind = go_bind
