from pypeg2 import re, flag, name, Plain, optional, attr, K, parse


__header = ""
__source = ""


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


class __CType:
	def __repr__(self):
		return get_fully_qualified_ctype_name(self)


__CType.grammar = flag("const", K("const")), optional([flag("signed", K("signed")), flag("unsigned", K("unsigned"))]), attr("unqualified_name", typename), optional(attr("ref", ref_re))


class __CArg:
	def __repr__(self):
		out = repr(self.ctype)
		if hasattr(self, 'name'):
			out += ' ' + str(self.name)
		return out


__CArg.grammar = attr("ctype", __CType), optional(name())


#
def insert_comment(comment, in_source=True, in_header=True):
	global __header, __source
	if in_header:
		__header += '// ' + comment + '\n'
	if in_source:
		__source += '// ' + comment + '\n'


def insert_header_code(code):
	global __header
	__header += code + '\n'


def insert_source_code(code):
	global __source
	__source += code + '\n'


#
__namespace = None


def set_namespace(ns):
	global __namespace
	__namespace = ns


#
__templates = None


def set_proto_templates(check, to_c, from_c):
	global __templates
	__templates['proto_check'] = check
	__templates['proto_to_c'] = to_c
	__templates['proto_from_c'] = from_c


def set_call_templates(arg_to_c, rval_from_c, void_rval_from_c):
	global __templates
	__templates['arg_to_c'] = arg_to_c
	__templates['rval_from_c'] = rval_from_c
	__templates['void_rval_from_c'] = void_rval_from_c


def set_class_templates(check, to_c, from_c):
	global __templates
	__templates['class_check'] = check
	__templates['class_to_c'] = to_c
	__templates['class_from_c'] = from_c


#
__ctype_infos = None


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


def __output_type_op_function(body, type, info, op):
	name = '_%s_%s' % (info['clean_name'], op)

	proto = __templates['proto_' + op](name, type, info)

	global __header, __source
	__header += proto + ';\n'

	if callable(body):
		body_src = body(type, info)
	else:
		body_src = body

	__source += proto + ' { ' + body_src + ' }\n'

	return name


def bind_common(type, info):
	global __header, __source

	insert_comment('type operators for ' + type)

	info['clean_name'] = get_type_clean_name(type)
	info['type_tag'] = '__%s_type_tag' % info['clean_name']
	insert_source_code('static const char *%s = "%s";\n' % (info['type_tag'], type))


def bind_type(type, check, to_c, from_c):
	"""Declare a simple type natively supported by the VM"""
	global __ctype_infos

	info = {'policy': 'by_value', 'ctype': parse(type, __CType)}
	__ctype_infos[type] = info

	global __header, __source
	bind_common(type, info)

	assert check, "'check' operator must be provided for simple type '%s'" % type
	assert to_c, "'to_c' operator must be provided for simple type '%s'" % type
	assert from_c, "'from_c' operator must be provided for simple type '%s'" % type

	#
	info['check'] = __output_type_op_function(check, type, info, 'check')
	info['to_c'] = __output_type_op_function(to_c, type, info, 'to_c')
	info['from_c'] = __output_type_op_function(from_c, type, info, 'from_c')

	__header += '\n'
	__source += '\n'






#
def bind_class(type, check, to_c, from_c):
	"""Declare a C++ struct/class"""
	global __ctype_infos

	info = {'policy': 'by_pointer', 'ctype': parse(type, __CType)}
	__ctype_infos[type] = info

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







#
def __get_arg_name(i):
	return 'arg' + str(i)


def select_ctype_info(ctype):
	"""Select the type information structure."""
	full_qualified_ctype_name = get_fully_qualified_ctype_name(ctype)

	if full_qualified_ctype_name in __ctype_infos:
		return __ctype_infos[full_qualified_ctype_name]

	return __ctype_infos[ctype.unqualified_name]


def qualify_value_var(var_name, ctype):
	"""Qualify a C value variable so that it conforms to a C type signature."""
	if hasattr(ctype, 'ref'):
		if ctype.ref == '*':
			return '&' + var_name
		if ctype.ref == '&':
			return var_name

	return var_name


def qualify_pointer_var(var_name, ctype):
	"""Qualify a C pointer variable so that it conforms to a type signature."""
	pass


