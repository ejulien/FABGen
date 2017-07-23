from pypeg2 import re, flag, name, Plain, optional, attr, K, parse, Keyword, Enum, List, csl
from collections import OrderedDict
import copy


#
def get_fully_qualified_ctype_name(ctype):
	out = ''
	if ctype.const:
		out += 'const '
	if ctype.signed:
		out += 'signed '
	if ctype.unsigned:
		out += 'unsigned '
	out += ctype.name
	if hasattr(ctype, 'template'):
		out += '<%s>' % ctype.template[0]
	if ctype.const_ref:
		out += ' const '
	if hasattr(ctype, 'ref'):
		out += ' ' + ctype.ref
	return out


def ref_to_string(ref):
	parts = []
	for e in ref:
		if ref == '*':
			parts.append('ptr')
		elif ref == '&':
			parts.append('ref')
	return '_'.join(parts)


def get_clean_ctype_name(ctype):
	parts = []

	if ctype.const:
		parts.append('const')
	if ctype.signed:
		parts.append('signed')
	if ctype.unsigned:
		parts.append('unsigned')

	parts.append(ctype.name.replace(':', '_'))

	if hasattr(ctype, 'template'):
		parts.append('of_%s' % get_clean_ctype_name(ctype.template[0]))
	if ctype.const_ref:
		parts.append('const')
	if hasattr(ctype, 'ref'):
		parts.append(ref_to_string(ctype.ref))

	return '_'.join(parts)


def get_ctype_default_bound_name(ctype):
	ctype = copy.deepcopy(ctype)
	ctype.name = ctype.name.split('::')[-1]  # strip namespace
	return get_clean_ctype_name(ctype)


def ctypes_to_string(ctypes):
	return ','.join([repr(ctype) for ctype in ctypes])


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
	name = name.split('::')[-1]  # strip namespace
	return get_clean_symbol_name(name)


#
typename = re.compile(r"((::)*(_|[A-z])[A-z0-9_]*)+")
ref_re = re.compile(r"[&*]+")


class _TemplateParameters(List):
	pass


class _CType:
	def __repr__(self):
		return get_fully_qualified_ctype_name(self)

	def get_ref(self, extra_transform=''):
		return (self.ref if hasattr(self, 'ref') else '') + extra_transform

	def add_ref(self, ref):
		t = copy.deepcopy(self)
		if hasattr(self, 'ref'):
			t.ref += ref
		else:
			setattr(t, 'ref', ref)
		return t

	def is_pointer(self):
		ref = self.get_ref()
		return ref == '*'

	def is_const(self):
		if self.get_ref() == '':
			return self.const
		return self.const_ref

	def const_storage(self):
		"""Return a CType suitable for R/W storage of const type values"""
		t = copy.deepcopy(self)
		if self.get_ref() == '':
			t.const = False
		else:
			t.const_ref = False
		return t

	def non_const(self):
		t = copy.deepcopy(self)
		t.const = False
		return t

	def ref_stripped(self):
		t = copy.deepcopy(self)
		if hasattr(t, 'ref'):
			delattr(t, 'ref')
		return t


_TemplateParameters.grammar = "<", optional(csl(_CType)), ">"
_CType.grammar = flag("const", K("const")), optional(flag("signed", K("signed"))), optional(flag("unsigned", K("unsigned"))), attr("name", typename), optional(attr("template", _TemplateParameters)), optional(attr("ref", ref_re)), flag("const_ref", K("const"))


#
def _prepare_ctypes(ctypes, template):
	if not type(ctypes) is type([]):
		ctypes = [ctypes]
	return [parse(type, template) for type in ctypes]


#
class _CArg:
	def __repr__(self):
		out = repr(self.ctype)
		if hasattr(self, 'name'):
			out += ' ' + str(self.name)
		return out


_CArg.grammar = attr("ctype", _CType), optional(name())


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
	return ctype_ref_to(from_ref, to_ref) + var


