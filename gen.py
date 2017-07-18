from pypeg2 import re, flag, name, Plain, optional, attr, K, parse, Keyword, Enum, List, csl
from collections import OrderedDict
import copy


#
typename = re.compile(r"((::)*(_|[A-z])[A-z0-9_]*)+")
ref_re = re.compile(r"[&*]+")


def get_fully_qualified_ctype_name(type):
	out = ''
	if type.const:
		out += 'const '
	out += type.unqualified_name
	if hasattr(type, 'template'):
		out += '<%s>' % type.template[0]
	if hasattr(type, 'ref'):
		out += ' ' + type.ref
	return out


type_clean_rules = OrderedDict()

type_clean_rules['::'] = '__'  # namespace

type_clean_rules['+='] = 'inplace_add'
type_clean_rules['*='] = 'inplace_mul'
type_clean_rules['/='] = 'inplace_div'
type_clean_rules['-='] = 'inplace_sub'

type_clean_rules['+'] = 'add'
type_clean_rules['*'] = 'mul'
type_clean_rules['/'] = 'div'
type_clean_rules['-'] = 'sub'

type_clean_rules['*'] = 'ptr'  # pointer
type_clean_rules['&'] = '_r'  # reference

type_clean_rules['<'] = 'lt'
type_clean_rules['<='] = 'le'
type_clean_rules['=='] = 'eq'
type_clean_rules['!='] = 'ne'
type_clean_rules['>'] = 'gt'
type_clean_rules['>='] = 'ge'


def get_type_clean_name(type):
	""" Return a type name cleaned so that it may be used as variable name in the generator output."""
	parts = type.split(' ')

	def clean_type_name_part(part):
		for f_o, f_d in type_clean_rules.items():
			part = part.replace(f_o, f_d)
		return part

	parts = [clean_type_name_part(part) for part in parts]
	return '_'.join(parts)


def ctypes_to_string(ctypes):
	return ','.join([repr(ctype) for ctype in ctypes])


class _TemplateParameters(List):
	grammar = "<", optional(csl(typename)), ">"


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

	def non_const(self):
		t = copy.deepcopy(self)
		if self.get_ref() == '':
			t.const = False
		else:
			t.const_ref = False
		return t


_CType.grammar = flag("const", K("const")), optional([flag("signed", K("signed")), flag("unsigned", K("unsigned"))]), attr("unqualified_name", typename), optional(attr("template", _TemplateParameters)), optional(attr("ref", ref_re)), flag("const_ref", K("const"))


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


def get_type_bound_name(type):
	return type.split('::')[-1]