def __arg_to_c(args, i, arg_count):
	"""Convert an argument from a list of arguments, return the update argument position."""
	global __header, __source

	arg = args[i]  # argument to transform to C
	ctype_info = select_ctype_info(arg.type)

	arg_var = __get_arg_name(i)

	if ctype_info['policy'] == 'by_value':
		__source += '%s %s;\n' % (get_fully_qualified_ctype_name(arg.type), arg_var)
		__source += __templates['arg_to_c'](args, i, arg_count, ctype_info['to_c'], '&' + arg_var)
		qualified_arg_var = qualify_value_var(arg_var, arg.type)
	elif ctype_info['policy'] == 'by_pointer':
		__source += '%s *%s;\n' % (get_fully_qualified_ctype_name(arg.type), arg_var)
		__source += __templates['arg_to_c'](args, i, arg_count, ctype_info['to_c'], arg_var)
		qualified_arg_var = qualify_pointer_var(arg_var, arg.type)

	__source += '\n'

	return [qualified_arg_var]


def __args_to_c(args_ops):
	"""Prepare arguments to a C function call."""

	global __header, __source

	arg_count = len(args_ops)
	if arg_count == 1 and args_ops[0] == 'void':
		return  # no arguments expected

	qualified_args = []

	for arg_op in args_ops:
		info = arg_op['info']
		vars = arg_op['vars']

		for var in vars:
			__source += '%s %s;\n' % (get_fully_qualified_ctype_name(var['ctype']), var['var'])
			pass


			#	i = 0
#	while i < arg_count:
#		qualified_arg = __arg_to_c(args, i, arg_count)
#		i += len(qualified_arg)
#		qualified_args.extend(qualified_arg)

	return qualified_args


#
def __get_rval_name(i):
	return 'rval' + str(i)


def __rval_from_c(rvals):
	global __header, __source

	rval_count = len(rvals)

	# void return value
	if rval_count == 1 and rvals[0].unqualified_name == 'void':
		__source += __templates['void_rval_from_c']() + '\n'
		return

	for i, ctype in enumerate(rvals):
		type_info = select_ctype_info(ctype)
		name = __get_rval_name(i)

		own_policy = 'NonOwning'
		qualifier = ''

		if hasattr(ctype, 'ref'):
			if ctype.ref == '&':
				qualifier = '&'  # reference to pointer
				own_policy = 'NonOwning'
			elif ctype.ref == '*':
				own_policy = 'NonOwning'
		else:
			qualifier = '&'  # value to pointer
			own_policy = 'ByValue'

		__source += __templates['rval_from_c'](i, rval_count, qualifier + name, type_info['from_c'], own_policy) + '\n'


def __declare_rval_var(rval):
	if rval[0].unqualified_name == 'void':
		return

	global __header, __source

	ctype = rval[0]
	name = __get_rval_name(0)  # destination variable

	if hasattr(ctype, 'ref'):
		if ctype.ref == '*':
			__source += '%s *%s = ' % (ctype.unqualified_name, name)
		elif ctype.ref == '&':
			__source += '%s &%s = ' % (ctype.unqualified_name, name)
	else:
		__source += '%s %s = ' % (ctype.unqualified_name, name)







#
def __prepare_ctypes(ctypes, template):
	if not type(ctypes) is type([]):
		ctypes = [ctypes]
	return [parse(type, template) for type in ctypes]


def prepare_args(args):
	return __prepare_ctypes(args, __CArg)


def prepare_rval(rval):
	return __prepare_ctypes(rval, __CType)


#
def select_args_operators(args):
	return [{'info': select_ctype_info(arg.ctype), 'vars': [{'ctype': arg.ctype, 'var': __get_arg_name(i)}]} for i, arg in enumerate(args)]


#
def ctypes_to_string(ctypes):
	return ','.join([repr(ctype) for ctype in ctypes])


# --
def get_bind_function_name(name):
	return '_' + name


def bind_function(name, rval, args):
	rval = prepare_rval(rval)
	args = prepare_args(args)

	global __header, __source
	insert_comment('%s %s(%s)' % (ctypes_to_string(rval), name, ctypes_to_string(args)), True, False)

	__source += "static int " + get_bind_function_name(name) + "(lua_State *L) {\n"

	args_ops = select_args_operators(args)
	qualified_args = __args_to_c(args_ops)  # convert args

	__declare_rval_var(rval)
	__source += name + '(' + ', '.join(qualified_args) + ');\n'  # perform C function call
	__rval_from_c(rval)

	__source += "}\n\n"












#
def reset_generator():
	global __header, __source
	__header = ""
	__source = ""

	__source += '''
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

	global __templates, __ctype_infos
	__templates = {}
	__ctype_infos = {}


def get_output():
	header = "// MBIND - .h\n\n"
	if __namespace:
		header += "namespace " + __namespace + " {\n\n";
	header += __header
	if __namespace:
		header += "} // " + __namespace + "\n";

	#
	source = "// MBIND - .cpp\n\n"
	if __namespace:
		source += "namespace " + __namespace + " {\n\n";
	source += __source
	if __namespace:
		source += "} // " + __namespace + "\n";

	return header, source
