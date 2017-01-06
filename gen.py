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


_CType.grammar = flag("const", K("const")), optional([flag("signed", K("signed")), flag("unsigned", K("unsigned"))]), attr("unqualified_name", typename), optional(attr("ref", ref_re))


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
class TypeConverter:
	def __init__(self, type):
		self.ctype = parse(type, _CType)

		self.clean_name = get_type_clean_name(type)
		self.type_tag = '__%s_type_tag' % self.clean_name

	def check(self):
		assert 'check not implemented'
	def to_c(self):
		assert 'to_c not implemented'
	def from_c(self):
		assert 'from_c not implemented'

	def return_void_from_c(self):
		assert 'return_void_from_c not implemented'


#
class FABGen:
	def __init__(self):
		self.__namespace = None
		self.__header, self.__source = None, None

		self.__ctype_convs = None

	def start(self, namespace = None):
		self.__namespace = namespace
		self.__header, self.__source = "", ""

		self.__type_convs = {}

		self.__source += '''
#include <cstdint>

// native object wrapper
enum OwnershipPolicy { NonOwning, ByValue, ByAddress };

struct NativeObjectWrapper {
	virtual ~NativeObjectWrapper() = 0

	virtual void *GetObj() const = 0;
	virtual const char *GetTypeTag() const = 0;

	bool IsNativeObjectWrapper() const { return magic == 'fab!'; }

private:
	uint32_t magic = 'fab!';
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
			self.__header += code
		if in_source:
			self.__source += code

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
			proto = proto(name, conv.ctype)

		self.__header += proto + ';\n'

		body = getattr(conv, 'tmpl_%s' % op)
		if callable(body):
			body = body()

		self.__source += proto + ' { ' + body + ' }\n'
		setattr(conv, op, name)

	#

	def bind_type(self, type, conv):
		"""Declare a converter for a type natively supported by the target VM."""
		self.__type_convs[type] = conv

		# output type tag
		self.insert_code('// type operators for %s\n' % type)
		self.__source += 'static const char *%s = "%s";\n\n' % (conv.type_tag, type)

		self.__output_type_op_function(conv, 'check')
		self.__output_type_op_function(conv, 'to_c')
		self.__output_type_op_function(conv, 'from_c')

		#
		self.insert_code('\n')

	def get_output(self):
		header = "// FABGen - .h\n\n"
		if self.__namespace:
			header += "namespace " + self.__namespace + " {\n\n";
		header += self.__header
		if self.__namespace:
			header += "} // " + self.__namespace + "\n";

		source = "// FABGen - .cpp\n\n"
		if self.__namespace:
			source += "namespace " + self.__namespace + " {\n\n";
		source += self.__source
		if self.__namespace:
			source += "} // " + self.__namespace + "\n";

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

	#
	@staticmethod
	def get_bind_function_name(name):
		return '_' + name

	def bind_function(self, name, rval, args):
		rval = parse(rval, _CType)
		args = _prepare_ctypes(args, _CArg)

		self.insert_code('// %s %s(%s)\n' % (rval, name, ctypes_to_string(args)), True, False)

		self.__source += "static int " + self.get_bind_function_name(name) + "(lua_State *L) {\n"

		# declare call arguments and convert them from the VM
		args = self.select_args_convs(args)

		c_call_args = []
		for i, arg in enumerate(args):
			conv = arg['conv']

			block, arg_p = conv.new_var('arg%d' % i)
			self.__source += block
			self.__source += conv.to_c_ptr(i, arg_p)  # convert from VM to C var pointer
			c_call_args.append('arg%d' % i)  # FIXME transform to argument signature

		# declare the return value
		rval = self.select_ctype_conv(rval)

		if rval:
			block, rval_p = rval.new_var('rval')
			self.__source += block
			self.__source += "rval = "

		# perform function call
		self.__source += '%s(%s);\n' % (name, ', '.join(c_call_args))  # perform C function call

		# convert the return value
		if rval:
			self.__source += "%s(L, %s, ByValue)" % (rval.from_c, rval_p)

		# cleanup arguments
		# ...

		# cleanup return value

		#	qualified_args = __args_to_c(args_infos)  # convert args
		'''
		__rvals_from_c(rval)

		__source += "}\n\n"
		'''







'''
#
def bind_class(type, check, to_c, from_c):
	"""Declare a converter for a C/C++ custom type."""
	global __ctype_convs

	info = {'policy': 'by_pointer', 'ctype': parse(type, __CType)}
	__ctype_convs[type] = info

	global __header, __source
	bind_common(type, info)

	# default to language conversion for complex objects
	if not check:
		check = __templates['class_check']
	if not to_c:
		to_c = __templates['class_to_c']
	if not from_c:
		from_c = __templates['class_from_c']

	#
	info['check'] = __output_type_op_function(check, type, info, 'check')
	info['to_c'] = __output_type_op_function(to_c, type, info, 'to_c')
	info['from_c'] = __output_type_op_function(from_c, type, info, 'from_c')

	__header += '\n'
	__source += '\n'
'''










#