class TypeConverter:
	def __init__(self, type, storage_type=None):
		self.ctype = parse(type, _CType)

		if not storage_type:
			self.storage_ctype = self.ctype.non_const()
		else:
			self.storage_ctype = parse(storage_type, _CType)

		self.clean_name = get_type_clean_name(type)
		self.bound_name = get_type_bound_name(type)
		self.fully_qualified_name = get_fully_qualified_ctype_name(self.ctype)
		self.type_tag = '__%s_type_tag' % self.clean_name

		self.constructor = None
		self.members = []
		self.static_members = []
		self.methods = []
		self.static_methods = []
		self.arithmetic_ops = []
		self.comparison_ops = []

		self._non_copyable = False

		self.bases = []  # type derives from the following types

	def get_operator(self, op):
		for arithmetic_op in self.arithmetic_ops:
			if arithmetic_op['op'] == op:
				return arithmetic_op

	def get_type_api(self, module_name):
		return ''

	def finalize_type(self):
		return ''

	def to_c_call(self, out_var, in_var_p):
		assert 'to_c_call not implemented in converter'

	def from_c_call(self, ctype, out_var, in_var_p):
		assert 'from_c_call not implemented in converter'

	def prepare_var_for_conv(self, var, var_ref):
		"""Prepare a variable for use with the converter from_c/to_c methods."""
		return transform_var_ref_to(var, var_ref, self.ctype.get_ref('*'))

	def get_all_methods(self):
		"""Return a list of all the type methods (including inherited methods)."""
		all_methods = copy.copy(self.methods)

		def collect_base_methods(base):
			for method in base.methods:
				if not any(m['name'] == method['name'] for m in all_methods):
					all_methods.append(method)

			for _base in base.bases:
				collect_base_methods(_base)

		for base in self.bases:
			collect_base_methods(base)

		return all_methods

	def can_upcast_to(self, type):
		clean_name = get_type_clean_name(type)

		if self.clean_name == clean_name:
			return True

		for base in self.bases:
			if base.can_upcast_to(type):
				return True

		return False


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
		self.__function_templates = {}

		self._bound_types = []  # list of bound types
		self._bound_functions = []  # list of bound functions

		self.output_header()
		self.output_includes()

		self._source += 'enum OwnershipPolicy { NonOwning, Copy, Owning };\n\n'
		self._source += 'void *_type_tag_upcast(void *in_p, const char *in_type_tag, const char *out_type_tag);\n\n'

		self._custom_init_code = ""

	def add_include(self, path, is_system_include = False):
		if is_system_include:
			self.__system_includes.append(path)
		else:
			self.__user_includes.append(path)

	def insert_code(self, code, in_source=True, in_header=True):
		if in_header:
			self._header += code
		if in_source:
			self._source += code

	def add_custom_init_code(self, code):
		self._custom_init_code += code

	#
	def raise_exception(self, type, reason):
		assert 'raise_exception not implemented in generator'

	#
	def begin_type(self, conv):
		"""Declare a new type converter."""
		self._header += conv.get_type_api(self._name)

		self._source += '// %s type tag\n' % conv.fully_qualified_name
		self._source += 'static const char *%s = "%s";\n\n' % (conv.type_tag, conv.fully_qualified_name)
		self._source += conv.get_type_api(self._name)

		self._bound_types.append(conv)
		self.__type_convs[conv.fully_qualified_name] = conv
		return conv

	def end_type(self, conv):
		self._source += conv.get_type_glue(self._name) + '\n'

	def bind_type(self, conv):
		self.begin_type(conv)
		self.end_type(conv)

	#
	def begin_class(self, type, converter_class=None, noncopyable=False):
		"""Begin a class declaration."""
		if type in self.__type_convs:
			return self.__type_convs[type]  # type already declared

		conv = self.default_class_converter(type) if converter_class is None else converter_class(type)
		conv = self.begin_type(conv)

		conv._non_copyable = noncopyable

		return conv

	def end_class(self, type):
		"""End a class declaration."""
		self.end_type(self.__type_convs[type])

	def decl_class(self, type, converter_class=None):
		"""Forward declare a class."""
		return self.begin_class(type, converter_class)

	#
	def add_class_base(self, type, base):
		conv = self.__type_convs[type]
		base_conv = self.__type_convs[base]
		conv.bases.append(base_conv)

	#
	def select_ctype_conv(self, ctype):
		"""Select a type converter."""
		full_qualified_ctype_name = get_fully_qualified_ctype_name(ctype)

		if full_qualified_ctype_name == 'void':
			return None

		if full_qualified_ctype_name in self.__type_convs:
			return self.__type_convs[full_qualified_ctype_name]

		err_msg = "No converter for type %s" % ctype.unqualified_name
		assert ctype.unqualified_name in self.__type_convs, err_msg

		return self.__type_convs[ctype.unqualified_name]

	#
	def decl_var(self, ctype, name, end_of_expr=';\n'):
		return '%s %s%s' % (get_fully_qualified_ctype_name(ctype), name, end_of_expr)

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
			rval = parse(proto[0], _CType)
			_proto = {'rval': {'ctype': rval.non_const(), 'conv': self.select_ctype_conv(rval)}, 'args': []}

			args = proto[1]
			if not type(args) is type([]):
				args = [args]

			for arg in args:
				carg = parse(arg, _CArg)
				conv = self.select_ctype_conv(carg.ctype)
				_proto['args'].append({'carg': carg, 'conv': conv, 'check_var': None})

			_protos.append(_proto)

		return _protos

	def __proto_call(self, self_conv, proto, expr_eval, ctx, fixed_arg_count=None):
		rval = proto['rval']['ctype']
		rval_conv = proto['rval']['conv']

		# prepare C call self argument
		if self_conv:
			if ctx in ['getter', 'setter', 'method', 'arithmetic_op', 'inplace_arithmetic_op', 'comparison_op']:
				self._source += '	' + self.decl_var(self_conv.storage_ctype, '_self')
				self._source += '	' + self_conv.to_c_call(self.get_self(ctx), '&_self')

		# prepare C call arguments
		args = proto['args']
		c_call_args = []

		for idx, arg in enumerate(args):
			conv = arg['conv']
			if not conv:
				continue

			arg_name = 'arg%d' % idx
			self._source += self.decl_var(conv.storage_ctype, arg_name)
			self._source += conv.to_c_call(self.get_arg(idx, ctx), '&' + arg_name)

			c_call_arg_transform = ctype_ref_to(conv.storage_ctype.get_ref(), arg['carg'].ctype.get_ref())
			c_call_args.append(c_call_arg_transform + arg_name)

		# declare return value
		if ctx == 'constructor':
			rval = rval.add_ref('*')  # constructor returns a pointer
			self._source += self.decl_var(rval, 'rval', ' = ')
			self._source += expr_eval(c_call_args) + '\n'

			ownership = 'Owning'  # constructor output is owned by VM
			self.rval_from_c_ptr(rval, 'rval', rval_conv, ctype_ref_to(rval.get_ref(), rval_conv.ctype.get_ref() + '*') + 'rval', ownership)
		else:
			# return value is optional for a function call
			if rval_conv:
				self._source += self.decl_var(rval, 'rval', ' = ')

			self._source += expr_eval(c_call_args) + '\n'

			if rval_conv:
				ownership = self.__ref_to_ownership_policy(rval)
				self.rval_from_c_ptr(rval, 'rval', rval_conv, ctype_ref_to(rval.get_ref(), rval_conv.ctype.get_ref() + '*') + 'rval', ownership)

		self.commit_rvals(rval, ctx)

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
					proto_arg_type_name = proto_arg['conv'].bound_name

					expected_types.append('%s %s' % (proto_arg_type_name, proto_arg_name))

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
	def bind_function(self, name, rval, args):
		self.bind_function_overloads(name, [(rval, args)])

	def bind_function_overloads(self, name, protos):
		expr_eval = lambda args: '%s(%s);' % (name, ', '.join(args))
		proxy_name = get_type_clean_name('_%s__' % name)
		self.__bind_proxy(proxy_name, None, protos, 'function %s' % name, expr_eval, 'function')

		bound_name = get_type_bound_name(name)
		self._bound_functions.append({'name': name, 'bound_name': bound_name, 'proxy_name': proxy_name, 'protos': protos})

	#
	def bind_constructor(self, type, args):
		self.bind_constructor_overloads(type, [args])

	def bind_constructor_overloads(self, type, proto_args):
		self_conv = self.select_ctype_conv(parse(type, _CType))

		expr_eval = lambda args: 'new %s(%s);' % (type, ', '.join(args))
		protos = [(type, args) for args in proto_args]
		proxy_name = get_type_clean_name('_%s__constructor__' % type)
		self.__bind_proxy(proxy_name, self_conv, protos, '%s constructor' % self_conv.bound_name, expr_eval, 'constructor')

		self_conv.constructor = {'proxy_name': proxy_name, 'protos': protos}

	#
	def bind_method(self, type, name, rval, args):
		self.bind_method_overloads(type, name, [(rval, args)])

	def bind_method_overloads(self, type, name, protos):
		self_conv = self.select_ctype_conv(parse(type, _CType))

		expr_eval = lambda args: '_self->%s(%s);' % (name, ', '.join(args))
		proxy_name = get_type_clean_name('_%s__%s__' % (type, name))
		self.__bind_proxy(proxy_name, self_conv, protos, 'method %s of %s' % (name, self_conv.bound_name), expr_eval, 'method')

		self_conv.methods.append({'name': name, 'proxy_name': proxy_name, 'protos': protos})

	#
	def bind_member(self, type, member):
		self_conv = self.select_ctype_conv(parse(type, _CType))
		arg = parse(member, _CArg)

		# getter must go through a pointer or reference so that the enclosing object copy is modified
		getter_ctype = arg.ctype
		if getter_ctype.get_ref() == '':
			getter_ctype = getter_ctype.add_ref('&')

		expr_eval = lambda args: '_self->%s;' % arg.name
		getter_protos = [(get_fully_qualified_ctype_name(getter_ctype), [])]
		getter_proxy_name = get_type_clean_name('_%s__get_%s__' % (type, arg.name))
		self.__bind_proxy(getter_proxy_name, self_conv, getter_protos, 'get member %s of %s' % (arg.name, self_conv.bound_name), expr_eval, 'getter', 0)

		# setter
		if not arg.ctype.is_const():
			expr_eval = lambda args: '_self->%s = %s;' % (arg.name, args[0])
			setter_protos = [('void', [member])]
			setter_proxy_name = get_type_clean_name('_%s__set_%s__' % (type, arg.name))
			self.__bind_proxy(setter_proxy_name, self_conv, setter_protos, 'set member %s of %s' % (arg.name, self_conv.bound_name), expr_eval, 'setter', 1)
		else:
			setter_proxy_name = None

		self_conv.members.append({'name': arg.name, 'getter': getter_proxy_name, 'setter': setter_proxy_name})

	def bind_members(self, type, members):
		for member in members:
			self.bind_member(type, member)

	#
	def bind_static_member(self, type, member):
		self_conv = self.select_ctype_conv(parse(type, _CType))
		arg = parse(member, _CArg)

		# getter must go through a pointer or reference so that the enclosing object copy is modified
		getter_ctype = arg.ctype
		if getter_ctype.get_ref() == '':
			getter_ctype = getter_ctype.add_ref('&')

		expr_eval = lambda args: '%s::%s;' % (self_conv.fully_qualified_name, arg.name)
		getter_protos = [(get_fully_qualified_ctype_name(getter_ctype), [])]
		getter_proxy_name = get_type_clean_name('_%s__get_%s__' % (type, arg.name))
		self.__bind_proxy(getter_proxy_name, None, getter_protos, 'get static member %s of %s' % (arg.name, self_conv.bound_name), expr_eval, 'getter', 0)

		# setter
		if not arg.ctype.is_const():
			expr_eval = lambda args: '%s::%s = %s;' % (self_conv.fully_qualified_name, arg.name, args[0])
			setter_protos = [('void', [member])]
			setter_proxy_name = get_type_clean_name('_%s__set_%s__' % (type, arg.name))
			self.__bind_proxy(setter_proxy_name, None, setter_protos, 'set static member %s of %s' % (arg.name, self_conv.bound_name), expr_eval, 'setter', 1)
		else:
			setter_proxy_name = None

		self_conv.static_members.append({'name': arg.name, 'getter': getter_proxy_name, 'setter': setter_proxy_name})

	#
	def bind_arithmetic_op(self, type, op, rval, args):
		self.bind_arithmetic_op_overloads(type, op, [(rval, args)])

	def bind_arithmetic_op_overloads(self, type, op, protos):
		assert op in ['-', '+', '*', '/']
		self_conv = self.select_ctype_conv(parse(type, _CType))

		expr_eval = lambda args: '*_self %s %s;' % (op, ', '.join(args))
		proxy_name = get_type_clean_name('_%s__%s_operator__' % (type, op))
		self.__bind_proxy(proxy_name, self_conv, protos, '%s operator of %s' % (op, self_conv.bound_name), expr_eval, 'arithmetic_op', 1)

		self_conv.arithmetic_ops.append({'op': op, 'proxy_name': proxy_name})

	def bind_arithmetic_ops(self, type, ops, rval, args):
		for op in ops:
			self.bind_arithmetic_op(type, op, rval, args)

	def bind_arithmetic_ops_overloads(self, type, ops, protos):
		for op in ops:
			self.bind_arithmetic_op_overloads(type, op, protos)

	#
	def bind_inplace_arithmetic_op(self, type, op, args):
		self.bind_inplace_arithmetic_op_overloads(type, op, [args])

	def bind_inplace_arithmetic_op_overloads(self, type, op, args):
		assert op in ['-=', '+=', '*=', '/=']
		self_conv = self.select_ctype_conv(parse(type, _CType))

		expr_eval = lambda args: '*_self %s %s;' % (op, ', '.join(args))
		proxy_name = get_type_clean_name('_%s__%s_operator__' % (type, op))
		protos = [('void', arg) for arg in args]
		self.__bind_proxy(proxy_name, self_conv, protos, '%s operator of %s' % (op, self_conv.bound_name), expr_eval, 'inplace_arithmetic_op', 1)

		self_conv.arithmetic_ops.append({'op': op, 'proxy_name': proxy_name})

	def bind_inplace_arithmetic_ops(self, type, ops, args):
		for op in ops:
			self.bind_inplace_arithmetic_op(type, op, args)

	def bind_inplace_arithmetic_ops_overloads(self, type, ops, args):
		for op in ops:
			self.bind_inplace_arithmetic_op_overloads(type, op, args)

	#
	def bind_comparison_op(self, type, op, args):
		self.bind_comparison_op_overloads(type, op, [args])

	def bind_comparison_op_overloads(self, type, op, args):
		assert op in ['<', '<=', '==', '!=', '>', '>=']
		self_conv = self.select_ctype_conv(parse(type, _CType))

		expr_eval = lambda args: '*_self %s %s;' % (op, ', '.join(args))
		proxy_name = get_type_clean_name('_%s__%s_operator__' % (type, op))
		protos = [('bool', arg) for arg in args]
		self.__bind_proxy(proxy_name, self_conv, protos, '%s operator of %s' % (op, self_conv.bound_name), expr_eval, 'comparison_op', 1)

		self_conv.comparison_ops.append({'op': op, 'proxy_name': proxy_name})

	def bind_comparison_ops(self, type, ops, rval, args):
		for op in ops:
			self.bind_comparison_op(type, op, rval, args)

	def bind_comparison_ops_overloads(self, type, ops, protos):
		for op in ops:
			self.bind_comparison_op_overloads(type, op, protos)

	# global function template
	def decl_function_template(self, tmpl_name, tmpl_args, rval, args):
		self.__function_templates[tmpl_name] = {'tmpl_args': tmpl_args, 'rval': rval, 'args': args}

	def bind_function_template(self, tmpl_name, bound_name, bind_args):
		tmpl = self.__function_templates[tmpl_name]
		tmpl_args = tmpl['tmpl_args']

		assert len(tmpl_args) == len(bind_args)

		def bind_tmpl_arg(arg):
			return bind_args[tmpl_args.index(arg)] if arg in tmpl_args else arg

		bound_rval = bind_tmpl_arg(tmpl['rval'])
		bound_args = [bind_tmpl_arg(arg) for arg in tmpl['args']]

		bound_named_args = ['%s arg%d' % (arg, idx) for idx, arg in enumerate(bound_args)]

		# output wrapper
		self._source += '// %s<%s> wrapper\n' % (tmpl_name, ', '.join(bind_args))
		self._source += 'static %s %s(%s) { ' % (bound_rval, bound_name, ', '.join(bound_named_args))
		if bound_rval != 'void':
			self._source += 'return '
		self._source += '%s<%s>(%s);' % (tmpl_name, ', '.join(bind_args), ', '.join(['arg%d' % i for i in range(len(bound_args))]))
		self._source += ' }\n\n'

		# bind wrapper
		self.bind_function(bound_name, bound_rval, bound_args)

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

		def register_upcast(type, bases):
			for base in bases:
				downcasts[base].append(type)
				register_upcast(type, base.bases)

		for type in self._bound_types:
			register_upcast(type, type.bases)

		#
		out = '''\
// type_tag based cast system
void *_type_tag_upcast(void *in_p, const char *in_type_tag, const char *out_type_tag) {
	if (out_type_tag == in_type_tag)
		return in_p;

	void *out_p = NULL;
\n'''

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

			out += '	}'
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
