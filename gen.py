from pypeg2 import re, flag, name, Plain, optional, attr, K, parse


#
typename = re.compile(r"((::)*(_|[A-z])[A-z0-9_]*)+")
ref_re = re.compile(r"[&*]+")


def get_fully_qualified_ctype_name(type):
	out = ''
	if type.const:
		out += 'const '
	out += type.unqualified_name
	if hasattr(type, 'ref'):
		out += ' ' + type.ref
	return out


def get_type_clean_name(type):
	""" Return a type name cleaned so that it may be used as variable name in the generator output."""
	parts = type.split(' ')

	def clean_type_name_part(part):
		part = part.replace('*', 'ptr')  # pointer
		part = part.replace('&', '_r')  # reference
		part = part.replace('::', '__')  # namespace
		return part

	parts = [clean_type_name_part(part) for part in parts]
	return '_'.join(parts)


def ctypes_to_string(ctypes):
	return ','.join([repr(ctype) for ctype in ctypes])


class _CType:
	def __repr__(self):
		return get_fully_qualified_ctype_name(self)

	def get_ref(self):
		return self.ref if hasattr(self, 'ref') else ''


_CType.grammar = flag("const", K("const")), optional([flag("signed", K("signed")), flag("unsigned", K("unsigned"))]), attr("unqualified_name", typename), optional(attr("ref", ref_re))


#
def clean_c_symbol_name(name):
	name = name.replace('::', '__')
	return name


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


class TypeConverter:
	def __init__(self, type, storage_ref=''):
		self.ctype = parse(type, _CType)
		self.storage_ctype = parse(type + storage_ref, _CType)

		self.clean_name = get_type_clean_name(type)
		self.fully_qualified_name = get_fully_qualified_ctype_name(self.ctype)
		self.type_tag = '__%s_type_tag' % self.clean_name

	def check(self):
		assert 'check not implemented'
	def to_c(self):
		assert 'to_c not implemented'
	def from_c(self):
		assert 'from_c not implemented'

	def get_ownership_policy(self, ref):
		"""Return the VM default ownership policy for a reference coming from C."""
		if ref == '*' or ref == '&':
			return 'NonOwning'
		return 'ByValue'

	def return_void_from_c(self):
		assert 'return_void_from_c not implemented'


