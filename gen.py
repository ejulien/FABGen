# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

from pypeg2 import re, flag, name, Plain, optional, attr, K, parse, Keyword, Enum, List, csl, some, maybe_some
from collections import OrderedDict
import zlib
import copy


#
api_prefix = 'gen'

def apply_api_prefix(symbol):
	return '%s_%s' % (api_prefix, symbol) if api_prefix else symbol


def get_fabgen_api():
		return '''\
// FABgen .h

#pragma once

enum OwnershipPolicy { NonOwning, Copy, Owning };
'''


#
def get_fully_qualified_function_signature(func):
	out = ''
	if hasattr(func, 'void_rval'):
		out += 'void'
	else:
		out += str(func.rval)

	if hasattr(func, 'args'):
		args = [str(arg) for arg in func.args]
		out += '(%s)' % ', '.join(args)
	else:
		out += '()'

	return out


def get_fully_qualified_ctype_name(ctype):
	parts = []

	if ctype.const:
		parts.append('const')
	if ctype.signed:
		parts.append('signed')
	if ctype.unsigned:
		parts.append('unsigned')

	if hasattr(ctype, 'template'):
		if hasattr(ctype.template, 'args'):
			parts.append(ctype.name + '<%s>' % ', '.join([str(arg) for arg in ctype.template.args]))
		elif hasattr(ctype.template, 'function'):
			parts.append(ctype.name + '<%s>' % get_fully_qualified_function_signature(ctype.template.function))
	else:
		parts.append(repr(ctype.scoped_typename))

	if ctype.const_ref:
		parts.append('const')
	if hasattr(ctype, 'ref'):
		parts.append(ctype.ref)

	return ' '.join(parts)


def ref_to_string(ref):
	parts = []
	for e in ref:
		if ref == '*':
			parts.append('ptr')
		elif ref == '&':
			parts.append('ref')
	return '_'.join(parts)


def ctype_to_plain_string(ctype):
	parts = []

	if ctype.const:
		parts.append('const')
	if ctype.signed:
		parts.append('signed')
	if ctype.unsigned:
		parts.append('unsigned')

	_ctype = ctype.scoped_typename.parts[-1]  # ignore namespace entries (only consider last type in chain)
	_name = _ctype.name.replace('::', '_').replace(':', '_')

	parts.append(_name)

	if hasattr(_ctype, 'template'):
		if hasattr(_ctype.template, 'function'):
			function = _ctype.template.function

			parts.append('returning')

			if hasattr(function, 'void_rval'):
				parts.append('void')
			else:
				parts.append(ctype_to_plain_string(function.rval))

			if hasattr(function, 'args'):
				parts.append('taking')
				for arg in function.args:
					parts.append(ctype_to_plain_string(arg))
		else:
			parts.append('of_' + '_and_'.join([ctype_to_plain_string(arg) for arg in _ctype.template.args]))

	if ctype.const_ref:
		parts.append('const')
	if hasattr(ctype, 'ref'):
		parts.append(ref_to_string(ctype.ref))

	return '_'.join(parts)


def get_ctype_default_bound_name(ctype):
	ctype = copy.deepcopy(ctype)
	ctype.scoped_typename.explicit_global = False
	return ctype_to_plain_string(ctype)


#
symbol_clean_rules = OrderedDict()

symbol_clean_rules['::'] = '__'  # namespace

symbol_clean_rules['+='] = 'inplace_add'
symbol_clean_rules['*='] = 'inplace_mul'
symbol_clean_rules['/='] = 'inplace_div'
symbol_clean_rules['-='] = 'inplace_sub'

symbol_clean_rules['+'] = 'add'
symbol_clean_rules['*'] = 'mul'
symbol_clean_rules['/'] = 'div'
symbol_clean_rules['-'] = 'sub'

symbol_clean_rules['||'] = 'logicor'
symbol_clean_rules['&&'] = 'logicand'
symbol_clean_rules['|'] = 'pipe'
symbol_clean_rules['&'] = 'and'

symbol_clean_rules['<'] = 'lt'
symbol_clean_rules['<='] = 'le'
symbol_clean_rules['=='] = 'eq'
symbol_clean_rules['!='] = 'ne'
symbol_clean_rules['>'] = 'gt'
symbol_clean_rules['>='] = 'ge'


def strip_namespace(name):
	parts = name.split('::')
	return parts[-1] if len(parts) > 1 else name


def get_clean_symbol_name(name):
	""" Return a string cleaned so that it may be used as a valid symbol name in the generator output."""

	parts = name.split(' ')

	def clean_symbol_name_part(part):
		for f_o, f_d in symbol_clean_rules.items():
			part = part.replace(f_o, f_d)
		return part

	parts = [clean_symbol_name_part(part) for part in parts]
	return '_'.join(parts)


def get_symbol_default_bound_name(name):
	if isinstance(name, str):  # no namespace
		name = strip_namespace(name)
	else:
		name = name.naked_name()

	return get_clean_symbol_name(name)


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

#
typename = re.compile(r"(_|[A-z])[A-z0-9_]*")
ref_re = re.compile(r"[&*]+")


#
class _CType:
	def __repr__(self):
		return get_fully_qualified_ctype_name(self)

	def get_ref(self):
		return (self.ref if hasattr(self, 'ref') else '')

	def add_ref(self, ref):
		t = copy.deepcopy(self)
		if hasattr(self, 'ref'):
			t.ref += ref
		else:
			setattr(t, 'ref', ref)
		return t

	def is_pointer(self):
		return self.get_ref() == '*'

	def is_const(self):
		if self.get_ref() == '':
			return self.const
		return self.const_ref

	def non_const(self):
		t = copy.deepcopy(self)
		t.const = False
		return t

	def dereference_once(self):
		t = copy.deepcopy(self)
		if hasattr(t, 'ref'):
			t.ref = t.ref[:-1]
			if t.ref == '':
				delattr(t, 'ref')
		return t

	def ref_stripped(self):  # pragma: no cover
		t = copy.deepcopy(self)
		if hasattr(t, 'ref'):
			delattr(t, 'ref')
		return t


class _FunctionSignature:
	grammar = [attr("void_rval", "void"), attr("rval", _CType)], "(", optional(attr("args", csl(_CType))), ")"

	def __repr__(self):
		return get_fully_qualified_function_signature(self)


class _TemplateParameters:
	grammar = "<", [attr("function", _FunctionSignature), attr("args", csl(_CType))], ">"

	def __repr__(self):
		if hasattr(self, "function"):
			args = [repr(self.function)]
		else:
			args = [repr(arg) for arg in self.args]

		return '<' + ','.join(args) + '>'


class _Typename:
	grammar = attr("name", typename), optional(attr("template", _TemplateParameters))

	def __repr__(self):
		out = self.name

		if hasattr(self, 'template'):
			out += repr(self.template)

		return out


class _ScopedTypename:
	grammar = flag("explicit_global", K("::")), attr("parts", csl(_Typename, separator="::"))

	def naked_name(self):
		return self.parts[-1].name

	def __eq__(self, other):
		return repr(self) == repr(other)

	def __repr__(self):
		out = ''
		if self.explicit_global:
			out += '::'

		parts = []
		for part in self.parts:
			parts.append(repr(part))

		out += '::'.join(parts)
		return out


