# Harfang - The Fabulous binding Generator for CPython and Go
#	Copyright (C) 2020 Thomas Simonnet

import os
import sys
import time
import importlib

import argparse

import gen



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


class GoGenerator(gen.FABGen):
	default_ptr_converter = DummyTypeConverter
	default_class_converter = DummyTypeConverter
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
		self.bind_type(DummyTypeConverter('bool')).nobind = True

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
		for proto in protos:
			retval = ''

			if proto['rval']['conv']:
				retval = proto['rval']['conv'].bound_name

			go += '// ' + (name.title().strip().replace('_', '')) + ' ...\n'
			go += 'func %s' % (name.title().strip().replace('_', ''))

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
					go += '%s %s' % (argin['carg'].name, arg_bound_name)
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
				if 'arg_out' in proto['features']:
					for arg in proto['args']:
						if str(arg['carg'].name) in proto['features']['arg_out']:
							if has_previous_ret_arg:
								go += ' ,'

							arg_bound_name = arg['conv'].bound_name
							if arg_bound_name.endswith('_nobind') and arg['conv'].nobind:
								arg_bound_name = arg_bound_name[:-len('_nobind')]
							# if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and arg['conv'].bound_name != "string":
							# 	arg_bound_name = "*" + arg_bound_name

							go += arg_bound_name
							has_previous_ret_arg = True
			go += ')'

			# begin function declaration
			go += '{\n'

			# convert arg in to c
			if len(proto['args']):
				for argin in proto['argsin']:
					c_call = ""
					if argin['conv']:
						c_call = argin['conv'].to_c_call(argin['carg'].name, f"{argin['carg'].name}ToC", argin['carg'].ctype.is_pointer() or (hasattr(argin['carg'].ctype, 'ref') and argin['carg'].ctype.ref == "&"))
					if c_call != "":
						go += c_call
					else:
						# if the value is not arg in out
						if proto["features"] and "arg_in_out" in proto["features"] and str(argin['carg'].name) not in proto["features"]["arg_in_out"]:
							go += f"{argin['carg'].name}_out := {argin['carg'].name}\n"
				
			# declare arg out
			if 'arg_out' in proto['features']:
				i = 0
				for arg in proto['args']:
					if str(arg['carg'].name) in proto['features']['arg_out']:
						arg_bound_name = arg['conv'].bound_name
						if arg_bound_name.endswith('_nobind') and arg['conv'].nobind:
							arg_bound_name = arg_bound_name[:-len('_nobind')]

						if arg['conv'].go_type is not None:
							arg_bound_name = arg['conv'].go_type

						go += f"var OUTPUT{i} {arg_bound_name}\n"
						i += 1

			# begin call binding function
			if retval != '':
				go += "retval := "
			go += "C.HG%s" % name.title().strip().replace('_', '')
			
			go += '('
			if len(proto['args']):
				has_previous_arg = False
				i = 0
				for arg in proto['args']:
					if has_previous_arg:
						go += ' ,'
						
					if 'arg_out' in proto['features'] and str(arg['carg'].name) in proto['features']['arg_out']:
						if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and arg['conv'].bound_name != "string":
							go += "&"
						go += f"OUTPUT{i}"
						i += 1
					else:
						go += f"{arg['carg'].name}ToC"
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
			if 'arg_out' in proto['features']:
				if retval == '':
					go += "return "
				i = 0
				for arg in proto['args']:
					if str(arg['carg'].name) in proto['features']['arg_out']:
						if retval != '' or i > 0:
							go += ", "
							
						# check if need convert from c
						retval_go = f"OUTPUT{i}"
						if (not arg['carg'].ctype.is_pointer() and \
							not (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) or \
							arg['conv'].bound_name == "string":
							conversion_ret = arg['conv'].from_c_call("retval", "", "") 
							if conversion_ret != "":
								retval_go = conversion_ret


						#if (arg['carg'].ctype.is_pointer() or (hasattr(arg['carg'].ctype, 'ref') and arg['carg'].ctype.ref == "&")) and arg['conv'].bound_name != "string":
						#	retval_go = f"(*{arg['conv'].bound_name})(unsafe.Pointer({retval_go}))"

						go += retval_go
						i += 1

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
		for proto in protos:
			retval = 'void'

			if proto['rval']['storage_ctype']:
				# transform & to *
				if hasattr(proto['rval']['storage_ctype'], 'ref') and proto['rval']['storage_ctype'].ref == "&":
					retval = proto['rval']['conv'].bound_name + " *"
				else: 
					retval =  proto['rval']['storage_ctype']

			if is_in_header:
				go += 'extern '
			go += '%s HG%s' % (retval, name.title().strip().replace('_', ''))

			go += '('
			if len(proto['args']):
				has_previous_arg = False
				for argin in proto['args']:
					if has_previous_arg:
						go += ' ,'
					if len(argin['conv'].members) > 0:
						go += "struct "
					go += '%s ' % argin['conv'].ctype
					if argin['carg'].ctype.is_pointer() or (hasattr(argin['carg'].ctype, 'ref') and argin['carg'].ctype.ref == "&"):
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
						if hasattr(argin['carg'].ctype, 'ref') and argin['carg'].ctype.ref == "&":
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
			'#include "fabgen.h"\n\n'

		for conv in self._bound_types:
			if conv.nobind:
				continue


			go_h += f"struct {conv.bound_name};\n"
			if conv.methods or conv.members:
				# base	inheritance is done in go file with interface
				# for base in conv._bases:
				# 	go_h += '<inherits uid="%s"/>\n' % base.bound_name
				# static members
				# for member in conv.static_members:
				# 	go_h += f"{self.select_ctype_conv(member['ctype']).bound_name} {member['name']};\n"
				# # members
				# for member in conv.members:
				# 	go_h += f"{self.select_ctype_conv(member['ctype']).bound_name} {member['name']};\n"
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
			#go_h += f"}} HG{conv.bound_name};\n"
			
		# enum
		for bound_name, enum in self._enums.items():
			go_h += '<enum global="1" name="%s" uid="%s">\n' % (bound_name, bound_name)
			for name in enum.keys():
				go_h += '<entry name="%s"/>\n' % name
			go_h +=  '</enum>\n'

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

			go_c += f"// bind HG{conv.bound_name} methods\n"
			if conv.methods or conv.members:
				# base	inheritance is done in go file with interface
				# for base in conv._bases:
				# 	go_c += '<inherits uid="%s"/>\n' % base.bound_name
				# static members
				# for member in conv.static_members:
				# 	go_c += f"{self.select_ctype_conv(member['ctype']).bound_name} {member['name']};\n"
				# # members
				# for member in conv.members:
				# 	go_c += f"{self.select_ctype_conv(member['ctype']).bound_name} {member['name']};\n"
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
			go_c += '<enum global="1" name="%s" uid="%s">\n' % (bound_name, bound_name)
			for name in enum.keys():
				go_c += '<entry name="%s"/>\n' % name
			go_c +=  '</enum>\n'

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
#// #cgo CFLAGS: -Iyour-include-path
#// #cgo LDFLAGS: -Lyour-library-path -lyour-library-name-minus-the-lib-part

		for conv in self._bound_types:
			if conv.nobind:
				continue
			
			go_bind += f"type {conv.bound_name.title()} C.struct_{conv.bound_name.title()}\n"
			# if conv.methods or conv.members:
			# 	# base
			# 	for base in conv._bases:
			# 		go_bind += "{base.bound_name}\n"
			# 	# static members
			# 	for member in conv.static_members:
			# 		go_bind += '<variable name="%s" static="1" type="%s"/>\n' % (member['name'], self.select_ctype_conv(member['ctype']).bound_name)
			# 	# members
			# 	for member in conv.members:
			# 		go_bind += '<variable name="%s" type="%s"/>\n' % (member['name'], self.select_ctype_conv(member['ctype']).bound_name)
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
			# go_bind += '}\n'

		# enum
		for bound_name, enum in self._enums.items():
			go_bind += '<enum global="1" name="%s" uid="%s">\n' % (bound_name, bound_name)
			for name in enum.keys():
				go_bind += '<entry name="%s"/>\n' % name
			go_bind +=  '</enum>\n'

		# functions
		for func in self._bound_functions:
			go_bind += self.__extract_method_go('', func, is_global=True)

	
		self.go_bind = go_bind



