# Harfang - The Fabulous binding Generator for CPython and Go
#	Copyright (C) 2020 Thomas Simonnet

import os
import sys
import time
import importlib

import argparse

import gen


def clean_name(name):
	return str(name).strip().replace('_', '')


def clean_name_with_title(name):
	return str(name).title().strip().replace('_', '')


class GoTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):		
		super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)
		self.go_type = None

	def get_type_api(self, module_name):
		out = '// type API for %s\n' % self.ctype
		if self.c_storage_class:
			out += 'struct %s;\n' % self.c_storage_class
		if self.c_storage_class:
			out += 'void %s(int idx, void *obj, %s &storage);\n' % (self.to_c_func, self.c_storage_class)
		else:
			out += 'void %s(int idx, void *obj);\n' % self.to_c_func
		out += 'int %s(void *obj, OwnershipPolicy);\n' % self.from_c_func
		out += '\n'
		return out

	def to_c_call(self, in_var, out_var_p, is_pointer):
		out = ''
		if self.c_storage_class:
			c_storage_var = 'storage_%s' % out_var_p.replace('&', '_')
			out += '%s %s;\n' % (self.c_storage_class, c_storage_var)
			out += '%s(%s, (void *)%s, %s);\n' % (self.to_c_func, in_var, out_var_p, c_storage_var)
		else:
			out += '%s(%s, %s);\n' % (self.to_c_func, in_var, out_var_p)
		return out

	def from_c_call(self, out_var, expr, ownership):
		return "%s((void *)%s, %s);\n" % (self.from_c_func, expr, ownership)




class DummyTypeConverter(gen.TypeConverter):
	def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
		super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)

	def get_type_api(self, module_name):
		return ''

	def to_c_call(self, in_var, out_var_p, is_pointer):
		return ''

	def from_c_call(self, out_var, expr, ownership):
		return ''

	def check_call(self, in_var):
		return ''

	def get_type_glue(self, gen, module_name):
		return ''


class DummyExternTypeConverter(gen.TypeConverter):
	def __init__(self, type, to_c_storage_type=None, bound_name=None, module=None):
		super().__init__(type, to_c_storage_type, bound_name, None, None)

		self.module = module  # store module

	def get_type_api(self, module_name):
		return ''

	def to_c_call(self, in_var, out_var_p, is_pointer):
		return ''

	def from_c_call(self, out_var, expr, ownership):
		return ''

	def check_call(self, in_var):
		return ''

	def get_type_glue(self, gen, module_name):
		return ''
		
class GoClassTypeDefaultConverter(GoTypeConverterCommon):
	def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
		super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)

	def is_type_class(self):
		return True

	def get_type_api(self, module_name):
		return ''

	def to_c_call(self, in_var, out_var_p, is_pointer):	
		out = f"{out_var_p.replace('&', '_')} := {in_var}.h\n"
		return out

	def from_c_call(self, out_var, expr, ownership):
		return ''

	def check_call(self, in_var):
		return ''

	def get_type_glue(self, gen, module_name):
		return ''