_CType.grammar = flag("const"), flag("signed"), flag("unsigned"), attr("scoped_typename", _ScopedTypename), optional(attr("ref", ref_re)), flag("const_ref", K("const"))


#
class _NamedCType:
	grammar = attr("ctype", _CType), attr("name", _ScopedTypename)

	def __repr__(self):  # pragma: no cover
		return ' '.join([repr(self.ctype), self.name.naked_name()])


#
def ctype_ref_to(src_ref, dst_ref):
	i = 0
	while i < len(src_ref) and i < len(dst_ref):
		if src_ref[i] != dst_ref[i]:
			break
		i += 1

	src_ref = src_ref[i:]
	dst_ref = dst_ref[i:]

	if src_ref == '&':
		if dst_ref == '&':
			return ''  # ref to ref
		elif dst_ref == '*':
			return '&'  # ref to ptr
		else:
			return ''  # ref to value
	elif src_ref == '*':
		if dst_ref == '&':
			return '*'  # ptr to ref
		elif dst_ref == '*':
			return ''  # ptr to ptr
		else:
			return '*'  # ptr to value
	else:
		if dst_ref == '&':
			return ''  # value to ref
		elif dst_ref == '*':
			return '&'  # value to ptr
		else:
			return ''  # value to value


def transform_var_ref_to(var, from_ref, to_ref):
	if isinstance(var, _ScopedTypename):
		var = var.naked_name()
	return ctype_ref_to(from_ref, to_ref) + var


def add_list_unique(lst, val, dlg):
	for ent in lst:
		if dlg(val, ent):
			return
	lst.append(val)


def collect_attr_from_conv_recursive(out, conv, attr, dlg):
	for entry in getattr(conv, attr):
		add_list_unique(out, entry, dlg)
	for base in conv._bases:
		collect_attr_from_conv_recursive(out, base, attr, dlg)
	return out


class TypeConverter:
	def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None, needs_c_storage_class=False):
		self.ctype = parse(type, _CType)
		self.to_c_storage_ctype = parse(to_c_storage_type, _CType) if to_c_storage_type is not None else self.ctype.non_const()
		self.bound_name = get_ctype_default_bound_name(self.ctype) if bound_name is None else bound_name
		self.from_c_storage_ctype = parse(from_c_storage_type, _CType) if from_c_storage_type is not None else None  # if None the prototype return value type will be used to determine adequate storage at binding time

		if needs_c_storage_class:
			self.c_storage_class = 'storage_%s' % self.bound_name
		else:
			self.c_storage_class = None

		self.type_tag = 'type_tag_' + self.bound_name

		self.constructor = None
		self.members = []
		self.static_members = []
		self.methods = []
		self.static_methods = []
		self.arithmetic_ops = []
		self.comparison_ops = []

		self._non_copyable = False
		self._moveable = False
		self._inline = False
		self._supports_deep_compare = False
		self._is_pointer = False

		self._features = {}
		self._casts = []  # valid casts
		self._bases = []  # bases

		self.nobind = False

		self.check_func = apply_api_prefix('check_%s' % self.bound_name)
		self.to_c_func = apply_api_prefix('to_c_%s' % self.bound_name)
		self.from_c_func = apply_api_prefix('from_c_%s' % self.bound_name)

	def is_type_class(self):
		return False

	def get_operator(self, op):
		for arithmetic_op in self.arithmetic_ops:
			if arithmetic_op['op'] == op:
				return arithmetic_op

	def get_type_api(self, module_name):
		return ''

	def finalize_type(self):
		return ''

	def to_c_call(self, out_var, expr):
		assert 'not implemented in this converter'  # pragma: no cover
	def from_c_call(self, out_var, expr, ownership):
		assert 'not implemented in this converter'  # pragma: no cover

	def prepare_var_for_conv(self, var, input_ref):
		"""Transform a variable for use with the converter from_c/to_c methods."""
		return transform_var_ref_to(var, input_ref, self.to_c_storage_ctype.get_ref())
	def prepare_var_from_conv(self, var, target_ref):
		"""Transform a converted variable back to its ctype reference."""
		return transform_var_ref_to(var, self.to_c_storage_ctype.get_ref(), target_ref)

	def get_all_members(self):
		return collect_attr_from_conv_recursive([], self, 'members', lambda a,b: a['name'] == b['name'])
	def get_all_static_members(self):
		return collect_attr_from_conv_recursive([], self, 'static_members', lambda a,b: a['name'] == b['name'])
	def get_all_methods(self):
		return collect_attr_from_conv_recursive([], self, 'methods', lambda a,b: a['bound_name'] == b['bound_name'])
	def get_all_static_methods(self):
		return collect_attr_from_conv_recursive([], self, 'static_methods', lambda a,b: a['bound_name'] == b['bound_name'])

	def add_feature(self, key, val):
		self._features[key] = val


def format_list_for_comment(lst):
	ln = len(lst)

	if ln == 0:
		return ''
	if ln == 1:
		return lst[0]
	if ln == 2:
		return '%s or %s' % (lst[0], lst[1])

	return ', '.join(lst[:-1]) + ' or ' + lst[-1]


