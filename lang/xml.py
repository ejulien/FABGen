# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

import os
import sys
import time
import importlib

import argparse

import gen


class DummyTypeConverter(gen.TypeConverter):
	def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
		super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, needs_c_storage_class)

	def get_type_api(self, module_name):
		return ''

	def to_c_call(self, in_var, out_var_p):
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

	def to_c_call(self, in_var, out_var_p):
		return ''

	def from_c_call(self, out_var, expr, ownership):
		return ''

	def check_call(self, in_var):
		return ''

	def get_type_glue(self, gen, module_name):
		return ''


class XMLGenerator(gen.FABGen):
	default_ptr_converter = DummyTypeConverter
	default_class_converter = DummyTypeConverter
	default_extern_converter = DummyExternTypeConverter

	def __init__(self):
		super().__init__()
		self.check_self_type_in_ops = True
		self.xml = ''

	def get_language(self):
		return "API"

	def output_includes(self):
		pass

	def start(self, module_name):
		super().start(module_name)

		# std
		self.bind_type(DummyTypeConverter('bool')).nobind = True
		self.bind_type(DummyTypeConverter('char')).nobind = True
		self.bind_type(DummyTypeConverter('short')).nobind = True
		self.bind_type(DummyTypeConverter('int')).nobind = True
		self.bind_type(DummyTypeConverter('long')).nobind = True
		self.bind_type(DummyTypeConverter('int8_t', bound_name='Int8')).nobind = True
		self.bind_type(DummyTypeConverter('int16_t', bound_name='Int16')).nobind = True
		self.bind_type(DummyTypeConverter('int32_t', bound_name='Int32')).nobind = True
		self.bind_type(DummyTypeConverter('int64_t', bound_name='Int64')).nobind = True
		self.bind_type(DummyTypeConverter('char16_t', bound_name='Char16')).nobind = True
		self.bind_type(DummyTypeConverter('char32_t', bound_name='Char32')).nobind = True
		self.bind_type(DummyTypeConverter('unsigned char', bound_name='UInt8')).nobind = True
		self.bind_type(DummyTypeConverter('unsigned short', bound_name='UInt16')).nobind = True
		self.bind_type(DummyTypeConverter('unsigned int', bound_name='UInt32')).nobind = True
		self.bind_type(DummyTypeConverter('unsigned long', bound_name="UInt64")).nobind = True
		self.bind_type(DummyTypeConverter('uint8_t', bound_name='UInt8')).nobind = True
		self.bind_type(DummyTypeConverter('uint16_t', bound_name='UInt16')).nobind = True
		self.bind_type(DummyTypeConverter('uint32_t', bound_name='UInt32')).nobind = True
		self.bind_type(DummyTypeConverter('uint64_t', bound_name='UInt64')).nobind = True
		self.bind_type(DummyTypeConverter('intptr_t', bound_name='IntPtr')).nobind = True
		self.bind_type(DummyTypeConverter('size_t')).nobind = True
		self.bind_type(DummyTypeConverter('float')).nobind = True
		self.bind_type(DummyTypeConverter('double')).nobind = True
		self.bind_type(DummyTypeConverter('const char *', bound_name="string")).nobind = True
		self.bind_type(DummyTypeConverter('std::string')).nobind = True

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
	def get_output(self):
		return {'api.xml': self.xml}

	def __extract_method(self, classname, method, static=False, name=None, bound_name=None, is_global=False):
		xml = ""

		if bound_name is None:
			bound_name = method['bound_name']
		if name is None:
			name = bound_name

		uid = classname + '_' + bound_name if classname else bound_name

		protos = self._build_protos(method['protos'])
		for proto in protos:
			retval = 'void'

			if proto['rval']['conv']:
				retval = proto['rval']['conv'].bound_name

			xml += '<function name="%s" returns="%s" uid="%s"' % (name, retval, uid)

			if 'rval_constants_group' in proto['features']:
				xml += ' returns_constants_group="%s"' % proto['features']['rval_constants_group']

			if is_global:
				xml += ' global="1"'
			if static:
				xml += ' static="1"'

			if len(proto['args']):
				xml += '>\n'

				constants_group = proto['features']['constants_group'] if 'constants_group' in proto['features'] else {}

				for argin in proto['argsin']:
					arg_name = str(argin['carg'].name)
					arg_type_bound_name = argin['conv'].bound_name

					xml += '<parm name="%s" type="%s"' % (arg_name, arg_type_bound_name)
					if arg_name in constants_group:
						xml += ' constants_group="%s"' % constants_group[arg_name]
					xml += '/>\n'

				if 'arg_out' in proto['features']:
					for i, arg in enumerate(proto['args']):
						if str(arg['carg'].name) in proto['features']['arg_out']:
							xml += '<parm name="OUTPUT%d" type="%s"/>\n' % (i, arg['conv'].bound_name)

				if 'arg_in_out' in proto['features']:
					for i, arg in enumerate(proto['args']):
						if str(arg['carg'].name) in proto['features']['arg_in_out']:
							xml += '<parm name="OUTPUT%d" type="%s"/>\n' % (i, arg['conv'].bound_name)

				xml += '</function>\n'
			else:
				xml += '/>\n'

		return xml

	def finalize(self):
		super().finalize()
		
		xml = '<?xml version="1.0" ?>\n<api>\n'
		for conv in self._bound_types:
			if conv.nobind:
				continue
			
			xml += '<class name="%s" uid="%s">\n' % (conv.bound_name, conv.bound_name)
			if conv.methods or conv.members:
				# base
				for base in conv._bases:
					xml += '<inherits uid="%s"/>\n' % base.bound_name
				# static members
				for member in conv.static_members:
					xml += '<variable name="%s" static="1" type="%s"/>\n' % (member['name'], self.select_ctype_conv(member['ctype']).bound_name)
				# members
				for member in conv.members:
					xml += '<variable name="%s" type="%s"/>\n' % (member['name'], self.select_ctype_conv(member['ctype']).bound_name)
				# constructors
				if conv.constructor:
					xml += self.__extract_method(conv.bound_name, conv.constructor, bound_name="Constructor")
				# arithmetic operators
				for arithmetic in conv.arithmetic_ops:
					bound_name = 'operator_' + gen.get_clean_symbol_name(arithmetic['op'])
					xml += self.__extract_method(conv.bound_name, arithmetic, name='operator'+arithmetic['op'], bound_name=bound_name)
				# comparison_ops
				for comparison in conv.comparison_ops:
					bound_name = 'operator_' + gen.get_clean_symbol_name(comparison['op'])
					xml += self.__extract_method(conv.bound_name, comparison, name='operator'+comparison['op'], bound_name=bound_name)
				# static methods
				for method in conv.static_methods:
					xml += self.__extract_method(conv.bound_name, method, static=True)
				# methods
				for method in conv.methods:
					xml += self.__extract_method(conv.bound_name, method)
			xml += '</class>\n'

		# enum
		for bound_name, enum in self._enums.items():
			xml += '<enum global="1" name="%s" uid="%s">\n' % (bound_name, bound_name)
			for name in enum.keys():
				xml += '<entry name="%s"/>\n' % name
			xml += '</enum>\n'

		# constants (per group)
		constants_groups = {}

		for var in self._bound_variables:
			group = var['group']
			if group is not None:
				if group not in constants_groups:
					constants_groups[group] = [var]
				else:
					constants_groups[group].append(var)

		for group, constants in constants_groups.items():
			xml += '<constants global="1" name="%s" uid="%s">\n' % (group, group)
			for constant in constants:
				xml += '<entry name="%s"/>\n' % constant['bound_name']
			xml += '</constants>\n'

		# functions
		for func in self._bound_functions:
			xml += self.__extract_method('', func, is_global=True)

		xml += '</api>\n'
		self.xml = xml
