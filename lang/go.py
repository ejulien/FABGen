# Harfang - The Fabulous binding Generator for CPython and Go
# 	Copyright (C) 2020 Thomas Simonnet

import os
from os import stat_result
from pypeg2 import parse
import json
import re
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
	if new_name in ["break", "default", "func", "interface", "select", "case", "defer", "go", "map", "struct", "chan", "else", "goto", "package", "switch", "const", "fallthrough", "if", "range", "type", "continue", "for", "import", "return", "var" ]:
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
		# make sur the first letter is capitalize
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
		self.base_type = type
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
		return ""

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
		out += 'int (*%s)(void *obj, OwnershipPolicy) = nullptr;\n' % self.from_c_func
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

		self._source += self.get_binding_api_declaration()

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
		self._source += """\
%s *%s(uint32_t type_tag) {
	return nullptr;
}\n\n""" % (
			type_info_name,
			gen.apply_api_prefix("get_bound_type_info"),
		)

		self._source += """
%s *%s(const char *type) {
	return nullptr;
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
		return {"wrapper.cpp": self.go_c, "wrapper.h": self.go_h, "bind.go": self.go_bind, "translate_file.json": self.go_translate_file}

	def _get_type(self, name):
		for type in self._bound_types:
			if type:
				return type
		return None

	def _get_conv(self, conv_name):
		if conv_name in self._FABGen__type_convs:
			return self.get_conv(conv_name)
		return None

	def _get_conv_from_bound_name(self, bound_name):
		for name, conv in self._FABGen__type_convs.items():
			if conv.bound_name == bound_name:
				return conv
		return None

	def __get_is_type_class_or_pointer_with_class(self, conv):
		if conv.is_type_class() or \
			(isinstance(conv, GoPtrTypeConverter) and self._get_conv(str(conv.ctype.scoped_typename)) is None):
			return True
		return False

	def __get_stars(self, val, start_stars=0, add_start_for_ref=True):
		stars = "*" * start_stars
		if "carg" in val and hasattr(val["carg"].ctype, "ref"):
			stars += "*" * (len(val["carg"].ctype.ref) if add_start_for_ref else val["carg"].ctype.ref.count('*'))
		elif "storage_ctype" in val and hasattr(val["storage_ctype"], "ref"):
			stars += "*" * (len(val["storage_ctype"].ref) if add_start_for_ref else val["storage_ctype"].ref.count('*'))
		elif hasattr(val["conv"].ctype, "ref"):
			stars += "*" * (len(val["conv"].ctype.ref) if add_start_for_ref else val["conv"].ctype.ref.count('*'))
		return stars

	def __arg_from_cpp_to_c(self, val, retval_name, just_copy):
		src = ""
		# type class, not a pointer
		if val['conv'] is not None and val['conv'].is_type_class() and \
			not val['conv'].ctype.is_pointer() and ('storage_ctype' not in val or not hasattr(val['storage_ctype'], 'ref') or not any(s in val['storage_ctype'].ref for s in ["&", "*"])):
				# special shared ptr
				if 'proxy' in val['conv']._features:
					src += f"	if(!{retval_name})\n" \
						"		return nullptr;\n"

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
				stars = self.__get_stars(val)
				if len(stars) > 0:# rarely use but just in case
					retval_name = f"new const char*(&(*{retval_name}->begin()))"
				else:
					retval_name = f"{retval_name}.c_str()"
			else:
				retval_name = f"{retval_name}"

		# cast it
		# if it's an enum
		if val["conv"].bound_name in self._enums.keys():
			enum_conv = self._get_conv_from_bound_name(val['conv'].bound_name)
			if enum_conv is not None and hasattr(enum_conv, "base_type") and enum_conv.base_type is not None:
				arg_bound_name = str(enum_conv.base_type)
			else:
				arg_bound_name = "int"
			retval_name = f"({arg_bound_name}){retval_name}"
		# cast it, if it's a const
		elif 'storage_ctype' in val and val["storage_ctype"].const or \
			'carg' in val and val["carg"].ctype.const:
			arg_bound_name = self.__get_arg_bound_name_to_c(val)
			retval_name = f"({arg_bound_name}){retval_name}"

		return src, retval_name

	def __arg_from_c_to_cpp(self, val, retval_name, add_star=True):
		src = ""
		# check if there is special slice to convert
		if isinstance(val["conv"], lib.go.stl.GoSliceToStdVectorConverter):
			# special if string or const char*
			if "GoStringConverter" in str(val["conv"].T_conv): # or \
				# "GoConstCharPtrConverter" in str(val["conv"].T_conv):
				src += f"std::vector<{val['conv'].T_conv.ctype}> {retval_name};\n"\
					f"for(int i_counter_c=0; i_counter_c < {retval_name}ToCSize; ++i_counter_c)\n"\
					f"	{retval_name}.push_back(std::string({retval_name}ToCBuf[i_counter_c]));\n"
			# slice from class
			elif self.__get_is_type_class_or_pointer_with_class(val["conv"].T_conv):
				src += f"std::vector<{val['conv'].T_conv.ctype}> {retval_name};\n"\
					f"for(int i_counter_c=0; i_counter_c < {retval_name}ToCSize; ++i_counter_c)\n"\
					f"	{retval_name}.push_back(*(({val['conv'].T_conv.ctype}**){retval_name}ToCBuf)[i_counter_c]);\n"
			else:
				src += f"std::vector<{val['conv'].T_conv.ctype}> {retval_name}(({val['conv'].T_conv.ctype}*){retval_name}ToCBuf, ({val['conv'].T_conv.ctype}*){retval_name}ToCBuf + {retval_name}ToCSize);\n"

		retval = ""
		# very special case, std::string &
		if "GoStringConverter" in str(val["conv"]) and \
			"carg" in val and hasattr(val["carg"].ctype, "ref") and any(s in val["carg"].ctype.ref for s in ["&"]):
			src += f"std::string {retval_name}_cpp(*{retval_name});\n"
			retval += f"{retval_name}_cpp"
		# std::function
		elif "GoStdFunctionConverter" in str(val["conv"]):
			func_name = val["conv"].base_type.replace("std::function<", "").replace(">", "")
			first_parenthesis = func_name.find("(")
			retval += f"({func_name[:first_parenthesis]}(*){func_name[first_parenthesis:]}){retval_name}"
		# classe or pointer on class
		else:
			if self.__get_is_type_class_or_pointer_with_class(val["conv"]):
				stars = self.__get_stars(val, add_start_for_ref=False)
				# for type pointer, there is a * in the ctype, so remove one
				if isinstance(val['conv'], GoPtrTypeConverter):
					stars = stars[1:]
				
				# if it's not a pointer, add a star anyway because we use pointer to use in go
				if (not val["conv"].ctype.is_pointer() and ("carg" not in val or ("carg" in val and not val["carg"].ctype.is_pointer()))):
					stars += "*"
					if add_star:
						retval += "*"

				retval += f"({val['conv'].ctype}{stars}){retval_name}"

			elif "carg" in val and hasattr(val["carg"].ctype, "ref") and any(s in val["carg"].ctype.ref for s in ["&"]):
				# add cast and *
				retval = f"({val['carg'].ctype})(*{retval_name})"
			# cast, if it's an enum
			elif val["conv"].bound_name in self._enums.keys():
				retval = f"({val['conv'].ctype}){retval_name}"
			else:
				retval = retval_name

		return src, retval

	def __arg_from_c_to_go(self, val, retval_name, non_owning=False):
		
		rval_ownership = self._FABGen__ctype_to_ownership_policy(val["conv"].ctype)

		src = ""
		# check if pointer 
		if ('carg' in val and (val['carg'].ctype.is_pointer() or (hasattr(val['carg'].ctype, 'ref') and any(s in val['carg'].ctype.ref for s in ["&", "*"])))) or \
			('carg' not in val and 'storage_ctype' in val and (val['storage_ctype'].is_pointer() or (hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&", "*"])))) or \
			('carg' not in val and 'storage_ctype' not in val and (val['conv']._is_pointer or val['conv'].ctype.is_pointer())):
			is_pointer = True
		else:
			is_pointer = False

		# check if ref 
		if ('carg' in val and (hasattr(val['carg'].ctype, 'ref') and any(s in val['carg'].ctype.ref for s in ["&"]))) or \
			('carg' not in val and 'storage_ctype' in val and ((hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&"])))):
			is_ref = True
		else:
			is_ref = False

		# check if need convert from c
		# if not a pointer
		if not is_pointer:
			if val['conv'].bound_name in self._enums.keys():# if it's an enum
				retval_name = f"{val['conv'].bound_name}({retval_name})"
			else:
				conversion_ret = val['conv'].from_c_call(retval_name, "", "") 
				if conversion_ret != "":
					retval_name = conversion_ret

				# if it's a class, not a pointer, only out, create the class special
				if val["conv"].is_type_class():
					retval_boundname = val["conv"].bound_name
					retval_boundname = clean_name_with_title(retval_boundname)

					src += f"	{retval_name}GO := &{retval_boundname}{{h:{retval_name}}}\n"

					# check if owning to have the right to destroy it
					if rval_ownership != "NonOwning" and not is_ref and not non_owning:
						src += f"	runtime.SetFinalizer({retval_name}GO, func(cleanval *{retval_boundname}) {{\n" \
								f"		C.Wrap{retval_boundname}Free(cleanval.h)\n" \
								f"	}})\n"
					retval_name = f"{retval_name}GO"

		# if pointer or ref
		elif is_pointer:
			# special const char * and string
			if "GoConstCharPtrConverter" in str(val["conv"]) or \
				"GoStringConverter" in str(val["conv"]):
				stars = self.__get_stars(val)

				retval_name_from_c = "*"*len(stars) + retval_name
				if "GoConstCharPtrConverter" in str(val["conv"]):
					retval_name_from_c = "*"*(len(stars) -1) + retval_name

				conversion_ret = val['conv'].from_c_call(retval_name_from_c, "", "")

				if len(stars) > 0:
					prefix = "&" * len(stars)
					if "GoConstCharPtrConverter" in str(val["conv"]):
						prefix = "&" * (len(stars)-1)

					src+= f"{retval_name}GO := string({conversion_ret})\n"
					retval_name = prefix + retval_name + "GO"
				else:
					conversion_ret = retval_name

			# if it's a class, a pointer, only out, create the class special
			elif self.__get_is_type_class_or_pointer_with_class(val["conv"]):
				retval_boundname = val['conv'].bound_name
				retval_boundname = clean_name_with_title(retval_boundname)
				src += f"var {retval_name}GO *{retval_boundname}\n" \
						f"if {retval_name} != nil {{\n" \
						f"	{retval_name}GO = &{retval_boundname}{{h:{retval_name}}}\n"

				# check if owning to have the right to destroy it
				if rval_ownership != "NonOwning" and not is_ref and not non_owning:
					src += f"	runtime.SetFinalizer({retval_name}GO, func(cleanval *{retval_boundname}) {{\n" \
							f"		C.Wrap{retval_boundname}Free(cleanval.h)\n"\
							f"	}})\n"
				src += "}\n"
				retval_name = f"{retval_name}GO"
			else:
				retval_name = f"({self.__get_arg_bound_name_to_go(val)})(unsafe.Pointer({retval_name}))\n"

		return src, retval_name

	def __arg_from_go_to_c(self, val, arg_name):
		def convert_got_to_c(val, arg_name, arg_out_name, start_stars=0):
			stars = self.__get_stars(val, start_stars)

			if val["conv"].is_type_class():
				c_call = f"{clean_name(arg_out_name).replace('&', '_')} := ({stars}C.Wrap{clean_name_with_title(val['conv'].bound_name)})(unsafe.Pointer({clean_name(arg_name)}))\n"
			else:
				# get base conv (without pointer)
				base_conv = self._get_conv(str(val["conv"].ctype.scoped_typename))
				if base_conv is None:
					if isinstance(val["conv"], GoPtrTypeConverter):
						c_call = f"{clean_name(arg_out_name).replace('&', '_')} := ({stars[1:]}C.Wrap{clean_name_with_title(val['conv'].bound_name)})(unsafe.Pointer({clean_name(arg_name)}))\n"
					else:
						c_call = f"{clean_name(arg_out_name).replace('&', '_')} := ({stars}{str(val['conv'].bound_name)})(unsafe.Pointer({clean_name(arg_name)}))\n"
				elif hasattr(base_conv, "go_to_c_type") and base_conv.go_to_c_type is not None:
					c_call = f"{clean_name(arg_out_name).replace('&', '_')} := ({stars}{base_conv.go_to_c_type})(unsafe.Pointer({clean_name(arg_name)}))\n"
				else:
					c_call = f"{clean_name(arg_out_name).replace('&', '_')} := ({stars}{base_conv.bound_name})(unsafe.Pointer({clean_name(arg_name)}))\n"
			return c_call
		
		c_call = ""
		# if it's a pointer on something
		if isinstance(val["conv"], GoPtrTypeConverter):
			base_conv = self._get_conv(str(val["conv"].ctype.scoped_typename))
			if base_conv is None or base_conv.is_type_class():
				c_call = f"{clean_name(arg_name)}ToC := {clean_name(arg_name)}.h\n"
			else:
				c_call = convert_got_to_c(val, arg_name, f"{arg_name}ToC")
		# if it's a class
		elif val["conv"].is_type_class():
			stars = self.__get_stars(val)
			c_call = f"{clean_name(arg_name)}ToC := {stars[1:]}{clean_name(arg_name)}.h\n"
		# if it's an enum
		elif val["conv"].bound_name in self._enums.keys():
			enum_conv = self._get_conv_from_bound_name(val["conv"].bound_name)
			if enum_conv is not None and hasattr(enum_conv, "go_to_c_type") and enum_conv.go_to_c_type is not None:
				arg_bound_name = enum_conv.go_to_c_type
			else:
				arg_bound_name = "C.int"
				
			c_call = f"{clean_name(arg_name)}ToC := {arg_bound_name}({clean_name(arg_name)})\n"
		# special Slice
		elif isinstance(val["conv"], lib.go.stl.GoSliceToStdVectorConverter):
			c_call = ""
			slice_name = clean_name(arg_name)
			# special if string or const char*
			if "GoConstCharPtrConverter" in str(val["conv"].T_conv) or \
				"GoStringConverter" in str(val["conv"].T_conv):
				c_call += f"var {slice_name}SpecialString []*C.char\n"
				c_call += f"for _, s := range {slice_name} {{\n"
				c_call += f"	{slice_name}SpecialString = append({slice_name}SpecialString, C.CString(s))\n"
				c_call += f"}}\n"
				slice_name = f"{slice_name}SpecialString"

			# if it's a class, get a list of pointer to c class
			elif self.__get_is_type_class_or_pointer_with_class(val["conv"].T_conv):
				c_call += f"var {slice_name}Pointer  []C.Wrap{clean_name_with_title(val['conv'].T_conv.bound_name)}\n"
				c_call += f"for _, s := range {slice_name} {{\n"
				c_call += f"	{slice_name}Pointer = append({slice_name}Pointer, s.h)\n"
				c_call += f"}}\n"
				slice_name = f"{slice_name}Pointer"

			c_call += f"{slice_name}ToC := (*reflect.SliceHeader)(unsafe.Pointer(&{slice_name}))\n"
			c_call += f"{slice_name}ToCSize := C.size_t({slice_name}ToC.Len)\n"

			c_call += convert_got_to_c({"conv": val["conv"].T_conv}, f"{slice_name}ToC.Data", f"{slice_name}ToCBuf", 1)
		# std function
		elif "GoStdFunctionConverter" in str(val["conv"]):
			c_call += f"{clean_name(arg_name)}ToC := (C.Wrap{clean_name_with_title(val['conv'].bound_name)})({clean_name(arg_name)})\n"
		else:
			how_many_stars = 0
			# compute how many stars (to handle specifically the const char *)
			if "carg" in val:
				if hasattr(val["carg"].ctype, "ref") and any(s in val["carg"].ctype.ref for s in ["&", "*"]):
					how_many_stars = len(val["carg"].ctype.ref)
				elif val["carg"].ctype.is_pointer():
					how_many_stars = 1
			else:
				if hasattr(val["conv"].ctype, "ref") and any(s in val["conv"].ctype.ref for s in ["&", "*"]):
					how_many_stars = len(val["conv"].ctype.ref)
				elif val["conv"].ctype.is_pointer() :
					how_many_stars = 1
			
			is_pointer = True
			if how_many_stars == 0 or \
				(how_many_stars == 1 and "GoConstCharPtrConverter" in str(val["conv"])):
				is_pointer = False
			c_call = val["conv"].to_c_call(clean_name(arg_name), f"{clean_name(arg_name)}ToC", is_pointer)
		return c_call

	def __get_arg_bound_name_to_go(self, val):
		if val["conv"].is_type_class():
			arg_bound_name = val["conv"].bound_name
		else:
			# check the convert from the base (in case of ptr) or a string
			if ('carg' in val and (val['carg'].ctype.is_pointer() or (hasattr(val['carg'].ctype, 'ref') and any(s in val['carg'].ctype.ref for s in ["&", "*"])))) or \
				('storage_ctype' in val and (val['storage_ctype'].is_pointer() or (hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&", "*"])))) or \
				isinstance(val['conv'], GoPtrTypeConverter):

				if hasattr(val["conv"], "go_type") and val["conv"].go_type is not None:
					arg_bound_name = str(val["conv"].go_type)
				else:
					base_conv = self._get_conv(str(val['conv'].ctype.scoped_typename))
					if base_conv is None:
						arg_bound_name = str(val["conv"].bound_name)
					else:
						if hasattr(base_conv, "go_type") and base_conv.go_type is not None:
							arg_bound_name = base_conv.go_type
						else:
							arg_bound_name = base_conv.bound_name
			else:
				if val['conv'].bound_name in self._enums.keys():# if it's an enum
					arg_bound_name = f"{val['conv'].bound_name}"
				elif hasattr(val["conv"], "go_type") and val["conv"].go_type is not None:
					arg_bound_name = val["conv"].go_type
				else:
					arg_bound_name = val["conv"].bound_name

		if arg_bound_name.endswith("_nobind") and val["conv"].nobind:
			arg_bound_name = arg_bound_name[:-len("_nobind")]

		# if it's a pointer and not a string
		if (('carg' in val and (val['carg'].ctype.is_pointer() or (hasattr(val['carg'].ctype, 'ref') and any(s in val['carg'].ctype.ref for s in ["&", "*"])))) or \
			('storage_ctype' in val and (val['storage_ctype'].is_pointer() or (hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&", "*"])))) or \
			isinstance(val['conv'], GoPtrTypeConverter)):
			# find how many * we need to add
			stars = "*"
			if "carg" in val and hasattr(val["carg"].ctype, "ref"):
				stars += "*" * (len(val["carg"].ctype.ref) - 1)
			if "storage_ctype" in val and hasattr(val["storage_ctype"], "ref"):
				stars += "*" * (len(val["storage_ctype"].ref) - 1)

			# special const char *
			if "GoConstCharPtrConverter" in str(val["conv"]):
				stars = stars[1:]

			# Harfang class doesn't need to be a pointer in go (because it's a struct containing a wrap pointer C)
			if not self.__get_is_type_class_or_pointer_with_class(val["conv"]):
				arg_bound_name = stars + arg_bound_name

		# std function
		if "GoStdFunctionConverter" in str(val["conv"]):
			arg_bound_name = "unsafe.Pointer"

		# class or slice, clean the name with title
		if self.__get_is_type_class_or_pointer_with_class(val["conv"]) or \
			isinstance(val['conv'], lib.go.stl.GoSliceToStdVectorConverter):
			arg_bound_name = clean_name_with_title(arg_bound_name)

		# i'f it's a class, it's a pointer
		if self.__get_is_type_class_or_pointer_with_class(val["conv"]):
			arg_bound_name = "*" + arg_bound_name
			
		return arg_bound_name

	def __get_arg_bound_name_to_c(self, val):
		arg_bound_name = ""

		# check to add const
		if 'storage_ctype' in val and val["storage_ctype"].const or \
			'carg' in val and val["carg"].ctype.const:
			arg_bound_name += "const "
		
		# if class or pointer with class
		if self.__get_is_type_class_or_pointer_with_class(val["conv"]) or \
			"GoStdFunctionConverter" in str(val["conv"]):
			arg_bound_name += f"Wrap{clean_name_with_title(val['conv'].bound_name)} "
		else:
			# check the convert from the base (in case of ptr)
			if  ('carg' in val and (val['carg'].ctype.is_pointer() or (hasattr(val['carg'].ctype, 'ref') and any(s in val['carg'].ctype.ref for s in ["&", "*"])))) or \
				('storage_ctype' in val and (val['storage_ctype'].is_pointer() or (hasattr(val['storage_ctype'], 'ref') and any(s in val['storage_ctype'].ref for s in ["&", "*"])))) or \
				isinstance(val['conv'], GoPtrTypeConverter):
				# check if it's an enum
				if val['conv'].bound_name in self._enums.keys():
					enum_conv = self._get_conv_from_bound_name(val['conv'].bound_name)
					if enum_conv is not None and hasattr(enum_conv, "base_type") and enum_conv.base_type is not None:
						arg_bound_name = str(enum_conv.base_type)
					else:
						arg_bound_name = "int"
				else:
					# sometimes typedef is weird and don't give valid value, so check it
					base_conv = self._get_conv(str(val['conv'].bound_name))
					if base_conv is None:
						# check with typedef
						if hasattr(val['conv'], "base_type") and val['conv'].base_type is not None:
							arg_bound_name = str(val['conv'].base_type)
						else:
							if 'storage_ctype' in val:
								arg_bound_name += f"{val['storage_ctype']} "
							else:
								arg_bound_name += f"{val['conv'].ctype} "
					
						# if it's a ptr type, remove a star
						if isinstance(val['conv'], GoPtrTypeConverter):
							arg_bound_name = arg_bound_name.replace("*", "").replace("&", "")
					else:
						arg_bound_name += f"{val['conv'].bound_name} "

				# add a star (only if it's not a const char * SPECIAL CASE)
				if "GoConstCharPtrConverter" not in str(val["conv"]):
					arg_bound_name += "*"

				if "carg" in val and hasattr(val["carg"].ctype, "ref"):
					arg_bound_name += "*" * (len(val["carg"].ctype.ref) - 1)
				if "storage_ctype" in val and hasattr(val["storage_ctype"], "ref"):
					arg_bound_name += "*" * (len(val["storage_ctype"].ref) - 1)
			else:
				# check if it's an enum
				if val['conv'].bound_name in self._enums.keys():
					enum_conv = self._get_conv_from_bound_name(val['conv'].bound_name)
					if enum_conv is not None and hasattr(enum_conv, "base_type") and enum_conv.base_type is not None:
						arg_bound_name = str(enum_conv.base_type)
					else:
						arg_bound_name = "int"
				else:
					# sometimes typedef is weird and don't give valid value, so check it
					base_conv = self._get_conv(str(val['conv'].bound_name))
					if base_conv is None:
						if hasattr(val['conv'], "base_type") and val['conv'].base_type is not None:
							arg_bound_name = str(val['conv'].base_type)
						else:
							if 'storage_ctype' in val:
								arg_bound_name += f"{val['storage_ctype']} "
							else:
								arg_bound_name += f"{val['conv'].ctype} "
					else:
						arg_bound_name += f"{val['conv'].bound_name} "
		return arg_bound_name

	def __extract_sequence_go(self, conv):
		go = ""

		classname = clean_name_with_title(conv.bound_name)

		internal_conv = conv._features["sequence"].wrapped_conv

		arg_bound_name = self.__get_arg_bound_name_to_go({"conv": internal_conv})

		# GET
		go += f"// Get ...\n" \
				f"func (pointer *{classname}) Get(id int) {arg_bound_name} {{\n"
		go += f"v := C.Wrap{classname}GetOperator(pointer.h, C.int(id))\n"

		src, retval_go = self.__arg_from_c_to_go({"conv": internal_conv}, "v")
		go += src
		go += f"return {retval_go}\n"
		go += "}\n"

		# SET
		go += f"// Set ...\n" \
				f"func (pointer *{classname}) Set(id int, v {arg_bound_name}) {{\n"
		# convert to c
		c_call = self.__arg_from_go_to_c({"conv": internal_conv}, "v")
		if c_call != "":
			go += c_call
		else:
			go += "vToC := v\n"

		go += f"	C.Wrap{classname}SetOperator(pointer.h, C.int(id), vToC)\n"
		go += "}\n"

		# Len
		go += f"// Len ...\n" \
				f"func (pointer *{classname}) Len() int32 {{\n"
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
		c_arg_bound_name = c_arg_bound_name.replace("const const", "const")

		# GET
		if is_in_header:
			go += "extern "
		go += f"{c_arg_bound_name} Wrap{cleanClassname}GetOperator(Wrap{cleanClassname} h, int id)"

		if is_in_header:
			go += ";\n"
		else:
			go += f"{{\n" \
				"	bool error;\n" \
				f"	{internal_conv.ctype} v;\n	"
			go += conv._features['sequence'].get_item(f"(({conv.ctype}*)h)", "id", "v", "error")

			src, retval_c = self.__arg_from_cpp_to_c({"conv": internal_conv}, "v", False)
			go += src
			go += f"	return {retval_c};\n}}\n"

		# SET
		if is_in_header:
			go += "extern "
		go += f"void Wrap{cleanClassname}SetOperator(Wrap{cleanClassname} h, int id, {c_arg_bound_name} v)"

		if is_in_header:
			go += ";\n"
		else:
			go += f"{{\n" \
				"	bool error;\n"

			src, inval = self.__arg_from_c_to_cpp({"conv": internal_conv}, "v", False)
			go += src

			go += conv._features['sequence'].set_item(f"(({conv.ctype}*)h)", "id", inval, "error")
			go += f"\n}}\n"

		# LEN
		if is_in_header:
			go += "extern "
		go += f"int Wrap{cleanClassname}LenOperator(Wrap{cleanClassname} h)"

		if is_in_header:
			go += ";\n"
		else:
			go += f"{{\n" \
				"	int size;\n	"
			go += conv._features['sequence'].get_size(f"(({conv.ctype}*)h)", "size")
			go += f"	return size;\n}}\n"

		return go

	def __extract_get_set_member_go(self, classname, member, static=False, name=None, bound_name=None, is_global=False, implicit_cast=None):
		go = ""
		conv = self.select_ctype_conv(member["ctype"])

		if "bound_name" in member:
			bound_name = str(member["bound_name"])
		elif bound_name is None:
			bound_name = str(member["name"])
		if name is None:
			name = bound_name

		name = name.replace(":", "")
		name = clean_name_with_title(name)

		arg_bound_name = self.__get_arg_bound_name_to_go({"conv": conv})

		def create_get_set(do_static):
			# GET
			go = ""

			# if it's a const, just write it once
			if is_global and member["ctype"].const:
				go += f"// {name} ...\n"
				if self.__get_is_type_class_or_pointer_with_class(conv):
					go += f"var {clean_name(name)} = {arg_bound_name.replace('*', '')}{{h:C.Wrap{clean_name_with_title(classname)}Get{name}()}}\n"
				elif implicit_cast is not None:
					go += f"var {clean_name(name)} = {implicit_cast}(C.Wrap{clean_name_with_title(classname)}Get{name}())\n"
				else:
					go += f"var {clean_name(name)} = {arg_bound_name}(C.Wrap{clean_name_with_title(classname)}Get{name}())\n"
			else:
				go += "// "
				if do_static:
					go += f"{clean_name_with_title(classname)}"
				go += f"Get{name} ...\n"
				go += f"func "
				if do_static:
					go += f"{clean_name_with_title(classname)}"
				else:
					go += f"(pointer *{clean_name_with_title(classname)}) "

				go += f"Get{name}() {arg_bound_name} {{\n"
				go += f"v := C.Wrap{clean_name_with_title(classname)}Get{name}("
				if not static and not is_global:
					go += "pointer.h"
				go += ")\n"

				# check if need convert from c
				src, retval_go = self.__arg_from_c_to_go({"conv": conv}, "v", True)
				go += src
				go += f"return {retval_go}\n"

				go += "}\n"

			# SET
			# add set only if the member is not const
			if not member["ctype"].const:
				go += f"// "
				if do_static:
					go += f"{clean_name_with_title(classname)}"
				go += f"Set{name} ...\n" \
						f"func "
						
				if do_static:
					go += f"{clean_name_with_title(classname)}"
				else:
					go += f"(pointer *{clean_name_with_title(classname)}) "

				go += f"Set{name}(v {arg_bound_name}) {{\n"

				# convert to c
				c_call = self.__arg_from_go_to_c({"conv": conv}, "v")
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
		name = clean_name_with_title(name)

		c_name = str(member["name"])

		cleanClassname = clean_name_with_title(classname)

		# special Slice
		if isinstance(conv, lib.go.stl.GoSliceToStdVectorConverter):
			arg_bound_name = self.__get_arg_bound_name_to_c({"conv": conv.T_conv})
		else:
			arg_bound_name = self.__get_arg_bound_name_to_c({"conv": conv})
		
		# special std::string (convert to const char*)
		c_arg_bound_name = arg_bound_name.replace("std::string", "const char*")
		c_arg_bound_name = c_arg_bound_name.replace("const const", "const")

		# GET
		if is_in_header:
			go += "extern "

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
				if convClass is not None:
					go += f"	auto ret = {prefix}{convClass.ctype}::{c_name};\n"
				else:
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
		if not(member["ctype"].const or conv._non_copyable):
			if is_in_header:
				go += "extern "

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
					if convClass is not None:
						go += f"{{ {convClass.ctype}::{c_name} = {inval};\n}}\n"
					else:
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
			# add bounding_name to the overload function
			if "bound_name" in proto["features"]:
				go += proto["features"]["bound_name"]
			# if automatic suffix generated
			elif "suggested_suffix" in proto:
				go += proto["suggested_suffix"]

			# get doc
			if classname == "" or is_constructor:
				doc = self.get_symbol_doc(bound_name)
			else:
				doc = self.get_symbol_doc(classname + "_" + bound_name)

			if doc == "":
				go += " ...\n"
			else:
				go += " " + re.sub(r'(\[)(.*?)(\])', r'\1harfang.\2\3', doc) + "\n"

			go += "func "
			if not is_global:
				go += f"(pointer *{clean_name_with_title(classname)}) "
			go += f"{clean_name_with_title(name_go)}"

			# add bounding_name to the overload function
			if "bound_name" in proto["features"]:
				go += proto["features"]["bound_name"]
			# if automatic suffix generated
			elif "suggested_suffix" in proto:
				go += proto["suggested_suffix"]

			# add input(s) declaration
			go += "("
			if len(proto["args"]):
				has_previous_arg = False
				for argin in proto["argsin"]:
					if has_previous_arg:
						go += " ,"

					# check if the input is in feature constant group, overrite the type
					if "features" in proto and "constants_group" in proto["features"] and str(argin["carg"].name) in proto["features"]["constants_group"]:
						go += f"{clean_name(argin['carg'].name)} {proto['features']['constants_group'][str(argin['carg'].name)]}"
					else:
						go += f"{clean_name(argin['carg'].name)} {self.__get_arg_bound_name_to_go(argin)}"
					has_previous_arg = True

			go += ")"

			# add output(s) declaration
			go += "("
			has_previous_ret_arg = False
			if proto["rval"]["conv"]:
				go += self.__get_arg_bound_name_to_go(proto["rval"])
				has_previous_ret_arg = True
			
			# only add arg output, NOT ARG IN OUT (pass them by pointer, not return them)
			if len(proto['args']):
				for arg in proto['args']:
					if 'arg_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_out']:
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
						arg_bound_name = self.__get_arg_bound_name_to_go(arg)

						if arg["carg"].ctype.is_pointer() or (hasattr(arg["carg"].ctype, "ref") and arg["carg"].ctype.ref == "&"):
							# if it's a arg out and a class
							if self.__get_is_type_class_or_pointer_with_class(arg["conv"]):
								arg_bound_name = clean_name_with_title(f"new_{arg_bound_name.replace('*', '')}")
								# find the constructor without arg
								for arg_conv in self._bound_types:
									if str(arg_conv.ctype) == str(arg["conv"].ctype) and hasattr(arg_conv, "constructor") and arg_conv.constructor is not None:
										proto_args = self._build_protos(arg_conv.constructor["protos"])
										break
								else:
									proto_args = None
								
								id_proto_without_arg = ""
								if proto_args is not None and len(proto_args) > 1:
									for id_proto_arg, proto_arg in enumerate(proto_args):
										if len(proto_arg['args']) <= 0:
											# add bounding_name to the overload function
											if "bound_name" in proto_arg["features"]:
												id_proto_without_arg = proto_arg["features"]["bound_name"]
											# if automatic suffix generated
											elif "suggested_suffix" in proto_arg:
												id_proto_without_arg = proto_arg["suggested_suffix"]
											break

								go += f"{clean_name(arg['carg'].name)} := {arg_bound_name}{id_proto_without_arg}()\n"
							else:
								# not a class, remove the * and make a new
								go += f"{clean_name(arg['carg'].name)} := new({arg_bound_name.replace('*', '')})\n"
						else:
							go += f"var {clean_name(arg['carg'].name)} {arg_bound_name}\n"

					c_call = ""
					if arg["conv"]:
						c_call = self.__arg_from_go_to_c(arg, arg['carg'].name)
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

			# add bounding_name to the overload function
			if "bound_name" in proto["features"]:
				go += proto["features"]["bound_name"]
			# if automatic suffix generated
			elif "suggested_suffix" in proto:
				go += proto["suggested_suffix"]

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
						slice_name = clean_name(arg['carg'].name)
						if "GoConstCharPtrConverter" in str(arg["conv"].T_conv) or \
							"GoStringConverter" in str(arg["conv"].T_conv):	
							slice_name = f"{slice_name}SpecialString"
						# if it's a class, get a list of pointer to c class
						elif self.__get_is_type_class_or_pointer_with_class(arg["conv"].T_conv):
							slice_name = f"{slice_name}Pointer"
						go += f"{slice_name}ToCSize, {slice_name}ToCBuf"
					else:
						# if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and \
						# 	arg['conv'].bound_name != "string" and not arg['conv'].is_type_class():
						# 	go += "&"
						go += f"{clean_name(arg['carg'].name)}ToC"

					has_previous_arg = True
			go += ")\n"
			ret_args = []
			if retval != "":
				src, retval_go = self.__arg_from_c_to_go(proto["rval"], "retval")
				go += src

				ret_args.append(retval_go)

			# return arg out
			# only add arg output, NOT ARG IN OUT (pass them by pointer, not return them)
			if "arg_out" in proto["features"]:
				for arg in proto['args']:
					if 'arg_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_out']:
						# add name
						retval_go = clean_name(str(arg["carg"].name))
						# if it's a arg out and a class, don't convert because it was already done upper
						if not self.__get_is_type_class_or_pointer_with_class(arg["conv"]):
							retval_go = clean_name(str(arg["carg"].name)) + "ToC"
							src, retval_go = self.__arg_from_c_to_go(arg, retval_go)
							go += src
							
						ret_args.append(retval_go)

			if len(ret_args) > 0:
				go += "return "
			has_previous_arg = False
			for retarg in ret_args:
				if has_previous_arg:
					# check and remove "\n" just in case
					if go[-1] == "\n":
						go = go[:-1]
					go += ", "
				has_previous_arg = True
				go += retarg
				
			# check and remove "\n" just in case
			if go[-1] == "\n":
				go = go[:-1]
			go += "\n}\n"

		return go

	def __extract_method(self, classname, convClass, method, static=False, name=None, bound_name=None, is_global=False, is_in_header=False, is_constructor=False, overload_op=None):
		go = ""

		if bound_name is None:
			bound_name = method["bound_name"]
		if name is None:
			name = bound_name
		wrap_name = bound_name

		cpp_function_name = name
		if "name" in method:
			cpp_function_name = method["name"]

		if bound_name == "OpenVRStateToViewState":
			bound_name = bound_name

		uid = classname + bound_name if classname else bound_name

		protos = self._build_protos(method["protos"])
		for id_proto, proto in enumerate(protos):
			retval = "void"

			if str(proto["rval"]["storage_ctype"]) != "void":
				retval = self.__get_arg_bound_name_to_c(proto["rval"])

				# special std::string (convert to const char*)
				retval = retval.replace("std::string", "const char*")
				retval = retval.replace("const const", "const")

			if is_in_header:
				go += "extern "
			go += f"{retval} Wrap{clean_name_with_title(wrap_name)}"

			# not global, add the Name of the class to be sure to avoid double name function name
			if not is_global or (not is_constructor and is_global and convClass is not None):
				go += f"{clean_name_with_title(convClass.bound_name)}"

			# add bounding_name to the overload function
			if "bound_name" in proto["features"]:
				go += proto["features"]["bound_name"]
			# if automatic suffix generated
			elif "suggested_suffix" in proto:
				go += proto["suggested_suffix"]

			go += "("

			has_previous_arg = False
			# not global, member class, include the "this" pointer first
			if not is_global or (not is_constructor and is_global and convClass is not None):
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
					arg_bound_name = arg_bound_name.replace("const const", "const")

					# special Slice
					if isinstance(argin["conv"], lib.go.stl.GoSliceToStdVectorConverter):
						go += f"size_t {clean_name(argin['carg'].name)}ToCSize, {arg_bound_name} *{clean_name(argin['carg'].name)}ToCBuf"
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
				if "route" in proto["features"] and convClass is not None and not is_constructor:
					args.append(f"({convClass.ctype}*)this_")

				# convert arg to cpp
				if len(proto["args"]):
					# if the function is global but have a convclass,
					# special case, which include the class has arg in first arg
					if  not is_constructor and is_global and convClass is not None:
						src, retval_c = self.__arg_from_c_to_cpp({"conv":convClass}, "this_")
						go += src
						args.append(retval_c)

					# other normal args
					for argin in proto["args"]:
						# special Slice
						if isinstance(argin["conv"], lib.go.stl.GoSliceToStdVectorConverter):
							src, retval_c = self.__arg_from_c_to_cpp(argin, clean_name(str(argin["carg"].name)))
						else:
							src, retval_c = self.__arg_from_c_to_cpp(argin, str(argin["carg"].name))
						go += src
						args.append(retval_c)

				if is_constructor:
					# constructor, make our own return
					retval = "void"
					# if another route is set
					if "route" in proto["features"]:
						go += f"	return (void*){proto['features']['route'](args)}\n"
					elif "proxy" in convClass._features:
						go += "	auto " + convClass._features["proxy"].wrap(f"new {convClass._features['proxy'].wrapped_conv.bound_name}({','.join(args)})", "v")
						go += "	return v;\n"
					else:
						go += f"	return (void*)(new {convClass.ctype}({','.join(args)}));\n"
				else:
					# if there is return value
					if retval != "void":
						go += "	auto ret = "

					# special comparison
					if overload_op is not None:
							go += f"(*({convClass.ctype}*)this_)"
							go += overload_op
							go += f"({args[0]});\n"
					# classic call to function
					else:
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

							# cpp function name
							go += cpp_function_name

							# add function's arguments
							go += f"({','.join(args)});\n"

						# return arg out
						if "arg_out" in proto["features"] or "arg_in_out" in proto["features"]:
							for arg in proto['args']:
								if ('arg_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_out']) or \
									('arg_in_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_in_out']):
									# FOR NOW ONLY FOR THE STD::STRING
									if "GoStringConverter" in str(arg["conv"]) and \
										"carg" in arg and hasattr(arg["carg"].ctype, "ref") and any(s in arg["carg"].ctype.ref for s in ["&"]):
										# it's a pointer (or there is a bug)
										retval_cpp = f"(&({str(arg['carg'].name)}_cpp))"
										src, retval_cpp = self.__arg_from_cpp_to_c(arg, retval_cpp, static)
										go += src
										go += f"	{str(arg['carg'].name)} = {retval_cpp};\n"

				if retval != "void":
					src, retval_c = self.__arg_from_cpp_to_c(proto["rval"], "ret", static)
					go += src
					go += f"return {retval_c};\n"
				go += "}\n"

		return go

	# VERY SPECIAL
	# check in every methods, 
	# if one arg is only out and if it's a class, if there is a constructor with no arg
	def _check_arg_out_add_constructor_if_needed(self, method):
		def check_if_val_have_constructor(val):
			# if it's a arg out and a class
			if self.__get_is_type_class_or_pointer_with_class(val["conv"]):
				# find the constructor without arg
				type_conv = None
				for arg_conv in self._bound_types:
					if str(arg_conv.ctype) == str(val["conv"].ctype):
						type_conv = arg_conv
						if hasattr(arg_conv, "constructor") and arg_conv.constructor is not None:
							proto_args = self._build_protos(arg_conv.constructor["protos"])
							break
				else:
					proto_args = None
				
				# if no proto constructor with no args, add one
				if proto_args is None and type_conv is not None:
					self.bind_constructor(type_conv, [])

		# check all protos
		protos = self._build_protos(method["protos"])
		for proto in protos:
			# convert arg in to c
			if len(proto["args"]):
				for arg in proto["args"]:
					# if arg out only, declare this value
					if "arg_out" in proto["features"] and str(arg["carg"].name) in proto["features"]["arg_out"]:
						if arg["carg"].ctype.is_pointer() or (hasattr(arg["carg"].ctype, "ref") and arg["carg"].ctype.ref == "&"):
							check_if_val_have_constructor(arg)

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

				# VERY SPECIAL
				# check in every methods, 
				# if one arg is only out and if it's a class, if there is a constructor with no arg
				for method in conv.static_methods+conv.methods:	
					self._check_arg_out_add_constructor_if_needed(method)

			# add down cast
			for base in conv._bases:
				self.add_cast(base, conv, lambda in_var, out_var: "%s = (%s *)((%s *)%s);\n" % (out_var, conv.ctype, base.ctype, in_var))

		# VERY SPECIAL
		# check in every methods, 
		# if one arg is only out and if it's a class, if there is a constructor with no arg
		for func in self._FABGen__function_declarations.values():
			self._check_arg_out_add_constructor_if_needed(func)

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
			
		# enum
		for bound_name, enum in self._enums.items():
			enum_conv = self._get_conv_from_bound_name(bound_name)
			if enum_conv is not None and hasattr(enum_conv, "base_type") and enum_conv.base_type is not None:
				arg_bound_name = str(enum_conv.base_type)
			else:
				arg_bound_name = "int"
				
			go_h += f"extern {arg_bound_name} Get{bound_name}(const int id);\n"

		# write all typedef first
		for conv in self._bound_types:
			if conv.nobind:
				continue

			cleanBoundName = clean_name_with_title(conv.bound_name)
			if self.__get_is_type_class_or_pointer_with_class(conv) :
				go_h += f"typedef void* Wrap{cleanBoundName};\n"

			if "GoStdFunctionConverter" in str(conv):
				func_name = conv.base_type.replace("std::function<", "").replace(">", "").replace("&", "*")
				first_parenthesis = func_name.find("(")
				# get all args boundname in c
				args = func_name[first_parenthesis+1:-1].split(",")
				args_boundname = []
				for arg in args:
					if len(arg):
						ctype = parse(arg, gen._CType)
						conv = self.select_ctype_conv(ctype)
						args_boundname.append(self.__get_arg_bound_name_to_c({"conv": conv, "carg": type('carg', (object,), {'ctype':ctype})()}))

				go_h += f"typedef {func_name[:first_parenthesis]} (*Wrap{cleanBoundName})({','.join(args_boundname)});\n"

		# write the rest of the classes
		for conv in self._bound_types:
			if conv.nobind:
				continue

			cleanBoundName = clean_name_with_title(conv.bound_name)

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

			# destructor for all type class
			if self.__get_is_type_class_or_pointer_with_class(conv) :
				go_h += f"extern void Wrap{cleanBoundName}Free(Wrap{cleanBoundName});\n"

			# arithmetic operators
			go_h += extract_conv_and_bases(conv.arithmetic_ops, \
									lambda arithmetic: self.__extract_method(conv.bound_name, conv, arithmetic, is_in_header=True, name=arithmetic['op'], bound_name=gen.get_clean_symbol_name(arithmetic['op'])), \
									[base_class.arithmetic_ops for base_class in conv._bases])

			# comparison_ops
			go_h += extract_conv_and_bases(conv.comparison_ops, \
									lambda comparison: self.__extract_method(conv.bound_name, conv, comparison, is_in_header=True, name=comparison['op'], bound_name=gen.get_clean_symbol_name(comparison['op'])), \
									[base_class.comparison_ops for base_class in conv._bases])

			# static methods
			go_h += extract_conv_and_bases(conv.static_methods, \
									lambda method: self.__extract_method(conv.bound_name, conv, method, static=True, is_in_header=True), \
									[base_class.static_methods for base_class in conv._bases])
			# methods
			go_h += extract_conv_and_bases(conv.methods, \
									lambda method: self.__extract_method(conv.bound_name, conv, method, is_in_header=True), \
									[base_class.methods for base_class in conv._bases])
				
			
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
			go_c += "".join(['#include "%s"\n\n' % path for path in self._FABGen__system_includes])
		if len(self._FABGen__user_includes) > 0:
			go_c += "".join(['#include "%s"\n\n' % path for path in self._FABGen__user_includes])

		go_c += self._source

		# enum
		for bound_name, enum in self._enums.items():
			enum_conv = self._get_conv_from_bound_name(bound_name)
			if enum_conv is not None and hasattr(enum_conv, "base_type") and enum_conv.base_type is not None:
				arg_bound_name = str(enum_conv.base_type)
			else:
				arg_bound_name = "int"

			enum_vars = []
			for name, value in enum.items():
				enum_vars.append(f"({arg_bound_name}){value}")
			go_c += f"static const {arg_bound_name} Wrap{bound_name} [] = {{ {', '.join(enum_vars)} }};\n"
			go_c += f"{arg_bound_name} Get{bound_name}(const int id) {{ return Wrap{bound_name}[id];}}\n"

		#  classes
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
				
			# destructor for all type class
			if self.__get_is_type_class_or_pointer_with_class(conv) :
				# delete
				go_c += f"void Wrap{cleanBoundName}Free(Wrap{cleanBoundName} h){{" \
						f"delete ({conv.ctype}*)h;" \
						f"}}\n" 

			# arithmetic operators
			go_c += extract_conv_and_bases(conv.arithmetic_ops, \
									lambda arithmetic: self.__extract_method(conv.bound_name, conv, arithmetic, name=arithmetic['op'], bound_name=gen.get_clean_symbol_name(arithmetic['op']), overload_op=arithmetic["op"]), \
									[base_class.arithmetic_ops for base_class in conv._bases])

			# comparison_ops
			go_c += extract_conv_and_bases(conv.comparison_ops, \
									lambda comparison: self.__extract_method(conv.bound_name, conv, comparison, name=comparison["op"], bound_name=gen.get_clean_symbol_name(comparison["op"]), overload_op=comparison["op"]), \
									[base_class.comparison_ops for base_class in conv._bases])

			# static methods
			go_c += extract_conv_and_bases(conv.static_methods, \
									lambda method: self.__extract_method(conv.bound_name, conv, method, static=True), \
									[base_class.static_methods for base_class in conv._bases])
			# methods
			go_c += extract_conv_and_bases(conv.methods, \
									lambda method: self.__extract_method(conv.bound_name, conv, method), \
									[base_class.methods for base_class in conv._bases])

		# functions
		for func in self._bound_functions:
			go_c += self.__extract_method("", None, func, name=func["name"], is_global=True)

		# global variables
		for var in self._bound_variables:
			go_c += self.__extract_get_set_member("", None, var, is_global=True, static=True)

		self.go_c = go_c

		# .go
		go_bind = f"package {clean_name(self._name)}\n" \
				'// #include "wrapper.h"\n' \
				'// #cgo CFLAGS: -I . -Wall -Wno-unused-variable -Wno-unused-function -O3\n' \
				'// #cgo CXXFLAGS: -std=c++14 -O3\n' \
				f"// #cgo LDFLAGS: -lstdc++ -L. -l{self._name}\n" \
				'import "C"\n\n' \
				'import (\n'
		# check if reflect package is needed
		for conv in self._FABGen__type_convs.values():
			# special Slice
			if isinstance(conv, lib.go.stl.GoSliceToStdVectorConverter):
				go_bind += '	"reflect"\n'
				break
		# add runtime package if we have class
		for conv in self._FABGen__type_convs.values():
			if self.__get_is_type_class_or_pointer_with_class(conv):
				go_bind += '	"runtime"\n'
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

			# it's class
			if self.__get_is_type_class_or_pointer_with_class(conv):
				doc = self.get_symbol_doc(conv.bound_name)
				if doc == "":
					doc = " ..."
				else:
					doc = " " + re.sub(r'(\[)(.*?)(\])', r'\1harfang.\2\3', doc)

				go_bind += f"// {cleanBoundName} {doc}\n" \
							f"type {cleanBoundName} struct{{\n" \
							f"	h C.Wrap{cleanBoundName}\n" \
							"}\n"
			
			# it's a sequence
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

			# destructor for all type class
			if self.__get_is_type_class_or_pointer_with_class(conv) :
				go_bind += f"// Free ...\n" \
				f"func (pointer *{cleanBoundName}) Free(){{\n" \
				f"	C.Wrap{cleanBoundName}Free(pointer.h)\n" \
				f"}}\n"
				
				go_bind += f"// IsNil ...\n" \
				f"func (pointer *{cleanBoundName}) IsNil() bool{{\n" \
				f"	return pointer.h == C.Wrap{cleanBoundName}(nil)\n" \
				f"}}\n"

				# runtime.SetFinalizer(funcret, func(ctx *Ret) { C.free(ctx.bufptr) })

			# arithmetic operators
			go_bind += extract_conv_and_bases(conv.arithmetic_ops, \
									lambda arithmetic: self.__extract_method_go(conv.bound_name, conv, arithmetic, bound_name=gen.get_clean_symbol_name(arithmetic['op'])), \
									[base_class.arithmetic_ops for base_class in conv._bases])
			# comparison_ops
			go_bind += extract_conv_and_bases(conv.comparison_ops, \
									lambda comparison: self.__extract_method_go(conv.bound_name, conv, comparison, bound_name=gen.get_clean_symbol_name(comparison['op'])), \
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
			go_bind += f"// {bound_name} ...\n"
			enum_conv = self._get_conv_from_bound_name(bound_name)
			if enum_conv is not None and hasattr(enum_conv, "go_type") and enum_conv.go_type is not None:
				go_bind += f"type {bound_name} {enum_conv.go_type}\n"
			else:
				go_bind += f"type {bound_name} int\n"
			go_bind += "var (\n"
			for id, name in enumerate(enum.keys()):
				go_bind += f"	// {clean_name(name)} ...\n"
				go_bind += f"	{clean_name(name)} =  {bound_name}(C.Get{bound_name}({id}))\n"
			go_bind += ")\n"

		# functions
		for func in self._bound_functions:
			go_bind += self.__extract_method_go("", None, func, is_global=True)

		# global variables
		# sort by group if needed
		bound_variables_groups = {}
		for var in self._bound_variables:
			if "group" in var and var["group"] is not None:
				group_name = clean_name_with_title(var["group"])
				if group_name not in bound_variables_groups:
					bound_variables_groups[group_name] = []
				bound_variables_groups[group_name].append(var)

		# add bound variables groups
		for group_name, var_group in bound_variables_groups.items():
			go_bind += f"// {group_name} ...\n"
			var_conv = self.select_ctype_conv(var_group[0]["ctype"])
			if var_conv is not None and hasattr(var_conv, "go_type") and var_conv.go_type is not None:
				go_bind += f"type {group_name} {var_conv.go_type}\n"
			else:
				go_bind += f"type {group_name} int\n"

			for id, var in enumerate(var_group):
				go_bind += self.__extract_get_set_member_go("", var, is_global=True, implicit_cast=group_name)

		# add bound variables without group
		for var in self._bound_variables:
			if "group" not in var or var["group"] is None:
				go_bind += self.__extract_get_set_member_go("", var, is_global=True)

		self.go_bind = go_bind

		# Create Translate file c++ to go name
		go_translate_file = {}

		def bind_method_translate(classname, convClass, method, static=False, name=None, bound_name=None, is_global=False, is_constructor=False):
			if bound_name is None:
				bound_name = method["bound_name"]
			if name is None:
				name = bound_name

			name_go = name
			if is_constructor:
				name_go = "new_" + name_go

			protos = self._build_protos(method["protos"])
			return_protos_name = []
			for id_proto, proto in enumerate(protos):
				method_name_go = f"{clean_name_with_title(name_go)}"

				# add bounding_name to the overload function
				if "bound_name" in proto["features"]:
					method_name_go += proto["features"]["bound_name"]
				# if automatic suffix generated
				elif "suggested_suffix" in proto:
					method_name_go += proto["suggested_suffix"]
			
				return_protos_name.append(method_name_go)
			return name, return_protos_name

		for conv in self._bound_types:
			if conv.nobind:
				continue

			go_translate_file[conv.bound_name] = {"name": clean_name_with_title(conv.bound_name)}

			# members
			members = {}
			for member in conv.static_members + conv.members:
				bound_name = None
				if "bound_name" in member:
					bound_name = str(member["bound_name"])
				elif bound_name is None:
					bound_name = str(member["name"])

				name = bound_name.replace(":", "")
				name = clean_name_with_title(name)
				members[bound_name] = [f"Get{name}", f"Set{name}"]

			if len(members):
				go_translate_file[conv.bound_name]["members"] = members
				
			# functions
			functions = {}

			# constructors
			if conv.constructor:
				name, protos_name = bind_method_translate(conv.bound_name, conv, conv.constructor, bound_name=f"{conv.bound_name}", is_global=True, is_constructor=True)
				functions[name] = protos_name

			for method in conv.static_methods + conv.methods:
				name, protos_name = bind_method_translate(conv.bound_name, conv, method)
				functions[name] = protos_name
				
			for arithmetic in conv.arithmetic_ops:
				name, protos_name = bind_method_translate(conv.bound_name, conv, arithmetic, bound_name=gen.get_clean_symbol_name(arithmetic['op']))
				functions[name] = protos_name
			for comparison in conv.comparison_ops:
				name, protos_name = bind_method_translate(conv.bound_name, conv, comparison, bound_name=gen.get_clean_symbol_name(comparison['op']))
				functions[name] = protos_name
				
			if len(functions):
				go_translate_file[conv.bound_name]["functions"] = functions

		# enum
		for bound_name, enum in self._enums.items():
			go_translate_file[bound_name] = bound_name
			go_bind += "var (\n"
			for id, name in enumerate(enum.keys()):
				go_translate_file[name] = clean_name(name)
		
		# functions
		for func in self._bound_functions:
			name, protos_name = bind_method_translate("", None, func, is_global=True)
			go_translate_file[name] = protos_name

		# global variables
		for member in self._bound_variables:
			bound_name = None
			if "bound_name" in member:
				bound_name = str(member["bound_name"])
			elif bound_name is None:
				bound_name = str(member["name"])

			name = bound_name.replace(":", "")
			name = clean_name_with_title(name)
			go_translate_file[bound_name] = [f"Get{name}", f"Set{name}"]

		self.go_translate_file = json.dumps(go_translate_file, indent=4, sort_keys=True)