class TypeConverter:
	def __init__(self, type, storage_type=None, bound_name=None):
		self.ctype = parse(type, _CType)

		if not storage_type:
			self.storage_ctype = self.ctype.const_storage()
		else:
			self.storage_ctype = parse(storage_type, _CType)

		self.clean_name = get_clean_ctype_name(self.ctype)
		self.bound_name = get_ctype_default_bound_name(self.ctype) if bound_name is None else bound_name
		self.fully_qualified_name = get_fully_qualified_ctype_name(self.ctype)
		self.type_tag = 'type_tag_' + self.bound_name

		self.constructor = None
		self.members = []
		self.static_members = []
		self.methods = []
		self.static_methods = []
		self.arithmetic_ops = []
		self.comparison_ops = []

		self._non_copyable = False

		self._features = {}
		self._upcasts = []  # valid upcasts
		self._casts = []  # valid casts

	def get_operator(self, op):
		for arithmetic_op in self.arithmetic_ops:
			if arithmetic_op['op'] == op:
				return arithmetic_op

	def get_type_api(self, module_name):
		return ''

	def finalize_type(self):
		return ''

	def to_c_call(self, out_var, expr):
		assert 'to_c_call not implemented in converter'

	def from_c_call(self, out_var, expr, ownership):
		assert 'from_c_call not implemented in converter'

	def prepare_var_for_conv(self, var, var_ref):
		"""Prepare a variable for use with the converter from_c/to_c methods."""
		return transform_var_ref_to(var, var_ref, self.ctype.get_ref('*'))


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
	def output_header(self):
		common = "// This file is automatically generated, do not modify manually!\n\n"

		self._source += "// FABgen .cpp\n"
		self._source += common
		self._header += "// FABgen .h\n"
		self._header += common

	def output_includes(self):
		self.add_include('cstdint', True)

		self._source += '{{{__WRAPPER_INCLUDES__}}}\n'

	def start(self, name):
		self._name = name
		self._header, self._source = "", ""

		self.__system_includes, self.__user_includes = [], []

		self.__type_convs = {}

		self._bound_types = []  # list of bound types
		self._bound_functions = []  # list of bound functions

		self._custom_init_code = ""
		self._enums = {}

		self.output_header()
		self.output_includes()

		self._source += 'enum OwnershipPolicy { NonOwning, Copy, Owning };\n\n'
		self._source += 'void *_type_tag_cast(void *in_p, const char *in_type_tag, const char *out_type_tag);\n\n'

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

	def insert_binding_code(self, code, comment):
		self._source += '// %s\n' % comment
		self._source += code
		self._source += '\n'

	def add_custom_init_code(self, code):
		self._custom_init_code += code

	#
	def raise_exception(self, type, reason):
		assert 'raise_exception not implemented in generator'

	#
	def begin_type(self, conv, features):
		"""Declare a new type converter."""
		self._header += conv.get_type_api(self._name)

		self._source += '// %s type tag\n' % conv.fully_qualified_name
		self._source += 'static const char *%s = "%s";\n\n' % (conv.type_tag, conv.bound_name)
		self._source += conv.get_type_api(self._name)

		conv._features = features

		self._bound_types.append(conv)
		self.__type_convs[conv.fully_qualified_name] = conv

		feats = list(conv._features.values())
		for feat in feats:
			feat.init_type_converter(self, conv)  # init converter feature
		return conv

	def end_type(self, conv):
		self._source += conv.get_type_glue(self, self._name) + '\n'

	def bind_type(self, conv, features={}):
		self.begin_type(conv, features)
		self.end_type(conv)

	#
	def typedef(self, type, alias_of, storage_type=None):
		conv = copy.deepcopy(self.__type_convs[alias_of])

		default_storage_type = type if storage_type is None else storage_type

		conv.fully_qualified_name = type
		conv.ctype = parse(type, _CType)
		conv.storage_ctype = parse(default_storage_type, _CType)

		self.__type_convs[type] = conv

	#
	def bind_enum(self, name, symbols, storage_type='int', bound_name=None, prefix=''):
		self.typedef(name, storage_type)

		if bound_name is None:
			bound_name = get_symbol_default_bound_name(name)

		enum = {}
		for symbol in symbols:
			enum[prefix + symbol] = '%s::%s' % (name, symbol)

		self._enums[bound_name] = enum

	#
	def begin_class(self, type, converter_class=None, noncopyable=False, bound_name=None, features={}):
		"""Begin a class declaration."""
		if type in self.__type_convs:
			return self.__type_convs[type]  # type already declared

		default_storage_type = type + '*'

		conv = self.default_class_converter(type, default_storage_type, bound_name) if converter_class is None else converter_class(type, default_storage_type, bound_name)
		conv = self.begin_type(conv, features)

		conv._non_copyable = noncopyable

		return conv

	def end_class(self, conv):
		"""End a class declaration."""
		self.end_type(conv)

	#
	def decl_class(self, type, converter_class=None):
		"""Forward declare a class."""
		return self.begin_class(type, converter_class)

	#
	def bind_ptr(self, type, converter_class=None, bound_name=None):
		conv = self.default_ptr_converter(type, None, bound_name) if converter_class is None else converter_class(type, None, bound_name)
		self.bind_type(conv)
		return conv

	#
	def add_upcast(self, derived_conv, base_conv):
		derived_conv._upcasts.append(base_conv)

	def add_cast(self, src_conv, tgt_conv, cast_delegate):
		"""Declare a cast delegate from one type to another."""
		src_conv._casts.append((tgt_conv, cast_delegate))

	#
	def select_ctype_conv(self, ctype):
		"""Select a type converter."""
		type = get_fully_qualified_ctype_name(ctype)

		if type == 'void':
			return None

		if type in self.__type_convs:
			return self.__type_convs[type]

		non_const_type = get_fully_qualified_ctype_name(ctype.non_const())

		if non_const_type in self.__type_convs:
			return self.__type_convs[non_const_type]

		non_const_ref_stripped_type = get_fully_qualified_ctype_name(ctype.non_const().ref_stripped())

		if non_const_ref_stripped_type in self.__type_convs:
			return self.__type_convs[non_const_ref_stripped_type]

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
	def commit_rvals(self, rval, ctx):
		assert "missing return values template"

	#
	def __ref_to_ownership_policy(self, ctype):
		return 'Copy' if ctype.get_ref() == '' else 'NonOwning'

	# --
	def __prepare_protos(self, protos):
		"""Prepare a list of prototypes, select converter objects"""
		_protos = []

		for proto in protos:
			assert len(proto) == 3, "prototype incomplete. Expected 3 entries (type, [arguments], [features]), found %d" % len(proto)

			rval = parse(proto[0], _CType)
			_proto = {'rval': {'ctype': rval.const_storage(), 'conv': self.select_ctype_conv(rval)}, 'args': [], 'features': proto[2]}

			args = proto[1]
			if not type(args) is type([]):
				args = [args]

			for arg in args:
				assert ',' not in arg, "malformed argument, a comma was found in an argument when it should be a separate list entry"
				carg = parse(arg, _CArg)
				conv = self.select_ctype_conv(carg.ctype)
				_proto['args'].append({'carg': carg, 'conv': conv, 'check_var': None})

			_protos.append(_proto)

		return _protos

	def __assert_conv_feature(self, conv, feature):
		assert feature in conv._features, "Type converter for %s does not support the %s feature" % (conv.ctype, feature)

	def _prepare_c_arg_self(self, conv, out_var, ctx='none', features=[]):
		out = ''
		if 'proxy' in features:
			proxy = conv._features['proxy']

			out += '	' + self.decl_var(conv.storage_ctype, '%s_wrapped' % out_var)
			out += '	' + conv.to_c_call(self.get_self(ctx), '&%s_wrapped' % out_var)

			out += '	' + self.decl_var(proxy.wrapped_conv.storage_ctype, out_var)
			out += proxy.unwrap('%s_wrapped' % out_var, out_var)
		else:
			out += '	' + self.decl_var(conv.storage_ctype, out_var)
			out += '	' + conv.to_c_call(self.get_self(ctx), '&%s' % out_var)
		return out

	def _prepare_c_arg(self, idx, conv, var, ctx='default', features=[]):
		out = self.decl_var(conv.storage_ctype, var)
		out += conv.to_c_call(self.get_arg(idx, ctx), '&%s' % var)
		return out

	def prepare_c_rval(self, conv, ctype, var, ownership=None):
		if ownership is None:
			ownership = self.__ref_to_ownership_policy(ctype)
		# transform from {T&, T*, T**, ...} to T* where T is conv.ctype
		expr = transform_var_ref_to(var, ctype.get_ref(), conv.ctype.add_ref('*').get_ref())
		return self.rval_from_c_ptr(conv, var, expr, ownership)

	def __proto_call(self, self_conv, proto, expr_eval, ctx, fixed_arg_count=None):
		features = proto['features']

		enable_proxy = 'proxy' in features
		if enable_proxy:
			assert ctx != 'function', "Proxy feature cannot be used for a function call"

			if self_conv is not None:
				self.__assert_conv_feature(self_conv, 'proxy')

		rval = proto['rval']['ctype']
		rval_conv = proto['rval']['conv']

		# prepare C call self argument
		if self_conv:
			if ctx in ['getter', 'setter', 'method', 'arithmetic_op', 'inplace_arithmetic_op', 'comparison_op']:
				self._source += self._prepare_c_arg_self(self_conv, '_self', ctx, features)

		# prepare C call arguments
		args = proto['args']
		c_call_args = []

		for idx, arg in enumerate(args):
			conv = arg['conv']
			if not conv:
				continue

			arg_name = 'arg%d' % idx
			self._source += self._prepare_c_arg(idx, conv, arg_name, ctx, features)

			c_call_arg_transform = ctype_ref_to(conv.storage_ctype.get_ref(), arg['carg'].ctype.get_ref())
			c_call_args.append(c_call_arg_transform + arg_name)

		# declare return value
		if ctx == 'constructor':
			rval_ptr = rval.add_ref('*')  # constructor returns a pointer

			if enable_proxy:
				proxy = rval_conv._features['proxy']

				self._source += self.decl_var(proxy.wrapped_conv.ctype.add_ref('*'), 'rval_raw', ' = ')
				self._source += 'new %s(%s);\n' % (proxy.wrapped_conv.ctype, ', '.join(c_call_args))

				self._source += self.decl_var(rval_ptr, 'rval')
				self._source += proxy.wrap('rval_raw', 'rval')
			else:
				self._source += self.decl_var(rval_ptr, 'rval', ' = ')
				self._source += 'new %s(%s);\n' % (rval, ', '.join(c_call_args))

			self._source += self.prepare_c_rval(rval_conv, rval_ptr, 'rval', 'Owning')  # constructor output is always owned by VM
		else:
			# return value is optional for a function call
			if rval_conv:
				self._source += self.decl_var(rval, 'rval', ' = ')

			self._source += expr_eval(c_call_args) + '\n'

			if rval_conv:
				self._source += self.prepare_c_rval(rval_conv, rval, 'rval')

		self._source += self.commit_rvals(rval, ctx)

	def __bind_proxy(self, name, self_conv, protos, desc, expr_eval, ctx, fixed_arg_count=None):
		protos = self.__prepare_protos(protos)

		# categorize prototypes by number of argument they take
		def get_protos_per_arg_count(protos):
			by_arg_count = {}
			for proto in protos:
				arg_count = len(proto['args'])
				if arg_count not in by_arg_count:
					by_arg_count[arg_count] = []
				by_arg_count[arg_count].append(proto)
			return by_arg_count

		protos_by_arg_count = get_protos_per_arg_count(protos)

		# prepare proxy function
		self.insert_code('// %s\n' % desc, True, False)

		max_arg_count = max(protos_by_arg_count.keys())

		self.open_proxy(name, max_arg_count, ctx)

		# output dispatching logic
		def get_protos_per_arg_conv(protos, arg_idx):
			per_arg_conv = {}
			for proto in protos:
				arg_conv = proto['args'][arg_idx]['conv']
				if arg_conv not in per_arg_conv:
					per_arg_conv[arg_conv] = []
				per_arg_conv[arg_conv].append(proto)
			return per_arg_conv
			

		has_fixed_argc = fixed_arg_count is not None

		if has_fixed_argc:
			assert len(protos_by_arg_count) == 1 and fixed_arg_count in protos_by_arg_count

		for arg_count, protos_with_arg_count in protos_by_arg_count.items():
			if not has_fixed_argc:
				self._source += '	if (arg_count == %d) {\n' % arg_count

			def output_arg_check_and_dispatch(protos, arg_idx, arg_limit):
				indent = '	' * (arg_idx+(2 if not has_fixed_argc else 1))

				if arg_idx == arg_limit:
					assert len(protos) == 1  # there should only be exactly one prototype with a single signature
					self.__proto_call(self_conv, protos[0], expr_eval, ctx, fixed_arg_count)
					return

				protos_per_arg_conv = get_protos_per_arg_conv(protos, arg_idx)

				self._source += indent
				for conv, protos_for_conv in protos_per_arg_conv.items():
					self._source += 'if (%s) {\n' % conv.check_call(self.get_arg(arg_idx, ctx))
					output_arg_check_and_dispatch(protos_for_conv, arg_idx+1, arg_limit)
					self._source += indent + '} else '

				self._source += '{\n'

				expected_types = []
				for proto in protos:
					proto_arg = proto['args'][arg_idx]

					proto_arg_name = str(proto_arg['carg'].name)
					proto_arg_bound_name = proto_arg['conv'].bound_name

					expected_types.append('%s %s' % (proto_arg_bound_name, proto_arg_name))

				self.set_error('runtime', 'incorrect type for argument %d to %s, expected %s' % (arg_idx+1, desc, format_list_for_comment(expected_types)))
				self._source += indent + '}\n'

			output_arg_check_and_dispatch(protos_with_arg_count, 0, arg_count)

			if not has_fixed_argc:
				self._source += '	} else '

		if not has_fixed_argc:
			self._source += '{\n'
			self.set_error('runtime', 'incorrect number of arguments to %s' % desc)
			self._source += '	}\n'

		#
		self.close_proxy(ctx)
		self._source += '\n'

	#
	def bind_function(self, name, rval, args, features=[], bound_name=None):
		self.bind_function_overloads(name, [(rval, args, features)], bound_name)

	def bind_function_overloads(self, name, protos, bound_name=None):
		expr_eval = lambda args: '%s(%s);' % (name, ', '.join(args))
		if bound_name is None:
			bound_name = get_symbol_default_bound_name(name)
		proxy_name = 'py_' + bound_name
		self.__bind_proxy(proxy_name, None, protos, 'function %s' % bound_name, expr_eval, 'function')

		self._bound_functions.append({'name': name, 'bound_name': bound_name, 'proxy_name': proxy_name, 'protos': protos})

	#
	def bind_constructor(self, conv, args, features=[]):
		self.bind_constructor_overloads(conv, [(args, features)])

	def bind_constructor_overloads(self, conv, proto_args):
		type = conv.fully_qualified_name

		expr_eval = lambda args: 'new %s(%s);' % (type, ', '.join(args))
		protos = [(type, args[0], args[1]) for args in proto_args]
		proxy_name = 'py_construct_' + conv.bound_name
		self.__bind_proxy(proxy_name, conv, protos, '%s constructor' % conv.bound_name, expr_eval, 'constructor')

		conv.constructor = {'proxy_name': proxy_name, 'protos': protos}

	#
	def bind_method(self, conv, name, rval, args, features=[], bound_name=None):
		self.bind_method_overloads(conv, name, [(rval, args, features)], bound_name)

	def bind_method_overloads(self, conv, name, protos, bound_name=None):
		expr_eval = lambda args: '_self->%s(%s);' % (name, ', '.join(args))
		if bound_name is None:
			bound_name = get_symbol_default_bound_name(name)
		proxy_name = 'py_method_%s_of_%s' % (bound_name, conv.bound_name)
		self.__bind_proxy(proxy_name, conv, protos, 'method %s of %s' % (bound_name, conv.bound_name), expr_eval, 'method')

		conv.methods.append({'name': name, 'bound_name': bound_name, 'proxy_name': proxy_name, 'protos': protos})

	#
	def bind_static_method(self, conv, name, rval, args, features=[], bound_name=None):
		self.bind_static_method_overloads(conv, name, [(rval, args, features)], bound_name)

	def bind_static_method_overloads(self, conv, name, protos, bound_name=None):
		expr_eval = lambda args: '%s::%s(%s);' % (conv.fully_qualified_name, name, ', '.join(args))
		if bound_name is None:
			bound_name = get_symbol_default_bound_name(name)
		proxy_name = 'py_static_method_%s_of_%s' % (bound_name, conv.bound_name)
		self.__bind_proxy(proxy_name, conv, protos, 'static method %s of %s' % (bound_name, conv.bound_name), expr_eval, 'static_method')

		conv.static_methods.append({'name': name, 'bound_name': bound_name, 'proxy_name': proxy_name, 'protos': protos})

	#
	def bind_member(self, conv, member, features=[]):
		arg = parse(member, _CArg)

		# getter must go through a pointer or reference so that the enclosing object copy is modified
		getter_ctype = arg.ctype
		if getter_ctype.get_ref() == '':
			getter_ctype = getter_ctype.add_ref('*')

		expr_eval = lambda args: '&_self->%s;' % arg.name
		getter_protos = [(get_fully_qualified_ctype_name(getter_ctype), [], features)]
		getter_proxy_name = 'py_get_%s_of_%s' % (get_symbol_default_bound_name(arg.name), conv.bound_name)
		self.__bind_proxy(getter_proxy_name, conv, getter_protos, 'get member %s of %s' % (arg.name, conv.bound_name), expr_eval, 'getter', 0)

		# setter
		if not arg.ctype.is_const():
			expr_eval = lambda args: '_self->%s = %s;' % (arg.name, args[0])
			setter_protos = [('void', [member], features)]
			setter_proxy_name = 'py_set_%s_of_%s' % (get_symbol_default_bound_name(arg.name), conv.bound_name)
			self.__bind_proxy(setter_proxy_name, conv, setter_protos, 'set member %s of %s' % (arg.name, conv.bound_name), expr_eval, 'setter', 1)
		else:
			setter_proxy_name = None

		conv.members.append({'name': arg.name, 'getter': getter_proxy_name, 'setter': setter_proxy_name})

	def bind_members(self, conv, members, features=[]):
		for member in members:
			self.bind_member(conv, member, features)

	#
	def bind_static_member(self, conv, member, features=[]):
		arg = parse(member, _CArg)

		# getter must go through a pointer or reference so that the enclosing object copy is modified
		getter_ctype = arg.ctype
		if getter_ctype.get_ref() == '':
			getter_ctype = getter_ctype.add_ref('&')

		if 'proxy' in features:
			self.__assert_conv_feature(conv, 'proxy')
			expr_eval = lambda args: '%s::%s;' % (conv._features['proxy'].wrapped_conv.fully_qualified_name, arg.name)
		else:
			expr_eval = lambda args: '%s::%s;' % (conv.fully_qualified_name, arg.name)

		getter_protos = [(get_fully_qualified_ctype_name(getter_ctype), [], features)]
		getter_proxy_name = 'py_get_%s_of_%s' % (get_symbol_default_bound_name(arg.name), conv.bound_name)
		self.__bind_proxy(getter_proxy_name, None, getter_protos, 'get static member %s of %s' % (arg.name, conv.bound_name), expr_eval, 'getter', 0)

		# setter
		if not arg.ctype.is_const():
			expr_eval = lambda args: '%s::%s = %s;' % (conv.fully_qualified_name, arg.name, args[0])
			setter_protos = [('void', [member], features)]
			setter_proxy_name = 'py_set_%s_of_%s' % (get_symbol_default_bound_name(arg.name), conv.bound_name)
			self.__bind_proxy(setter_proxy_name, None, setter_protos, 'set static member %s of %s' % (arg.name, conv.bound_name), expr_eval, 'setter', 1)
		else:
			setter_proxy_name = None

		conv.static_members.append({'name': arg.name, 'getter': getter_proxy_name, 'setter': setter_proxy_name})

	def bind_static_members(self, conv, members, features=[]):
		for member in members:
			self.bind_static_member(conv, member, features)

	#
	def bind_arithmetic_op(self, conv, op, rval, args, features=[]):
		self.bind_arithmetic_op_overloads(conv, op, [(rval, args, features)])

	def bind_arithmetic_op_overloads(self, conv, op, protos):
		assert op in ['-', '+', '*', '/'], 'Unsupported arithmetic operator ' + op

		expr_eval = lambda args: '*_self %s %s;' % (op, ', '.join(args))
		proxy_name = 'py_%s_operator_of_%s' % (get_clean_symbol_name(op), conv.bound_name)
		self.__bind_proxy(proxy_name, conv, protos, '%s operator of %s' % (op, conv.bound_name), expr_eval, 'arithmetic_op', 1)

		conv.arithmetic_ops.append({'op': op, 'proxy_name': proxy_name})

	def bind_arithmetic_ops(self, conv, ops, rval, args, features=[]):
		for op in ops:
			self.bind_arithmetic_op(conv, op, rval, args, features)

	def bind_arithmetic_ops_overloads(self, conv, ops, protos):
		for op in ops:
			self.bind_arithmetic_op_overloads(conv, op, protos)

	#
	def bind_inplace_arithmetic_op(self, conv, op, args, features=[]):
		self.bind_inplace_arithmetic_op_overloads(conv, op, [args, features])

	def bind_inplace_arithmetic_op_overloads(self, conv, op, args):
		assert op in ['-=', '+=', '*=', '/='], 'Unsupported inplace arithmetic operator ' + op

		expr_eval = lambda args: '*_self %s %s;' % (op, ', '.join(args))
		proxy_name = 'py_%s_operator_of_%s' % (get_clean_symbol_name(op), conv.bound_name)
		protos = [('void', arg[0], arg[1]) for arg in args]
		self.__bind_proxy(proxy_name, conv, protos, '%s operator of %s' % (op, conv.bound_name), expr_eval, 'inplace_arithmetic_op', 1)

		conv.arithmetic_ops.append({'op': op, 'proxy_name': proxy_name})

	def bind_inplace_arithmetic_ops(self, conv, ops, args, features=[]):
		for op in ops:
			self.bind_inplace_arithmetic_op(conv, op, args, features)

	def bind_inplace_arithmetic_ops_overloads(self, conv, ops, args):
		for op in ops:
			self.bind_inplace_arithmetic_op_overloads(conv, op, args)

	#
	def bind_comparison_op(self, conv, op, args, features=[]):
		self.bind_comparison_op_overloads(conv, op, [args, features])

	def bind_comparison_op_overloads(self, conv, op, args):
		assert op in ['<', '<=', '==', '!=', '>', '>='], 'Unsupported comparison operator ' + op

		expr_eval = lambda args: '*_self %s %s;' % (op, ', '.join(args[0]))
		proxy_name = 'py_%s_operator_of_%s' % (get_clean_symbol_name(op), conv.bound_name)
		protos = [('bool', arg[0], arg[1]) for arg in args]
		self.__bind_proxy(proxy_name, conv, protos, '%s operator of %s' % (op, conv.bound_name), expr_eval, 'comparison_op', 1)

		conv.comparison_ops.append({'op': op, 'proxy_name': proxy_name})

	def bind_comparison_ops(self, conv, ops, rval, args, features=[]):
		for op in ops:
			self.bind_comparison_op(conv, op, rval, args, features)

	def bind_comparison_ops_overloads(self, conv, ops, protos):
		for op in ops:
			self.bind_comparison_op_overloads(conv, op, protos)

	#
	def output_summary(self):
		self._source += '// Bound %d global functions:\n' % len(self._bound_functions)
		for f in self._bound_functions:
			self._source += '//	- %s bound as %s\n' % (f['name'], f['bound_name'])
		self._source += '\n'

	def get_type_tag_cast_function(self):
		downcasts = {}
		for type in self._bound_types:
			downcasts[type] = []

		def register_upcast(type, upcasts):
			for base in upcasts:
				downcasts[base].append(type)
				register_upcast(type, base._upcasts)

		for type in self._bound_types:
			register_upcast(type, type._upcasts)

		#
		out = '''\
// type_tag based cast system
void *_type_tag_cast(void *in_p, const char *in_type_tag, const char *out_type_tag) {
	if (out_type_tag == in_type_tag)
		return in_p;

	void *out_p = NULL;

	// upcast
'''

		i = 0
		for base in self._bound_types:
			if len(downcasts[base]) == 0:
				continue

			out += '	' if i == 0 else ' else '
			out += 'if (out_type_tag == %s) {\n' % base.type_tag

			for j, downcast in enumerate(downcasts[base]):
				out += '		' if j == 0 else '		else '
				out += 'if (in_type_tag == %s)\n' % downcast.type_tag
				out += '			out_p = (%s *)((%s *)in_p);\n' % (get_fully_qualified_ctype_name(base.ctype), get_fully_qualified_ctype_name(downcast.ctype))

			out += '	}\n'
			i += 1

		out += '''
	if (out_p)
		return out_p;

	// additional casts
'''

		i = 0
		for conv in self._bound_types:
			if len(conv._casts) == 0:
				continue

			out += '	' if i == 0 else ' else '
			out += 'if (in_type_tag == %s) {\n' % conv.type_tag

			for j, cast in enumerate(conv._casts):
				out += 'if (out_type_tag == %s) {\n' % cast[0].type_tag
				out += cast[1]('in_p', 'out_p')
				out += '}\n'

			out += '}\n'
			i += 1

		out += '''

	return out_p;
}\n\n'''
		return out

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

	def get_output(self):
		return self._header, self._source