#
class FABGen:
	def __init__(self):
		self.verbose = True
		self.embedded = False
		self.check_self_type_in_ops = False
		self.defines = []

	def apply_api_prefix(self, symbol):
		return apply_api_prefix(symbol)

	def get_language(self):
		assert 'not implemented in this generator'  # pragma: no cover

	def parse_ctype(self, type):
		return parse(type, _CType)

	def parse_named_ctype(self, type):
		type = type.replace('* *', '**')
		return parse(type, _NamedCType)

	def ctype_to_plain_string(self, ctype):
		return ctype_to_plain_string(ctype)

	get_symbol_doc_hook = lambda gen, name: ""

	def get_symbol_doc(self, name):
		return self.get_symbol_doc_hook(name)

	def output_header(self):
		common = "// This file is automatically generated, do not modify manually!\n\n"

		self._source += "// FABgen output .cpp\n"
		self._source += common
		self._source += '#include "fabgen.h"\n\n'

		self._header += '// FABgen output .h\n'
		self._header += common
		self._header += '#pragma once\n\n'
		self._header += '#include <cstdint>\n\n'
		self._header += '#include <cstddef>\n\n'

	def output_includes(self):
		self.add_include('cstdint', True)
		self.add_include('cassert', True)
		self.add_include('map', True)

		self._source += '{{{__WRAPPER_INCLUDES__}}}\n'

	def start(self, name):
		self._name = name
		self._header, self._source = "", ""

		self.__system_includes, self.__user_includes = [], []

		self.__type_convs = {}
		self.__function_declarations = {}

		self._bound_types = []  # list of bound types
		self._bound_functions = []  # list of bound functions
		self._bound_variables = []  # list of bound variables
		self._enums = {}  # list of bound enumerations

		self._extern_types = []  # list of extern types

		self._custom_init_code = ""
		self._custom_free_code = ""

		self.output_header()
		self.output_includes()

		self._source += 'static bool _type_tag_can_cast(uint32_t in_type_tag, uint32_t out_type_tag);\n'
		self._source += 'static void *_type_tag_cast(void *in_T0, uint32_t in_type_tag, uint32_t out_type_tag);\n\n'

	def add_include(self, path, is_system=False):
		if is_system:
			if path not in self.__system_includes:
				self.__system_includes.append(path)
		else:
			if path not in self.__user_includes:
				self.__user_includes.append(path)

	def insert_code(self, code, in_source=True, in_header=True):
		if in_header:
			self._header += code
		if in_source:
			self._source += code

	def insert_binding_code(self, code, comment=None):
		parts = []
		if comment is not None:
			parts.append('// %s\n' % comment)
		parts.append(code)
		parts.append('\n')
		self._source += ''.join(parts)

	def add_custom_init_code(self, code):
		self._custom_init_code += code

	def add_custom_free_code(self, code):
		self._custom_free_code += code

	#
	def defined(self, symbol):
		return symbol in self.defines

	#
	def begin_type(self, conv, features, nobind=False):
		"""Declare a new type converter."""
		if self.verbose:
			print('Binding type %s (%s)' % (conv.bound_name, conv.ctype))

		self._header += conv.get_type_api(self._name)

		self._source += '// %s type tag\n' % conv.ctype
		self._source += 'static uint32_t %s = %s;\n\n' % (conv.type_tag, hex(zlib.crc32(conv.bound_name.encode()) & 0xffffffff))

		self._source += conv.get_type_api(self._name)

		conv.nobind = nobind
		conv._features = copy.deepcopy(features)

		self._bound_types.append(conv)
		self.__type_convs[repr(conv.ctype)] = conv

		feats = list(conv._features.values())
		for feat in feats:
			if hasattr(feat, 'init_type_converter'):
				feat.init_type_converter(self, conv)  # init converter feature

		return conv

	def end_type(self, conv):
		type_glue = conv.get_type_glue(self, self._name)
		self._source += type_glue + '\n'

	def bind_type(self, conv, features={}):
		self.begin_type(conv, features)
		self.end_type(conv)
		return conv

	#
	def typedef(self, type, alias_of, to_c_storage_type=None, bound_name=None):
		conv = copy.deepcopy(self.__type_convs[alias_of])

		default_arg_storage_type = type if to_c_storage_type is None else to_c_storage_type

		if bound_name is not None:
			conv.bound_name=bound_name
		conv.ctype = parse(type, _CType)
		conv.to_c_storage_ctype = parse(default_arg_storage_type, _CType)

		self.__type_convs[type] = conv

	#
	def bind_named_enum(self, name, symbols, storage_type='int', bound_name=None, prefix='', namespace=None):
		if bound_name is None:
			bound_name = get_symbol_default_bound_name(name)

		self.typedef(name, storage_type, bound_name=bound_name)

		if namespace is None:
			namespace = name

		enum = {}
		for symbol in symbols:
			enum[prefix + symbol] = '%s::%s' % (namespace, symbol)

		self._enums[bound_name] = enum

	#
	def begin_class(self, type, converter_class=None, noncopyable=False, moveable=False, bound_name=None, features={}, nobind=False):
		"""Begin a class declaration."""
		if type in self.__type_convs:
			return self.__type_convs[type]  # type already declared

		default_storage_type = type + '*'

		conv = self.default_class_converter(type, default_storage_type, bound_name) if converter_class is None else converter_class(type, default_storage_type, bound_name)
		conv = self.begin_type(conv, features, nobind)

		conv._non_copyable = noncopyable
		conv._moveable = moveable
		return conv

	def end_class(self, conv):
		"""End a class declaration."""
		self.end_type(conv)

	#
	def bind_extern_type(self, type, bound_name=None, module=None):
		"""Bind an external type."""
		if type in self.__type_convs:
			return self.__type_convs[type]  # type already declared

		default_storage_type = type + '*'

		conv = self.default_extern_converter(type, default_storage_type, bound_name, module)

		if self.verbose:
			print('Binding extern type %s (%s)' % (conv.bound_name, conv.ctype))

		self._header += conv.get_type_api(self._name)
		self._source += conv.get_type_api(self._name)

		self._extern_types.append(conv)
		self.__type_convs[repr(conv.ctype)] = conv

		self._source += conv.get_type_glue(self, self._name) + '\n'
		return conv

	#
	def bind_ptr(self, type, converter_class=None, bound_name=None, features={}):
		if type in self.__type_convs:
			return self.__type_convs[type]  # type already declared

		conv = self.default_ptr_converter(type, None, bound_name) if converter_class is None else converter_class(type, None, bound_name)
		self.bind_type(conv, features)

		return conv

	#
	def add_cast(self, src_conv, tgt_conv, cast_delegate):
		"""Declare a cast delegate from one type to another."""
		src_conv._casts.append((tgt_conv, cast_delegate))

	#
	def __add_upcast(self, conv, base):
		self.add_cast(conv, base, lambda in_var, out_var: '%s = (%s *)((%s *)%s);\n' % (out_var, base.ctype, conv.ctype, in_var))
		for base_of_base in base._bases:
			self.__add_upcast(conv, base_of_base)

	def add_base(self, conv, base):
		self.__add_upcast(conv, base)
		conv._bases.append(base)

	def add_bases(self, conv, bases):
		for base in bases:
			self.add_base(conv, base)

	#
	def select_ctype_conv(self, ctype):
		"""Select a type converter."""

		if repr(ctype) == 'void':
			return None

		while True:
			type = repr(ctype)
			if type in self.__type_convs:
				return self.__type_convs[type]

			type = repr(ctype.non_const())
			if type in self.__type_convs:
				return self.__type_convs[type]

			if ctype.get_ref() == '':
				break

			ctype = ctype.dereference_once()

		raise Exception("Unknown type %s (no converter available)" % ctype)

	def get_conv(self, type):
		return self.__type_convs[type]

	#
	def decl_var(self, ctype, name, eol=';\n'):
		return '%s %s%s' % (get_fully_qualified_ctype_name(ctype), name, eol)

	#
	def select_args_convs(self, args):
		return [{'conv': self.select_ctype_conv(arg.ctype), 'ctype': arg.ctype} for i, arg in enumerate(args)]

	#
	def commit_from_c_vars(self, rval, ctx):
		assert 'not implemented in this generator'  # pragma: no cover

	def rval_assign_arg_in_out(self, out_var, arg_in_out):
		assert 'not implemented in this generator'  # pragma: no cover

	#
	def proxy_call_error(self, msg, ctx):
		assert 'not implemented in this generator'  # pragma: no cover

	#
	def __ctype_to_ownership_policy(self, ctype):
		return 'Copy' if ctype.get_ref() == '' else 'NonOwning'

	# --
	def __expand_protos(self, protos):
		_protos = []

		for proto in protos:
			_proto = (proto[0], [], proto[2])

			for arg in proto[1]:
				if arg.startswith('?'):
					_protos.append(_proto)
					_proto = copy.deepcopy(_proto)
					arg = arg[1:]

				_proto[1].append(arg)

			_protos.append(_proto)

		return _protos

	def __prepare_protos(self, protos):
		"""Prepare a list of prototypes, select converter objects"""
		_protos = []

		for proto in protos:
			assert len(proto) == 3, "prototype incomplete. Expected 3 entries (type, [arguments], [features]), found %d" % len(proto)

			rval_type, args, features = proto

			rval_ctype = parse(rval_type, _CType)
			rval_conv = self.select_ctype_conv(rval_ctype)

			if rval_conv is not None and rval_conv.from_c_storage_ctype is not None:
				from_c_storage_ctype = rval_conv.from_c_storage_ctype
			else:
				from_c_storage_ctype = rval_ctype  # prepare the return value variable CType
				if from_c_storage_ctype.get_ref() == '':
					from_c_storage_ctype = from_c_storage_ctype.non_const()

			_proto = {'rval': {'storage_ctype': from_c_storage_ctype, 'conv': rval_conv}, 'args': [], 'argsin': [], 'features': features}

			if not type(args) is type([]):
				args = [args]

			for arg in args:
				carg = self.parse_named_ctype(arg)
				conv = self.select_ctype_conv(carg.ctype)
				_proto['args'].append({'carg': carg, 'conv': conv, 'check_var': None})

			# prepare argsin, a list of arguments that should be provided by the caller
			_proto['argsin'] = _proto['args']  # default to the full arg list

			if 'arg_out' in features:  # exclude output arguments from the argsin list
				_proto['argsin'] = [arg for arg in _proto['args'] if arg['carg'].name.naked_name() not in _proto['features']['arg_out']]

			_protos.append(_proto)

		# compute suggested_suffix if language doesn't support overload
		if len(_protos) > 1:
			# get the base one, usually the first one with the less args
			id_base = 0
			proto_base = _protos[id_base]
			for id, proto in enumerate(_protos[1:]):
				if len(proto["args"]) < len(proto_base["args"]):
					proto_base = proto
					id_base = id + 1

			suggested_suffixes = []
			
			for id, proto in enumerate(_protos):
				if id == id_base:
					continue
				
				# check members difference
				def get_suggested_suffix(with_type = False):
					suggested_suffix = ""
					for i, arg in enumerate(proto["args"]):
						if i >= len(proto_base["args"]) or proto_base["args"][i]["carg"].name != arg["carg"].name or str(proto_base["args"][i]["carg"].ctype) != str(arg["carg"].ctype):
							if suggested_suffix == "":
								suggested_suffix = "With"
							if with_type:
								if arg["conv"].bound_name is not None:
									suggested_suffix += clean_name_with_title(str(arg["conv"].bound_name))
								else:
									suggested_suffix += clean_name_with_title(str(arg['carg'].ctype))

								if suggested_suffix.endswith("_nobind") and arg["conv"].nobind:
									suggested_suffix = suggested_suffix[:-len("_nobind")]

							suggested_suffix += clean_name_with_title(str(arg["carg"].name))
					return suggested_suffix

				suggested_suffix = get_suggested_suffix()
				
				# check if this suffix already exists
				if suggested_suffix in suggested_suffixes:
					# recheck the suggested suffix, but with the type
					suggested_suffix = get_suggested_suffix(True)

				suggested_suffixes.append(suggested_suffix)

				proto["suggested_suffix"] = suggested_suffix

		return _protos

	def __assert_conv_feature(self, conv, feature):
		assert feature in conv._features, "Type converter for %s does not support the %s feature" % (conv.ctype, feature)

	#
	def _prepare_to_c_self(self, conv, out_var, ctx='none', features=[]):
		out = ''
		if 'proxy' in features:
			proxy = conv._features['proxy']

			out += '	' + self.decl_var(conv.to_c_storage_ctype, '%s_wrapped' % out_var)
			out += '	' + conv.to_c_call(self.get_self(ctx), '&%s_wrapped' % out_var)

			out += '	' + self.decl_var(proxy.wrapped_conv.to_c_storage_ctype, out_var)
			out += proxy.unwrap('%s_wrapped' % out_var, out_var)
		else:
			out += '	' + self.decl_var(conv.to_c_storage_ctype, out_var)
			out += '	' + conv.to_c_call(self.get_self(ctx), '&%s' % out_var)
		return out

	def _declare_to_c_var(self, ctype, var):
		return self.decl_var(ctype, var)

	def _convert_to_c_var(self, idx, conv, var, ctx='default', features=[]):
		out = conv.to_c_call(self.get_var(idx, ctx), '&%s' % var)

		if 'validate_arg_in' in features:
			validator = features['validate_arg_in'][idx]
			if validator is not None:
				out += validator(self, var, ctx)

		return out

	def prepare_to_c_var(self, idx, conv, var, ctx='default', features=[]):
		return self._declare_to_c_var(conv.to_c_storage_ctype, var) + self._convert_to_c_var(idx, conv, var, ctx, features)

	#
	def declare_from_c_var(self, out_var):
		return ''

	def prepare_from_c_var(self, rval):
		if rval['ownership'] is None:
			rval['ownership'] = self.__ctype_to_ownership_policy(rval['ctype'])

		# transform from {T&, T*, T**, ...} to T* where T is conv.ctype
		expr = transform_var_ref_to(rval['var'], rval['ctype'].get_ref(), rval['conv'].ctype.add_ref('*').get_ref())

		out_var = (rval['var'] if isinstance(rval['var'], str) else rval['var'].naked_name()) + '_out'
		src = self.declare_from_c_var(out_var)
		if 'rval_transform' in rval['conv']._features:
			src += rval['conv']._features['rval_transform'](self, rval['conv'], expr, out_var, rval['ownership'])
		else:
			check_is_valid_pointer = rval['ctype'].is_pointer() or rval['conv']._is_pointer

			if check_is_valid_pointer:
				src += 'if (!%s) {\n' % rval['var']
				src += self.rval_from_nullptr(out_var)
				src += '} else {\n'

			if rval['conv'].is_type_class() and rval['is_arg_in_out']:  # if an object is used as arg_out then reuse the input argument directly 
				src += self.rval_assign_arg_in_out(out_var, self.get_var(rval['arg_idx'], rval['ctx']))
			else:
				src += self.rval_from_c_ptr(rval['conv'], out_var, expr, rval['ownership'])

			if check_is_valid_pointer:
				src += '}\n'

		return src

	#
	def _proto_call(self, self_conv, proto, expr_eval, ctx, fixed_arg_count=None):
		parts = []

		features = proto['features']

		enable_proxy = 'proxy' in features
		if enable_proxy:
			assert ctx != 'function', "Proxy feature cannot be used for a function call"

			if self_conv is not None:
				self.__assert_conv_feature(self_conv, 'proxy')

		# prepare C call self argument
		if self_conv:
			if ctx in ['getter', 'setter', 'method', 'arithmetic_op', 'inplace_arithmetic_op', 'comparison_op']:
				parts.append(self._prepare_to_c_self(self_conv, '_self', ctx, features))

		# prepare C call arguments
		args = proto['args']
		arg_out = features['arg_out'] if 'arg_out' in features else None

		c_call_args = []

		argin_idx = 0
		for idx, arg in enumerate(args):
			conv = arg['conv']

			var = 'arg%d' % idx

			if arg_out is not None and arg['carg'].name.naked_name() in arg_out:
				arg_ctype = conv.ctype
				parts.append(self._declare_to_c_var(arg_ctype, var))
			else:
				arg_ctype = conv.to_c_storage_ctype
				parts.append(self._declare_to_c_var(conv.to_c_storage_ctype, var))
				parts.append(self._convert_to_c_var(argin_idx, conv, var, ctx, features))
				argin_idx += 1

			c_call_args.append(transform_var_ref_to(var, arg_ctype.get_ref(), arg['carg'].ctype.get_ref()))

		if 'arg_in_out' in features:  # add in_out vars to the arg_out list
			if arg_out is None:
				arg_out = []
			arg_out = arg_out + features['arg_in_out']

		# c++ exception support
		if 'exception' in features:
			parts.append('try {\n')

		# declare return value
		rvals = []
		rvals_prepare_args = []

		if ctx == 'constructor':
			rval_conv = proto['rval']['conv']
			from_c_storage_ctype = proto['rval']['storage_ctype'].add_ref('*')  # constructor returns a pointer

			ownership = 'Owning'  # constructor output is always owned by the VM

			if enable_proxy:
				proxy = rval_conv._features['proxy']

				parts.append(self.decl_var(proxy.wrapped_conv.ctype.add_ref('*'), 'rval_raw', ' = '))
				parts.append('new %s(%s);\n' % (proxy.wrapped_conv.ctype, ', '.join(c_call_args)))

				parts.append(self.decl_var(from_c_storage_ctype, 'rval'))
				parts.append(proxy.wrap('rval_raw', 'rval'))
			else:
				if 'route' in features:
					parts.append(self.decl_var(from_c_storage_ctype, 'rval', ' = '))

					expr_eval = features['route']  # hijack the output expression
					parts.append(expr_eval(c_call_args) + '\n')
				else:
					if rval_conv._inline:
						if len(c_call_args) > 0:
							parts.append('%s _new_obj(%s);\n' % (rval_conv.ctype, ', '.join(c_call_args)))  # construct new inline object on the stack
						else:
							parts.append('%s _new_obj;\n' % rval_conv.ctype)
						ownership = 'Copy'  # inline objects are constructed on the heap then copy constructed to the VM memory block

					parts.append(self.decl_var(from_c_storage_ctype, 'rval', ' = '))

					if rval_conv._inline:
						parts.append('&_new_obj;\n')
					else:
						parts.append('new %s(%s);\n' % (rval_conv.ctype, ', '.join(c_call_args)))

			rvals_prepare_args.append({'conv': rval_conv, 'ctype': from_c_storage_ctype, 'var': 'rval', 'is_arg_in_out': False, 'ctx': ctx, 'ownership': ownership})
			rvals.append('rval')
		else:
			rval_conv = proto['rval']['conv']
			from_c_storage_ctype = proto['rval']['storage_ctype']

			# return value is optional for a function call
			if rval_conv:
				parts.append(self.decl_var(from_c_storage_ctype, 'rval', ' = '))

			if 'route' in features:
				if self_conv:
					c_call_args = ['_self'] + c_call_args
				expr_eval = features['route']  # hijack the output expression

			parts.append(expr_eval(c_call_args) + '\n')

			if rval_conv:
				ownership = None  # automatic ownership policy
				if 'new_obj' in features:
					ownership = 'Owning'  # force ownership when the prototype is flagged to return a new object
				elif 'copy_obj' in features:
					ownership = 'Copy'  # force copy ownership

				rvals_prepare_args.append({'conv': rval_conv, 'ctype': from_c_storage_ctype, 'var': 'rval', 'is_arg_in_out': False, 'ctx': ctx, 'ownership': ownership})
				rvals.append('rval')

		# process arg_out
		if arg_out is not None:
			arg_in_out = features['arg_in_out'] if 'arg_in_out' in features else []

			for idx, arg in enumerate(args):
				carg_name = arg['carg'].name.naked_name()

				if carg_name in arg_out:
					is_arg_in_out = carg_name in arg_in_out

					if is_arg_in_out:
						arg_ctype = arg['conv'].to_c_storage_ctype
					else:
						arg_ctype = arg['conv'].ctype

					rvals_prepare_args.append({'conv': arg['conv'], 'ctype': arg_ctype, 'var': 'arg%d' % idx, 'is_arg_in_out': is_arg_in_out, 'arg_idx': idx, 'ctx': ctx, 'ownership': None})
					rvals.append('arg%d' % idx)

		# check return values
		if 'check_rval' in features:
			parts.append(features['check_rval'](rvals, ctx))

		# prepare return values ([EJ] once check is done so we don't leak)
		for rval in rvals_prepare_args:
			parts.append(self.prepare_from_c_var(rval))

		parts.append(self.commit_from_c_vars(rvals, ctx))

		if 'exception' in features:
			parts.append('}\n')
			parts.append('catch(...) {\n')
			parts.append(self.proxy_call_error(features['exception'], ctx))
			parts.append('}\n')

		return ''.join(parts)

	def _bind_proxy(self, name, self_conv, protos, desc, expr_eval, ctx, fixed_arg_count=None):
		parts = []

		if self.verbose:
			print('Binding proxy %s' % name)

		protos = self.__expand_protos(protos)
		protos = self.__prepare_protos(protos)

		# categorize prototypes by number of argument they take
		def get_protos_per_arg_count(protos):
			by_arg_count = {}
			for proto in protos:
				arg_count = len(proto['argsin'])
				if arg_count not in by_arg_count:
					by_arg_count[arg_count] = []
				by_arg_count[arg_count].append(proto)
			return by_arg_count


		protos_by_arg_count = get_protos_per_arg_count(protos)

		# prepare proxy function
		self.insert_code('// %s\n' % desc, True, False)

		max_arg_count = max(protos_by_arg_count.keys())

		parts.append(self.open_proxy(name, max_arg_count, ctx))

		# check self
		if self.check_self_type_in_ops and ctx in ['arithmetic_op', 'inplace_arithmetic_op', 'comparison_op']:
			parts.append('if (!%s) {\n' % self_conv.check_call(self.get_self(ctx)))
			parts.append(self.proxy_call_error('incorrect type for argument 0 to %s, expected %s' % (desc, self_conv.bound_name), ctx))
			parts.append('}\n\n')

		# output dispatching logic
		def get_protos_per_arg_conv(protos, arg_idx):
			per_arg_conv = {}
			for proto in protos:
				arg_conv = proto['argsin'][arg_idx]['conv']
				if arg_conv not in per_arg_conv:
					per_arg_conv[arg_conv] = []
				per_arg_conv[arg_conv].append(proto)
			return per_arg_conv
			

		has_fixed_argc = fixed_arg_count is not None

		if has_fixed_argc:
			assert len(protos_by_arg_count) == 1 and fixed_arg_count in protos_by_arg_count

		for arg_count, protos_with_arg_count in protos_by_arg_count.items():
			if not has_fixed_argc:
				parts.append('	if (arg_count == %d) {\n' % arg_count)

			def output_arg_check_and_dispatch(protos, arg_idx, arg_limit):
				parts = []
				indent = '	' * (arg_idx+(2 if not has_fixed_argc else 1))

				if arg_idx == arg_limit:
					assert len(protos) == 1  # there should only be exactly one prototype with a single signature
					parts.append(self._proto_call(self_conv, protos[0], expr_eval, ctx, fixed_arg_count))
					return ''.join(parts)

				protos_per_arg_conv = get_protos_per_arg_conv(protos, arg_idx)

				parts.append(indent)
				for conv, protos_for_conv in protos_per_arg_conv.items():
					parts.append('if (%s) {\n' % conv.check_call(self.get_var(arg_idx, ctx)))
					parts.append(output_arg_check_and_dispatch(protos_for_conv, arg_idx+1, arg_limit))
					parts.append(indent + '} else ')

				parts.append('{\n')

				expected_types = []
				for proto in protos:
					proto_arg = proto['argsin'][arg_idx]

					proto_arg_name = str(proto_arg['carg'].name)
					proto_arg_bound_name = proto_arg['conv'].bound_name

					expected_types.append('%s %s' % (proto_arg_bound_name, proto_arg_name))

				parts.append(self.set_error('runtime', 'incorrect type for argument %d to %s, expected %s' % (arg_idx+1, desc, format_list_for_comment(expected_types))))
				parts.append(indent + '}\n')
				return ''.join(parts)

			parts.append(output_arg_check_and_dispatch(protos_with_arg_count, 0, arg_count))

			if not has_fixed_argc:
				parts.append('	} else ')

		if not has_fixed_argc:
			parts.append('{\n')
			parts.append(self.set_error('runtime', 'incorrect number of arguments to %s' % desc))
			parts.append('	}\n')

		#
		parts.append(self.close_proxy(ctx))
		parts.append('\n')

		self._source += ''.join(parts)

	#
	def __do_bind_function_overloads(self, name, protos, bound_name=None):
		expr_eval = lambda args: '%s(%s);' % (name, ', '.join(args))

		if bound_name is None:
			bound_name = get_symbol_default_bound_name(name)
		proxy_name = apply_api_prefix(bound_name)

		self._bind_proxy(proxy_name, None, protos, 'function %s' % bound_name, expr_eval, 'function')
		self._bound_functions.append({'name': name, 'bound_name': bound_name, 'proxy_name': proxy_name, 'protos': protos})

	def __commit_function_declarations(self):
		for name, decl in self.__function_declarations.items():
			self.__do_bind_function_overloads(name, decl['protos'], decl['bound_name'])

	def bind_function(self, name, rval, args, features=[], bound_name=None):
		self.bind_function_overloads(name, [(rval, args, features)], bound_name)

	def bind_function_overloads(self, name, protos, bound_name=None):
		if not name in self.__function_declarations:
			fn = self.__function_declarations[name] = {
				'protos': protos,
				'bound_name': bound_name
			}
		else:
			fn = self.__function_declarations[name]
			assert(bound_name == fn['bound_name'])  # ensure bound_name coherency
			fn['protos'] = fn['protos'] + protos

	# reverse binding support
	def _get_rbind_call_signature(self, name, rval, args):
		assert 'not implemented in this generator'  # pragma: no cover

	def _prepare_rbind_call(self, rval, args):
		assert 'not implemented in this generator'  # pragma: no cover

	def _rbind_call(self, rval, args, success_var):
		assert 'not implemented in this generator'  # pragma: no cover

	def _clean_rbind_call(self, rval, args):
		assert 'not implemented in this generator'  # pragma: no cover

	def __get_rbind_call_signature(self, name, rval, args, output_default_args):
		return '%s %s(%s%s, bool *success%s)' % (rval, name, self._get_rbind_call_custom_args(), (', ' + ', '.join([str(arg) for arg in args])) if len(args) > 0 else '', ' = NULL' if output_default_args else '')

	def rbind_function(self, name, rval, args, internal=False):
		parts = []
		args = [self.parse_named_ctype(arg) for arg in args]

		if internal:
			parts.append('static inline %s {\n' % self.__get_rbind_call_signature(apply_api_prefix(name), rval, args, True))
		else:
			self._header += '// C to Lua reverse binding call ' + name + '\n'
			self._header += self.__get_rbind_call_signature(apply_api_prefix(name), rval, args, True) + ';\n\n'
			parts.append('%s {\n' % self.__get_rbind_call_signature(apply_api_prefix(name), rval, args, False))

		parts.append(self._prepare_rbind_call(rval, args))

		# prepare args
		for arg in args:
			arg_conv = self.select_ctype_conv(arg.ctype)
			parts.append(self.prepare_from_c_var({'conv': arg_conv, 'ctype': arg.ctype, 'var': arg.name, 'is_arg_in_out': False, 'ownership': None}))

		parts.append(self.commit_from_c_vars([arg.name for arg in args], 'rbind_args'))

		# call
		parts.append('bool _call_success_var;')
		parts.append('\n' + self._rbind_call(rval, args, '_call_success_var') + '\n')
		parts.append('''\
if (success)
	*success = _call_success_var;
''')

		# rval
		if rval != 'void':
			rval_conv = self.select_ctype_conv(self.parse_ctype(rval))

			parts.append(self._declare_to_c_var(rval_conv.to_c_storage_ctype, '_rbind_rval'))
			parts.append('''\
if (%s) {
	%s
} else if (success != NULL) {
	*success = false;
}
''' % (rval_conv.check_call(self.get_var(0, 'rbind_rval')), self._convert_to_c_var(0, rval_conv, '_rbind_rval', 'rbind_rval')))

		parts.append(self._clean_rbind_call(rval, args))

		if rval != 'void':
			parts.append('return _rbind_rval;\n')

		parts.append('}\n')
		self._source += ''.join(parts)

	#
	def bind_constructor(self, conv, args, features=[]):
		self.bind_constructor_overloads(conv, [(args, features)])

	def bind_constructor_overloads(self, conv, proto_args):
		type = repr(conv.ctype)
		expr_eval = None  # unused for constructors

		protos = [(type, args[0], args[1]) for args in proto_args]
		proxy_name = apply_api_prefix('construct_%s' % conv.bound_name)

		self._bind_proxy(proxy_name, conv, protos, '%s constructor' % conv.bound_name, expr_eval, 'constructor')
		conv.constructor = {'proxy_name': proxy_name, 'protos': protos}

	#
	def bind_method(self, conv, name, rval, args, features=[], bound_name=None):
		self.bind_method_overloads(conv, name, [(rval, args, features)], bound_name)

	def bind_method_overloads(self, conv, name, protos, bound_name=None):
		expr_eval = lambda args: '_self->%s(%s);' % (name, ', '.join(args))

		if bound_name is None:
			bound_name = get_symbol_default_bound_name(name)
		proxy_name = apply_api_prefix('method_%s_of_%s' % (bound_name, conv.bound_name))

		self._bind_proxy(proxy_name, conv, protos, 'method %s of %s' % (bound_name, conv.bound_name), expr_eval, 'method')
		conv.methods.append({'name': name, 'bound_name': bound_name, 'proxy_name': proxy_name, 'protos': protos})

	#
	def bind_static_method(self, conv, name, rval, args, features=[], bound_name=None):
		self.bind_static_method_overloads(conv, name, [(rval, args, features)], bound_name)

	def bind_static_method_overloads(self, conv, name, protos, bound_name=None):
		expr_eval = lambda args: '%s::%s(%s);' % (conv.ctype, name, ', '.join(args))

		if bound_name is None:
			bound_name = get_symbol_default_bound_name(name)
		proxy_name = apply_api_prefix('static_method_%s_of_%s' % (bound_name, conv.bound_name))

		self._bind_proxy(proxy_name, conv, protos, 'static method %s of %s' % (bound_name, conv.bound_name), expr_eval, 'static_method')
		conv.static_methods.append({'name': name, 'bound_name': bound_name, 'proxy_name': proxy_name, 'protos': protos})

	#
	def bind_members(self, conv, members, features=[]):
		for member in members:
			self.bind_member(conv, member, features)

	def bind_member(self, conv, member, features=[]):
		is_bitfield = member.endswith(':')
		if is_bitfield:
			member = member[:-1]

		arg = parse(member, _NamedCType)

		# getter
		expr_eval = lambda args: '_self->%s;' % arg.name
		arg_ctype = arg.ctype if is_bitfield else arg.ctype.add_ref('&')
		getter_protos = [(repr(arg_ctype), [], features)]
		getter_proxy_name = apply_api_prefix('get_%s_of_%s' % (get_symbol_default_bound_name(arg.name), conv.bound_name))

		self._bind_proxy(getter_proxy_name, conv, getter_protos, 'get member %s of %s' % (arg.name, conv.bound_name), expr_eval, 'getter', 0)

		# setter
		if not arg.ctype.is_const():
			expr_eval = lambda args: '_self->%s = %s;' % (arg.name, args[0])

			setter_protos = [('void', [member], features)]
			setter_proxy_name = apply_api_prefix('set_%s_of_%s' % (get_symbol_default_bound_name(arg.name), conv.bound_name))

			self._bind_proxy(setter_proxy_name, conv, setter_protos, 'set member %s of %s' % (arg.name, conv.bound_name), expr_eval, 'setter', 1)
		else:
			setter_proxy_name = None

		conv.members.append({'name': arg.name, 'ctype': arg.ctype, 'getter': getter_proxy_name, 'setter': setter_proxy_name, 'is_bitfield': is_bitfield})

	#
	def bind_static_member(self, conv, member, features=[]):
		arg = parse(member, _NamedCType)

		# getter
		if 'proxy' in features:
			self.__assert_conv_feature(conv, 'proxy')
			expr_eval = lambda args: '&%s::%s;' % (conv._features['proxy'].wrapped_conv.ctype, arg.name)
		else:
			expr_eval = lambda args: '&%s::%s;' % (conv.ctype, arg.name)

		getter_protos = [(repr(arg.ctype.add_ref('*')), [], features)]
		getter_proxy_name = apply_api_prefix('get_%s_of_%s' % (get_symbol_default_bound_name(arg.name), conv.bound_name))
		
		self._bind_proxy(getter_proxy_name, None, getter_protos, 'get static member %s of %s' % (arg.name, conv.bound_name), expr_eval, 'getter', 0)

		# setter
		if not arg.ctype.is_const():
			expr_eval = lambda args: '%s::%s = %s;' % (conv.ctype, arg.name, args[0])

			setter_protos = [('void', [member], features)]
			setter_proxy_name = apply_api_prefix('set_%s_of_%s' % (get_symbol_default_bound_name(arg.name), conv.bound_name))

			self._bind_proxy(setter_proxy_name, None, setter_protos, 'set static member %s of %s' % (arg.name, conv.bound_name), expr_eval, 'setter', 1)
		else:
			setter_proxy_name = None

		conv.static_members.append({'name': arg.name, 'ctype': arg.ctype, 'getter': getter_proxy_name, 'setter': setter_proxy_name})

	def bind_static_members(self, conv, members, features=[]):
		for member in members:
			self.bind_static_member(conv, member, features)

	#
	def bind_variable(self, var, features=[], bound_name=None, group=None):
		arg = self.parse_named_ctype(var)
		conv = self.select_ctype_conv(arg.ctype)

		if bound_name == None:
			bound_name = get_symbol_default_bound_name(arg.name)

		# getter
		expr_eval = lambda args: '&%s;' % arg.name

		getter_protos = [(repr(arg.ctype.add_ref('*')), [], features)]
		getter_proxy_name = apply_api_prefix('get_%s_variable' % bound_name)

		self._bind_proxy(getter_proxy_name, None, getter_protos, 'get variable %s' % arg.name, expr_eval, 'getter', 0)

		# setter
		if not(arg.ctype.is_const() or conv._non_copyable):
			expr_eval = lambda args: '%s = %s;' % (arg.name, args[0])

			setter_protos = [('void', ["%s %s" % (str(arg.ctype), bound_name)], features)]
			setter_proxy_name = apply_api_prefix('set_%s_variable' % bound_name)

			self._bind_proxy(setter_proxy_name, None, setter_protos, 'set variable %s' % arg.name, expr_eval, 'setter', 1)
		else:
			setter_proxy_name = None

		self._bound_variables.append({'name': arg.name, 'bound_name': bound_name, 'ctype': arg.ctype, 'getter': getter_proxy_name, 'setter': setter_proxy_name, 'group': group})

	def bind_variables(self, vars, features=[], group=None):
		for var in vars:
			self.bind_variable(var, features, None, group)

	#
	def bind_constant(self, type, name, value, group=None):
		self.insert_binding_code('static const %s %s = %s;\n' % (type, name, value))
		self.bind_variable('const %s %s' % (type, name), [], None, group)

	def bind_constants(self, type, names_values, group=None):
		for nv in names_values:
			self.bind_constant(type, nv[0], nv[1], group)

	#
	def bind_arithmetic_op(self, conv, op, rval, args, features=[]):
		self.bind_arithmetic_op_overloads(conv, op, [(rval, args, features)])

	def bind_arithmetic_op_overloads(self, conv, op, protos):
		assert op in ['-', '+', '*', '/'], 'Unsupported arithmetic operator ' + op

		expr_eval = lambda args: '*_self %s %s;' % (op, ', '.join(args))
		proxy_name = apply_api_prefix('%s_operator_of_%s' % (get_clean_symbol_name(op), conv.bound_name))

		self._bind_proxy(proxy_name, conv, protos, '%s operator of %s' % (op, conv.bound_name), expr_eval, 'arithmetic_op', 1)
		conv.arithmetic_ops.append({'op': op, 'proxy_name': proxy_name, 'protos': protos})

	def bind_arithmetic_ops(self, conv, ops, rval, args, features=[]):
		for op in ops:
			self.bind_arithmetic_op(conv, op, rval, args, features)

	def bind_arithmetic_ops_overloads(self, conv, ops, protos):
		for op in ops:
			self.bind_arithmetic_op_overloads(conv, op, protos)

	#
	def bind_inplace_arithmetic_op(self, conv, op, args, features=[]):
		self.bind_inplace_arithmetic_op_overloads(conv, op, [(args, features)])

	def bind_inplace_arithmetic_op_overloads(self, conv, op, args):
		assert op in ['-=', '+=', '*=', '/='], 'Unsupported inplace arithmetic operator ' + op

		expr_eval = lambda args: '*_self %s %s;' % (op, ', '.join(args))
		proxy_name = apply_api_prefix('%s_operator_of_%s' % (get_clean_symbol_name(op), conv.bound_name))
		protos = [('void', arg[0], arg[1]) for arg in args]

		self._bind_proxy(proxy_name, conv, protos, '%s operator of %s' % (op, conv.bound_name), expr_eval, 'inplace_arithmetic_op', 1)
		conv.arithmetic_ops.append({'op': op, 'proxy_name': proxy_name, 'protos': protos})

	def bind_inplace_arithmetic_ops(self, conv, ops, args, features=[]):
		for op in ops:
			self.bind_inplace_arithmetic_op(conv, op, args, features)

	def bind_inplace_arithmetic_ops_overloads(self, conv, ops, args):
		for op in ops:
			self.bind_inplace_arithmetic_op_overloads(conv, op, args)

	#
	def bind_comparison_op(self, conv, op, args, features=[]):
		self.bind_comparison_op_overloads(conv, op, [(args, features)])

	def bind_comparison_op_overloads(self, conv, op, args):
		assert op in ['<', '<=', '==', '!=', '>', '>='], 'Unsupported comparison operator ' + op

		expr_eval = lambda args: '*_self %s %s;' % (op, ', '.join(args))
		proxy_name = apply_api_prefix('%s_operator_of_%s' % (get_clean_symbol_name(op), conv.bound_name))
		protos = [('bool', arg[0], arg[1]) for arg in args]

		self._bind_proxy(proxy_name, conv, protos, '%s operator of %s' % (op, conv.bound_name), expr_eval, 'comparison_op', 1)
		conv.comparison_ops.append({'op': op, 'proxy_name': proxy_name, 'protos': protos})

	def bind_comparison_ops(self, conv, ops, args, features=[]):
		for op in ops:
			self.bind_comparison_op(conv, op, args, features)

	def bind_comparison_ops_overloads(self, conv, ops, protos):
		for op in ops:
			self.bind_comparison_op_overloads(conv, op, protos)

	#
	def get_type_tag_cast_function(self):
		out = '// type_tag based cast system\n'

		def output_type_tag_cast_tree(expr):
			out = []

			i = 0
			for conv in self._bound_types:
				if len(conv._casts) == 0:
					continue

				out.append('	' if i == 0 else ' else ')
				out.append('if (in_type_tag == %s) {\n' % conv.type_tag)

				for j, cast in enumerate(conv._casts):
					out.append('	' if j == 0 else ' else ')
					out.append('if (out_type_tag == %s) {\n' % cast[0].type_tag)
					out.append(expr(cast))
					out.append('}\n')

				out.append('}\n')
				i += 1

			return ''.join(out)

		# can cast
		out += '''\
static bool _type_tag_can_cast(uint32_t in_type_tag, uint32_t out_type_tag) {
	if (out_type_tag == in_type_tag)
		return true;

	%s
	return false;
}\n\n''' % output_type_tag_cast_tree(lambda cast: '	return true;\n')

		# cast
		out += '''\
static void *_type_tag_cast(void *in_ptr, uint32_t in_type_tag, uint32_t out_type_tag) {
	if (out_type_tag == in_type_tag)
		return in_ptr;

	void *out_ptr = NULL;
	%s

	return out_ptr;
}\n\n''' % output_type_tag_cast_tree(lambda cast: cast[1]('in_ptr', 'out_ptr'))

		return out

	def bind_cast_functions(self):
		upcasts = {}
		for conv in self._bound_types:
			if not conv.nobind:
				if conv not in upcasts:
					upcasts[conv] = []
				for cast in conv._casts:
					if not cast[0].nobind and cast[0] not in upcasts[conv]:
						upcasts[conv].append(cast[0])

		for conv, casts in upcasts.items():
			for cast in casts:
				name = '_Cast_%s_To_%s' % (cast.bound_name, conv.bound_name)
				self.insert_binding_code('static %s *%s(%s *o) { return (%s *)o; }' % (repr(conv.ctype), name, repr(cast.ctype), repr(conv.ctype)))
				self.bind_function(name, repr(conv.ctype) + ' *', [repr(cast.ctype) + ' *o'], [], name[1:])

	def __get_stats(self):  # pragma: no cover
		out = 'Module statistics:\n'

		out += ' - %d types\n' % len(self.__type_convs)
		out += ' - %d functions\n' % len(self._bound_functions)
		out += ' - %d enums\n' % len(self._enums)
		out += ' - %d extern types\n' % len(self._extern_types)

		method_count, static_method_count, member_count, static_member_count = 0, 0, 0, 0

		for name, conv in self.__type_convs.items():
			method_count += len(conv.methods)
			static_method_count += len(conv.static_methods)
			member_count += len(conv.members)
			static_member_count += len(conv.static_members)

		out += ' - %d methods\n' % method_count
		out += ' - %d static methods\n' % static_method_count
		out += ' - %d member\n' % member_count
		out += ' - %d static member\n' % static_member_count

		return out

	def __print_stats(self):  # pragma: no cover
		print(self.__get_stats())

	def output_linker_api(self):
		link_func = self.apply_api_prefix('link_binding')

		self._header += '''\
/*
	pass the get_c_type_info function from another binding to this function to resolve external types declared in this binding.
	you will need to write a wrapper to cast the type_info * pointer to the correct type if you are using a binding prefix.
	this function returns the number of unresolved external symbols.
*/
size_t %s(%s *(*get_c_type_info)(const char *));\n
''' % (link_func, self.apply_api_prefix('type_info'))

		self._source += '''\
size_t %s(%s *(*get_c_type_info)(const char *type)) {
	size_t unresolved = 0;\n
''' % (link_func, self.apply_api_prefix('type_info'))

		for extern_type in self._extern_types:
			self._source += '''\
	if (%s == nullptr) {
		if (%s *info = (*get_c_type_info)("%s")) {
			%s = info->check;
			%s = info->to_c;
			%s = info->from_c;
		} else {
			++unresolved;
		}
	}

''' % (
		extern_type.check_func,
		self.apply_api_prefix('type_info'),
		extern_type.ctype,
		extern_type.check_func,
		extern_type.to_c_func,
		extern_type.from_c_func
	)

		self._source += '''\
	return unresolved;
}

'''

	def finalize(self):
		# insert includes
		system_includes = ''
		if len(self.__system_includes) > 0:
			system_includes = ''.join(['#include <%s>\n' % path for path in self.__system_includes])

		user_includes = ''
		if len(self.__user_includes) > 0:
			user_includes = ''.join(['#include "%s"\n' % path for path in self.__user_includes])

		self._source = self._source.replace('{{{__WRAPPER_INCLUDES__}}}', system_includes + user_includes)

		# cast to
		self._source += self.get_type_tag_cast_function()
		self.bind_cast_functions()

		# commit all function declarations
		self.__commit_function_declarations()

		# statistics
		if self.verbose:  # pragma: no cover
			self.__print_stats()

		# extern types linker API
		self.output_linker_api()

	def get_output(self):
		return {
			'bind_%s.h' % self.get_language(): self._header,
			'bind_%s.cpp' % self.get_language(): self._source
		}

	def _build_protos(self, protos):
		return self.__prepare_protos(self.__expand_protos(protos))