class GoGenerator(gen.FABGen):
	default_ptr_converter = DummyTypeConverter
	default_class_converter = GoClassTypeDefaultConverter
	default_extern_converter = DummyExternTypeConverter

	def __init__(self):
		super().__init__()
		self.check_self_type_in_ops = True
		self.go = ''

	def get_language(self):
		return "Go"

	def output_includes(self):
		pass

	def start(self, module_name):
		super().start(module_name)

		# std
		self.bind_type(DummyTypeConverter('char')).nobind = True
		self.bind_type(DummyTypeConverter('short')).nobind = True
		self.bind_type(DummyTypeConverter('long')).nobind = True
		self.bind_type(DummyTypeConverter('char16_t')).nobind = True
		self.bind_type(DummyTypeConverter('unsigned char')).nobind = True
		self.bind_type(DummyTypeConverter('unsigned short')).nobind = True
		self.bind_type(DummyTypeConverter('unsigned long')).nobind = True
		self.bind_type(DummyTypeConverter('uint8_t')).nobind = True
		self.bind_type(DummyTypeConverter('uint16_t')).nobind = True
		self.bind_type(DummyTypeConverter('uint64_t')).nobind = True
		self.bind_type(DummyTypeConverter('intptr_t')).nobind = True
		self.bind_type(DummyTypeConverter('double', bound_name='float64')).nobind = True
	#	self.bind_type(DummyTypeConverter('std::string')).nobind = True
		
		self._source += self.get_binding_api_declaration()
		# self._header += '#include "fabgen.h"\n'
		# self._header += self.get_binding_api_declaration()

	# kill a bunch of functions we don't care about
	def set_error(self, type, reason):
		return ''

	def get_self(self, ctx):
		return ''

	def get_var(self, i, ctx):
		return ''

	def open_proxy(self, name, max_arg_count, ctx):
		return ''

	def _proto_call(self, self_conv, proto, expr_eval, ctx, fixed_arg_count=None):
		return ''

	def _bind_proxy(self, name, self_conv, protos, desc, expr_eval, ctx, fixed_arg_count=None):
		return ''

	def close_proxy(self, ctx):
		return ''

	def proxy_call_error(self, msg, ctx):
		return ''

	def return_void_from_c(self):
		return ''

	def rval_from_nullptr(self, out_var):
		return ''

	def rval_from_c_ptr(self, conv, out_var, expr, ownership):
		return ''

	def commit_from_c_vars(self, rvals, ctx='default'):
		return ''

	def rbind_function(self, name, rval, args, internal=False):
		return ''

	#
	def get_binding_api_declaration(self):
		type_info_name = gen.apply_api_prefix('type_info')

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

		out += '// return a type info from its type tag\n'
		out += '%s *%s(uint32_t type_tag);\n' % (type_info_name, gen.apply_api_prefix('get_bound_type_info'))

		out += '// return a type info from its type name\n'
		out += '%s *%s(const char *type);\n' % (type_info_name, gen.apply_api_prefix('get_c_type_info'))

		out += '// returns the typetag of a userdata object, nullptr if not a Fabgen object\n'
		out += 'uint32_t %s(void* p);\n\n' % gen.apply_api_prefix('get_wrapped_object_type_tag')

		return out

	def output_binding_api(self):
		type_info_name = gen.apply_api_prefix('type_info')
		
		# self._source += '// Note: Types using a storage class for conversion are not listed here.\n'
		# self._source += 'static std::map<uint32_t, %s> __type_tag_infos;\n\n' % type_info_name

		# self._source += 'static void __initialize_type_tag_infos() {\n'
		# for type in self._bound_types:
		# 	if not type.c_storage_class:
		# 		self._source += '	__type_tag_infos[%s] = {%s, "%s", "%s", %s, %s, %s};\n' % (type.type_tag, type.type_tag, str(type.ctype), type.bound_name, type.check_func, type.to_c_func, type.from_c_func)
		# self._source += '};\n\n'

		self._source += '''\
%s *%s(uint32_t type_tag) {
	return nullptr;
	//auto i = __type_tag_infos.find(type_tag);
	//return i == __type_tag_infos.end() ? nullptr : &i->second;
}\n\n''' % (type_info_name, gen.apply_api_prefix('get_bound_type_info'))

		# self._source += 'static std::map<std::string, %s> __type_infos;\n\n' % type_info_name

		# self._source += 'static void __initialize_type_infos() {\n'
		# for type in self._bound_types:
		# 	if not type.c_storage_class:
		# 		self._source += '	__type_infos["%s"] = {%s, "%s", "%s", %s, %s, %s};\n' % (str(type.ctype), type.type_tag, str(type.ctype), type.bound_name, type.check_func, type.to_c_func, type.from_c_func)
		# self._source += '};\n\n'


		self._source += '''
%s *%s(const char *type) {
	return nullptr;
	//auto i = __type_infos.find(type);
	//return i == __type_infos.end() ? nullptr : &i->second;
}\n\n''' % (type_info_name, gen.apply_api_prefix('get_c_type_info'))

		self._source += '''\
uint32_t %s(void* p) {
	return 0;
	//auto o = cast_to_wrapped_Object_safe(L, idx);
	//return o ? o->type_tag : 0;
}\n\n''' % gen.apply_api_prefix('get_wrapped_object_type_tag')

	#
	def get_output(self):
		return {'wrapper.cpp': self.go_c, 'wrapper.h': self.go_h, "bind.go": self.go_bind}

	def _get_type(self, name):
		for type in self._bound_types:
			if type:
				return type
		return None
		
	def __extract_get_set_member_go(self, classname, member, static=False, name=None, bound_name=None, is_global=False):
		go = ""
		conv = self.select_ctype_conv(member['ctype'])

		if name is None:
			name = str(member["name"])
		
		arg_bound_name = conv.bound_name
		if arg_bound_name.endswith('_nobind') and conv.nobind:
			arg_bound_name = arg_bound_name[:-len('_nobind')]
		if (conv.ctype.is_pointer() or (hasattr(conv.ctype, 'ref') and conv.ctype.ref == "&")) and conv.bound_name != "string":
			arg_bound_name = "*" + arg_bound_name

		# GET
		go += f"// Get{name} ...\n" \
				f"func (a *{classname}) Get{name}() {arg_bound_name} {{\n" 
		go += f"v := C.Wrap{classname}Get{name}(a.h)\n"
		
		# check if need convert from c
		retval_go = "v"
		if (not conv.ctype.is_pointer() and not (hasattr(conv.ctype, 'ref') and conv.ctype.ref == "&")) or \
			conv.bound_name == "string":
			conversion_ret = conv.from_c_call("v", "", "") 
			if conversion_ret != "":
				retval_go = conversion_ret

		go += f"return {retval_go}\n"

		go += "}\n"

		# SET
		go += f"// Set{name} ...\n" \
				f"func (a *{classname}) Set{name}(v {arg_bound_name}) {{\n" 
		# convert to c		
		c_call = conv.to_c_call(name, f"vToC", conv.ctype.is_pointer() or (hasattr(conv.ctype, 'ref') and conv.ctype.ref == "&"))
		if c_call != "":
			go += c_call
		else:
			go += "vToC = v"

		go += f"	C.Wrap{classname}Set{name}(a.h, vToC)\n"
		go += "}\n"

		return go
			
	def __extract_get_set_member(self, classname, member, static=False, name=None, bound_name=None, is_global=False, is_in_header=False):
		go = ""
		conv = self.select_ctype_conv(member['ctype'])

		if name is None:
			name = str(member["name"])
		
		arg_bound_name = conv.bound_name
		if arg_bound_name.endswith('_nobind') and conv.nobind:
			arg_bound_name = arg_bound_name[:-len('_nobind')]
		if (conv.ctype.is_pointer() or (hasattr(conv.ctype, 'ref') and conv.ctype.ref == "&")) and conv.bound_name != "string":
			arg_bound_name = "*" + arg_bound_name

		# GET
		go += f"{arg_bound_name} Wrap{classname}Get{name}(Wrap{classname} h)"

		if is_in_header:
			go += ";\n"
		else:
			go += f"{{ return (({classname}*)h)->{name};}}\n"

		# SET
		go += f"void Wrap{classname}Set{name}(Wrap{classname} h, {arg_bound_name} v)"

		if is_in_header:
			go += ";\n"
		else:
			go += f"{{ (({classname}*)h)->{name} = v;}}\n"
		return go
			
	def __extract_method_go(self, classname, method, static=False, name=None, bound_name=None, is_global=False):
		go = ""

		if bound_name is None:
			bound_name = method['bound_name']
		if name is None:
			name = bound_name

		if bound_name == 'OpenVRStateToViewState':
			bound_name = bound_name

		uid = classname + bound_name if classname else bound_name

		protos = self._build_protos(method['protos'])
		for id_proto, proto in enumerate(protos):
			retval = ''

			if proto['rval']['conv']:
				retval = proto['rval']['conv'].bound_name

			go += '// ' + clean_name_with_title(name) + ' ...\n'

			go += "func "
			if not is_global:
				go += f"(a *{classname}) "
			go += f"{clean_name_with_title(name)}"

			# add number in case of multiple proto, in go, you can't have overload or default parameter
			if len(protos) > 1:
				go += f"{id_proto}"

			# add input(s) declaration
			go += '('
			if len(proto['args']):
				has_previous_arg = False
				for argin in proto['argsin']:
					arg_bound_name = argin['conv'].bound_name
					if arg_bound_name.endswith('_nobind') and argin['conv'].nobind:
						arg_bound_name = arg_bound_name[:-len('_nobind')]
					if (argin['carg'].ctype.is_pointer() or (hasattr(argin['carg'].ctype, 'ref') and argin['carg'].ctype.ref == "&")) and argin['conv'].bound_name != "string":
						arg_bound_name = "*" + arg_bound_name

					if has_previous_arg:
						go += ' ,'
					go += '%s %s' % (clean_name(argin['carg'].name), arg_bound_name)
					has_previous_arg = True

			go += ')'

			# add output(s) declaration	
			go += '('
			has_previous_ret_arg = False
			if proto['rval']['conv']:
				arg_bound_name = proto['rval']['conv'].bound_name
				if arg_bound_name.endswith('_nobind') and proto['rval']['conv'].nobind:
					arg_bound_name = arg_bound_name[:-len('_nobind')]
				if (proto['rval']['storage_ctype'].is_pointer() or (hasattr(proto['rval']['storage_ctype'], 'ref') and proto['rval']['storage_ctype'].ref == "&")) and proto['rval']['conv'].bound_name != "string":
					arg_bound_name = "*" + arg_bound_name
				go += arg_bound_name
				has_previous_ret_arg = True
			
			if len(proto['args']):
				for arg in proto['args']:
					if ('arg_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_out']) or \
						('arg_in_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_in_out']):
						if has_previous_ret_arg:
							go += ' ,'

						arg_bound_name = arg['conv'].bound_name
						if arg_bound_name.endswith('_nobind') and arg['conv'].nobind:
							arg_bound_name = arg_bound_name[:-len('_nobind')]
						if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and arg['conv'].bound_name != "string":
							arg_bound_name = "*" + arg_bound_name

						go += arg_bound_name
						has_previous_ret_arg = True
			go += ')'

			# begin function declaration
			go += '{\n'

			# convert arg in to c
			if len(proto['args']):
				for arg in proto['args']:
					# if arg out only, declare this value
					if 'arg_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_out']:
						arg_bound_name = arg['conv'].bound_name
						if arg_bound_name.endswith('_nobind') and arg['conv'].nobind:
							arg_bound_name = arg_bound_name[:-len('_nobind')]
						if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and arg['conv'].bound_name != "string":
							arg_bound_name = f"new({arg_bound_name})"
						go += f"{clean_name(arg['carg'].name)} := {arg_bound_name}\n"

					c_call = ""
					if arg['conv']:
						c_call = arg['conv'].to_c_call(clean_name(arg['carg'].name), f"{clean_name(arg['carg'].name)}ToC", arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&"))
					if c_call != "":
						go += c_call
					else:
						go += f"{clean_name(arg['carg'].name)}ToC := {clean_name(arg['carg'].name)}\n"
				
			# declare arg out
			if retval != '':
				go += "retval := "
			go += "C.Wrap%s" % clean_name_with_title(name)

			# add number in case of multiple proto, in go, you can't have overload or default parameter
			if len(protos) > 1:
				go += f"{id_proto}"
			
			go += '('
			if not is_global:
				go += '(a.h, '
				
			if len(proto['args']):
				has_previous_arg = False
				for arg in proto['args']:
					if has_previous_arg:
						go += ' ,'
					# if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and \
					# 	arg['conv'].bound_name != "string" and not arg['conv'].is_type_class():
					# 	go += "&"
					go += f"{clean_name(arg['carg'].name)}ToC"
						
					has_previous_arg = True
			go += ')\n'
			if retval != '':
				# check if need convert from c
				retval_go = "retval"
				if (not proto['rval']['storage_ctype'].is_pointer() and \
					not (hasattr(proto['rval']['storage_ctype'], 'ref') and proto['rval']['storage_ctype'].ref == "&")) or \
					proto['rval']['conv'].bound_name == "string":
					conversion_ret = proto['rval']['conv'].from_c_call("retval", "", "") 
					if conversion_ret != "":
						retval_go = conversion_ret
				
				if (proto['rval']['storage_ctype'].is_pointer() or \
					(hasattr(proto['rval']['storage_ctype'], 'ref') and proto['rval']['storage_ctype'].ref == "&")) and \
					proto['rval']['conv'].bound_name != "string":
					retval_go = f"(*{proto['rval']['conv'].bound_name})(unsafe.Pointer({retval_go}))\n"

				go += f"return {retval_go}"
			
			# return arg out
			if 'arg_out' in proto['features'] or 'arg_in_out' in proto['features']:
				if retval == '':
					go += "return "
				has_previous_arg = False
					
				for arg in proto['args']:
					if ('arg_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_out']) or \
						('arg_in_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_in_out']):
						if retval != '' or has_previous_arg:
							go += ", "
						has_previous_arg = True
							
						# add name
						retval_go = clean_name(str(arg['carg'].name))+"ToC"

						if arg['conv'].is_type_class():
							retval_go = clean_name(str(arg['carg'].name))
							
						# check if need convert from c
						if (not arg['carg'].ctype.is_pointer() and \
							not (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) or \
							arg['conv'].bound_name == "string":
							conversion_ret = arg['conv'].from_c_call("retval", "", "") 
							if conversion_ret != "":
								retval_go = conversion_ret

						if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and \
							arg['conv'].bound_name != "string" and not arg['conv'].is_type_class():
							retval_go = f"(*{arg['conv'].bound_name})(unsafe.Pointer({retval_go}))"

						go += retval_go

			go += '\n}\n'

		return go


	def __extract_method(self, classname, method, static=False, name=None, bound_name=None, is_global=False, is_in_header=False):
		go = ""

		if bound_name is None:
			bound_name = method['bound_name']
		if name is None:
			name = bound_name

		if bound_name == 'OpenVRStateToViewState':
			bound_name = bound_name

		uid = classname + bound_name if classname else bound_name

		protos = self._build_protos(method['protos'])
		for id_proto, proto in enumerate(protos):
			retval = 'void'

			if proto['rval']['storage_ctype']:
				# transform & to *
				if hasattr(proto['rval']['storage_ctype'], 'ref') and proto['rval']['storage_ctype'].ref == "&":
					retval = proto['rval']['conv'].bound_name + " *"
				else: 
					retval =  proto['rval']['storage_ctype']

			if is_in_header:
				go += 'extern '
			go += '%s Wrap%s' % (retval, clean_name_with_title(name))

			# add number in case of multiple proto, in go, you can't have overload or default parameter
			if len(protos) > 1:
				go += f"{id_proto}"

			go += '('
			if len(proto['args']):
				has_previous_arg = False
				for argin in proto['args']:
					if has_previous_arg:
						go += ' ,'
					if argin['conv'].is_type_class():
						go += "Wrap"
					go += '%s ' % argin['conv'].ctype
					if not argin['conv'].is_type_class() and (argin['carg'].ctype.is_pointer() or (hasattr(argin['carg'].ctype, 'ref') and argin['carg'].ctype.ref == "&")):
						go += "*"
					go += ' %s' %  argin['carg'].name
					has_previous_arg = True

			go += ')'

			if is_in_header:
				go += ';\n'
			else:
				go += '{'
				if retval != 'void':
					go += 'return '
					
				# transform & to *
				if hasattr(proto['rval']['storage_ctype'], 'ref') and proto['rval']['storage_ctype'].ref == "&":
					go += "&"
				go += "%s" % name
				
				go += '('
				if len(proto['args']):
					has_previous_arg = False
					for argin in proto['args']:
						if has_previous_arg:
							go += ' ,'
						if argin["conv"].is_type_class():
							go += f"({argin['conv'].ctype}*)"
						
						elif hasattr(argin['carg'].ctype, 'ref') and argin['carg'].ctype.ref == "&":
							go += "*"
						go += '%s' % argin['carg'].name
						has_previous_arg = True

				go += ');'
				go += '}\n'

		return go

	def finalize(self):
		super().finalize()

		self.output_binding_api()

		# .h
		go_h = '#pragma once\n' \
				'#ifdef __cplusplus\n'\
				'extern "C" {\n'\
				'#endif\n'

		go_h += '#include <stdint.h>\n' \
			'#include <stdbool.h>\n' \
			'#include <stddef.h>\n' \
			'#include <memory.h>\n' \
			'#include <stdlib.h>\n' \
			'#include "fabgen.h"\n\n'
			
		go_h += 'typedef int WrapBool;\n'

		for conv in self._bound_types:
			if conv.nobind:
				continue

			go_h += f"typedef void* Wrap{conv.bound_name};\n" \
					f"Wrap{conv.bound_name} Wrap{conv.bound_name}Init();\n" \
					f"void Wrap{conv.bound_name}Free(Wrap{conv.bound_name});\n"

			if conv.methods or conv.members:
				# base	inheritance is done in go file with interface
				# for base in conv._bases:
				# 	go_h += '<inherits uid="%s"/>\n' % base.bound_name
				# static members
				for member in conv.static_members:
					go_h += self.__extract_get_set_member(conv.bound_name, member, static=True, is_in_header=True)
				# members
				for member in conv.members:
					go_h += self.__extract_get_set_member(conv.bound_name, member, is_in_header=True)
				# constructors
				# if conv.constructor:
				# 	go_h += self.__extract_method(conv.bound_name, conv.constructor, bound_name="Constructor")
				# arithmetic operators
				for arithmetic in conv.arithmetic_ops:
					bound_name = 'operator_' + gen.get_clean_symbol_name(arithmetic['op'])
					go_h += self.__extract_method(conv.bound_name, arithmetic, name='operator'+arithmetic['op'], bound_name=bound_name)
				# comparison_ops
				for comparison in conv.comparison_ops:
					bound_name = 'operator_' + gen.get_clean_symbol_name(comparison['op'])
					go_h += self.__extract_method(conv.bound_name, comparison, name='operator'+comparison['op'], bound_name=bound_name)
				# static methods
				for method in conv.static_methods:
					go_h += self.__extract_method(conv.bound_name, method, static=True)
				# methods
				for method in conv.methods:
					go_h += self.__extract_method(conv.bound_name, method)
			#go_h += f"}} Wrap{conv.bound_name};\n"
			
		# enum
		for bound_name, enum in self._enums.items():
			go_h += f"extern int Get{bound_name}(const int id);\n"

		# functions
		for func in self._bound_functions:
			go_h += self.__extract_method('', func, is_global=True, is_in_header=True)

		go_h += '#ifdef __cplusplus\n' \
				'}\n' \
				'#endif\n'
		self.go_h = go_h


		# cpp
		go_c = '// go wrapper c\n' \
				'#include \"wrapper.h\"\n'
		go_c += self._source

		for conv in self._bound_types:
			if conv.nobind:
				continue

			go_c += f"// bind Wrap{conv.bound_name} methods\n" \
				f"Wrap{conv.bound_name} Wrap{conv.bound_name}Init(){{" \
				f"return (void*)(new {conv.bound_name}());" \
				f"}}\n"
			go_c += f"void Wrap{conv.bound_name}Free(Wrap{conv.bound_name} h){{" \
				f"delete ({conv.bound_name}*)h;" \
				f"}}\n" 

			if conv.methods or conv.members:
				# base	inheritance is done in go file with interface
				# for base in conv._bases:
				# 	go_c += '<inherits uid="%s"/>\n' % base.bound_name
				# static members
				for member in conv.static_members:
					go_c += self.__extract_get_set_member(conv.bound_name, member, static=True)
				# members
				for member in conv.members:
					go_c += self.__extract_get_set_member(conv.bound_name, member)
				# # constructors
				# if conv.constructor:
				# 	go_c += self.__extract_method(conv.bound_name, conv.constructor, bound_name="Constructor")
				# arithmetic operators
				for arithmetic in conv.arithmetic_ops:
					bound_name = 'operator_' + gen.get_clean_symbol_name(arithmetic['op'])
					go_c += self.__extract_method(conv.bound_name, arithmetic, name='operator'+arithmetic['op'], bound_name=bound_name)
				# comparison_ops
				for comparison in conv.comparison_ops:
					bound_name = 'operator_' + gen.get_clean_symbol_name(comparison['op'])
					go_c += self.__extract_method(conv.bound_name, comparison, name='operator'+comparison['op'], bound_name=bound_name)
				# static methods
				for method in conv.static_methods:
					go_c += self.__extract_method(conv.bound_name, method, static=True)
				# methods
				for method in conv.methods:
					go_c += self.__extract_method(conv.bound_name, method)

		# enum
		for bound_name, enum in self._enums.items():
			enum_vars = []
			for name, value in enum.items():
				enum_vars.append(f"{value}")
			go_c += f"static const int Wrap{bound_name} [] = {{ {', '.join(enum_vars)} }};\n"
			go_c += f"int Get{bound_name}(const int id) {{ return Wrap{bound_name}[id];}}\n"

		# functions
		for func in self._bound_functions:
			go_c += self.__extract_method('', func, is_global=True)

		self.go_c = go_c

		# .go
		go_bind = 'package harfang\n' \
				'// #include "wrapper.h"\n' \
				'// #cgo CFLAGS: -I .\n' \
				'import "C"\n\n' \
				'import "unsafe"\n'

		with open("lib/go/WrapperConverter.go", "r") as file:
			lines = file.readlines()
			go_bind += ''.join(lines)
			go_bind += "\n"

#// #cgo CFLAGS: -Iyour-include-path
#// #cgo LDFLAGS: -Lyour-library-path -lyour-library-name-minus-the-lib-part

		for conv in self._bound_types:
			if conv.nobind:
				continue
			
			go_bind += f"// {conv.bound_name.title()} ...\n" \
						f"type {conv.bound_name.title()} struct{{\n" \
						f"	h C.Wrap{conv.bound_name.title()}\n" \
						"}\n" \
						f"// New{conv.bound_name.title()} ...\n" \
						f"func New{conv.bound_name.title()}() *{conv.bound_name.title()} {{\n" \
						f"	ret := new({conv.bound_name.title()})\n" \
						f"	ret.h = C.Wrap{conv.bound_name.title()}Init() \n" \
						f"return ret\n" \
						f"}}\n" \
						f"// Free ...\n" \
						f"func (a *{conv.bound_name.title()}) Free(){{\n" \
						f"	C.Wrap{conv.bound_name.title()}Free(a.h)\n" \
						f"}}\n" \

			if conv.methods or conv.members:
			# 	# base
			# 	for base in conv._bases:
			# 		go_bind += "{base.bound_name}\n"
				# static members
				for member in conv.static_members:
					go_bind += self.__extract_get_set_member_go(conv.bound_name, member, static=True)
				# members
				for member in conv.members:
					go_bind += self.__extract_get_set_member_go(conv.bound_name, member, static=False)
			# 	# constructors
			# 	if conv.constructor:
			# 		go_bind += self.__extract_method(conv.bound_name, conv.constructor, bound_name="Constructor")
			# 	# arithmetic operators
			# 	for arithmetic in conv.arithmetic_ops:
			# 		bound_name = 'operator_' + gen.get_clean_symbol_name(arithmetic['op'])
			# 		go_bind += self.__extract_method(conv.bound_name, arithmetic, name='operator'+arithmetic['op'], bound_name=bound_name)
			# 	# comparison_ops
			# 	for comparison in conv.comparison_ops:
			# 		bound_name = 'operator_' + gen.get_clean_symbol_name(comparison['op'])
			# 		go_bind += self.__extract_method(conv.bound_name, comparison, name='operator'+comparison['op'], bound_name=bound_name)
			# 	# static methods
			# 	for method in conv.static_methods:
			# 		go_bind += self.__extract_method(conv.bound_name, method, static=True)
			# 	# methods
			# 	for method in conv.methods:
			# 		go_bind += self.__extract_method(conv.bound_name, method)

		# enum
		for bound_name, enum in self._enums.items():
			go_bind += f"type {bound_name} int\n" \
						"var (\n"
			for id, name in enumerate(enum.keys()):
				go_bind += f"	{clean_name(name)} =  {bound_name}(C.Get{bound_name}({id}))\n"
			go_bind +=  ')\n'

		# functions
		for func in self._bound_functions:
			go_bind += self.__extract_method_go('', func, is_global=True)

	
		self.go_bind = go_bind