#
class FABGen:
	def __init__(self):
		self._namespace = None
		self._header, self._source = None, None

		self.__type_convs = None
		self.__function_templates = None

	def start(self, namespace = None):
		self._namespace = namespace
		self._header, self._source = "", ""

		self.__type_convs = {}
		self.__function_templates = {}

		self._source += '''
#include <cstdint>

// native object wrapper
enum OwnershipPolicy { NonOwning, ByValue, ByAddress };

struct NativeObjectWrapper {
	virtual ~NativeObjectWrapper() = 0

	virtual void *GetObj() const = 0;
	virtual const char *GetTypeTag() const = 0;

	bool IsNativeObjectWrapper() const { return magic == 'fab!'; }

private:
	const uint32_t magic = 'fab!';
};

template <typename T> struct NativeObjectValueWrapper : NativeObjectWrapper {
	NativeObjectValueWrapper(T *obj_, const char *type_tag_) : obj(*obj_), type_tag(type_tag_) {}

	void *GetObj() const override { return &obj; }
	const char *GetTypeTag() const override { return type; }

private:
	T obj;
	const char *type_tag;
};

struct NativeObjectPtrWrapper : NativeObjectWrapper {
	NativeObjectPtrWrapper(void *obj_, const char *type_tag_) : obj(obj_), type_tag(type_tag_) {}

	void *GetObj() const override { return obj; }
	const char *GetType() const override { return type; }

private:
	void *obj;
	const char *type_tag;
};

template <typename T> struct NativeObjectUniquePtrWrapper : NativeObjectWrapper {
	NativeObjectUniquePtrWrapper(T *obj_, const char *type_tag_) : obj(obj_), type_tag(type_tag_) {}

	void *GetObj() const override { return obj.get(); }
	const char *GetTypeTag() const override { return type; }

private:
	std::unique_ptr<T> obj;
	const char *type_tag;
};

template <typename T> struct NativeObjectSharedPtrWrapper : NativeObjectWrapper {
	NativeObjectSharedPtrWrapper(std::shared_ptr<T> *obj_, const char *type_tag_) : obj(*obj_), type_tag(type_tag_) {}

	void *GetObj() const override { return obj.get(); }
	const char *GetTypeTag() const override { return type; }

private:
	std::shared_ptr<T> obj;
	const char *type_tag;
};
'''

	def insert_code(self, code, in_source=True, in_header=True):
		if in_header:
			self._header += code
		if in_source:
			self._source += code

	#
	def proto_check(self, name, ctype):
		assert 'proto_check not implemented in generator'
	def proto_to_c(self, name, ctype):
		assert 'proto_check not implemented in generator'
	def proto_from_c(self, name, ctype):
		assert 'proto_check not implemented in generator'

	def __output_type_op_function(self, conv, op):
		name = '_%s_%s' % (conv.clean_name, op)

		proto = getattr(self, 'proto_%s' % op)
		if callable(proto):
			ctype = conv.storage_ctype if op == 'to_c' else conv.ctype
			proto = proto(name, ctype)

		self._header += proto + ';\n'

		body = getattr(conv, 'tmpl_%s' % op)
		if callable(body):
			body = body()

		self._source += proto + ' { ' + body + ' }\n'
		setattr(conv, op, name)

	#

	def bind_type(self, conv):
		"""Declare a converter for a type natively supported by the target VM."""
		type = conv.fully_qualified_name
		self.__type_convs[type] = conv

		# output type tag
		self.insert_code('// type operators for %s\n' % type)
		self._source += 'static const char *%s = "%s";\n\n' % (conv.type_tag, type)

		self.__output_type_op_function(conv, 'check')
		self.__output_type_op_function(conv, 'to_c')
		self.__output_type_op_function(conv, 'from_c')

		#
		self.insert_code('\n')

	def get_output(self):
		header = "// FABGen - .h\n\n"
		if self._namespace:
			header += "namespace " + self._namespace + " {\n\n";
		header += self._header
		if self._namespace:
			header += "} // " + self._namespace + "\n";

		source = "// FABGen - .cpp\n\n"
		if self._namespace:
			source += "namespace " + self._namespace + " {\n\n";
		source += self._source
		if self._namespace:
			source += "} // " + self._namespace + "\n";

		return header, source

	#
	def select_ctype_conv(self, ctype):
		"""Select a type converter."""
		full_qualified_ctype_name = get_fully_qualified_ctype_name(ctype)

		if full_qualified_ctype_name == 'void':
			return None

		if full_qualified_ctype_name in self.__type_convs:
			return self.__type_convs[full_qualified_ctype_name]

		return self.__type_convs[ctype.unqualified_name]

	#
	def select_args_convs(self, args):
		return [{'conv': self.select_ctype_conv(arg.ctype), 'ctype': arg.ctype} for i, arg in enumerate(args)]

	def select_rvals_convs(self, rvals):
		return [{'conv': self.select_ctype_conv(ctype), 'ctype': ctype} for i, ctype in enumerate(rvals)]

	def decl_arg(self, ctype, name):
		return '%s %s;\n' % (get_fully_qualified_ctype_name(ctype), name)

	def cleanup_args(self, args):
		pass

	#
	def commit_rvals(self, rvals):
		assert "missing return values template"

	def decl_rval(self, type, name):
		return '%s %s = ' % (get_fully_qualified_ctype_name(type), name)

	def cleanup_rvals(self, rvals, rval_names):
		pass

	#
	@staticmethod
	def __get_bind_function_name(name):
		return '_' + clean_c_symbol_name(name)

	def bind_function(self, name, rval, args):
		rval = parse(rval, _CType)
		args = _prepare_ctypes(args, _CArg)

		self.insert_code('// %s %s(%s)\n' % (rval, name, ctypes_to_string(args)), True, False)

		self._source += self.new_function(self.__get_bind_function_name(name), args)

		# declare call arguments and convert them from the VM
		args = self.select_args_convs(args)

		c_call_args = []
		for i, arg in enumerate(args):
			conv = arg['conv']
			if not conv:
				continue

			arg_name = 'arg%d' % i
			self._source += self.decl_arg(conv.storage_ctype, arg_name)
			self._source += conv.to_c_ptr(self.get_arg(i, args), '&' + arg_name)

			c_call_arg_transform = ctype_ref_to(conv.storage_ctype.get_ref(), arg['ctype'].get_ref())
			c_call_args.append(c_call_arg_transform + arg_name)

		# declare the return value
		rval_names = []
		rval_conv = self.select_ctype_conv(rval)

		if rval_conv:
			self._source += self.decl_rval(rval, 'rval')
			rval_names.append('rval')

		# perform function call
		self._source += '%s(%s);\n' % (name, ', '.join(c_call_args))  # perform C function call

		# cleanup arguments
		self.cleanup_args(args)

		# convert the return value
		self.begin_convert_rvals()
		if rval_conv:
			self.rval_from_c_ptr(rval, 'rval', rval_conv, ctype_ref_to(rval.get_ref(), rval_conv.ctype.get_ref() + '*') + 'rval')

		# commit return values
		if rval_conv:
			rvals = [rval_conv]
		else:
			rvals = []

		self.commit_rvals(rvals, rval_names)

		# cleanup return value
		self.cleanup_rvals(rvals, rval_names)

		self._source += "}\n\n"

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
		self._source += 'static %s %s(%s) {\n' % (bound_rval, bound_name, ', '.join(bound_named_args))
		if bound_rval != 'void':
			self._source += 'return '
		self._source += '%s<%s>(%s);\n' % (tmpl_name, ', '.join(bind_args), ', '.join(['arg%d' % i for i in range(len(bound_args))]))
		self._source += '}\n\n'

		# bind wrapper
		self.bind_function(bound_name, bound_rval, bound_args)

	def get_class_default_converter(self):
		assert "missing class type default converter"

	def bind_class(self, name):
		class_default_conv = self.get_class_default_converter()
		self.bind_type(class_default_conv(name))
