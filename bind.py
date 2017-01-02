from pypeg2 import re, flag, name, Plain, optional, attr, K, parse


__header = ""
__source = ""


#
typename = re.compile(r"((::)*(_|[A-z])[A-z0-9_]*)+")
ref_re = re.compile(r"[&*]+")


class __CType:
	def __repr__(self):
		out = ""
		if self.const:
			out += "const "
		out += self.unqualified_name
		if hasattr(self, "ref"):
			out += self.ref
		return out


__CType.grammar = flag("const", K("const")), optional([flag("signed", K("signed")), flag("unsigned", K("unsigned"))]), attr("unqualified_name", typename), optional(attr("ref", ref_re))


class __CArg:
	def __repr__(self):
		out = repr(self.type)
		if hasattr(self, 'name'):
			out += ' ' + str(self.name)
		return out


__CArg.grammar = attr("type", __CType), optional(name())


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


def set_type_templates(check, to_c, from_c):
	global __templates
	__templates['check'] = check
	__templates['to_c'] = to_c
	__templates['from_c'] = from_c


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
__type_infos = None


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


def __get_type_op_function_name(type, op):
	""" Return the name of the function implementing an operator for a given type in the generator output."""
	return "_" + get_type_clean_name(type) + "_" + op


def __output_type_op_function(body, type, info, op):
	name = __get_type_op_function_name(type, op)

	proto = __templates[op](name, type, info)

	global __header, __source
	__header += proto + ';\n'
	__source += proto + ' { ' + body + ' }\n'

	return name


def bind_common(type, info):
	global __header, __source

	insert_comment('typemap for ' + type)

	info['type_cstr'] = '__%s_type_cstr' % type
	insert_source_code('static const char *%s = "%s";\n\n' % (info['type_cstr'], type))


def bind_type(type, check, to_c, from_c):
	"""Declare a simple type natively supported by the VM"""
	global __type_infos

	info = {'type': 'simple', 'check': check, 'to_c': to_c, 'from_c': from_c}
	__type_infos[type] = info

	global __header, __source
	bind_common(type, info)

	#
	info['__check_func'] = __output_type_op_function(check, type, info, 'check')
	info['__to_c_func'] = __output_type_op_function(to_c, type, info, 'to_c')
	info['__from_c_func'] = __output_type_op_function(from_c, type, info, 'from_c')

	__header += '\n'
	__source += '\n'






#
def bind_class(type, check, to_c, from_c):
	"""Declare a C++ struct/class"""
	global __type_infos

	info = {'type': 'class', 'check': check, 'to_c': to_c, 'from_c': from_c}
	__type_infos[type] = info

	global __header, __source
	bind_common(type, info)

	#
	info['__check_func'] = __output_type_op_function(check, type, info, 'class_check')
	info['__to_c_func'] = __output_type_op_function(to_c, type, info, 'class_to_c')
	info['__from_c_func'] = __output_type_op_function(from_c, type, info, 'class_from_c')

	__header += '\n'
	__source += '\n'







#
def __get_arg_name(i):
	return 'arg' + str(i)


def __arg_to_c(args, i, args_count):
	"""Convert an argument from a list of arguments, return the update argument position."""
	global __header, __source

	arg = args[i]  # argument to transform to C

	name = __get_arg_name(i)
	decl = __type_infos[arg.type.unqualified_name]

	# by value
	__source += arg.type.unqualified_name + ' ' + name + ';\n'
	__source += __templates['arg_to_c'](args, i, args_count, '&' + name, decl['__to_c_func']) + '\n'

	return i + 1



def __args_to_c(args):
	"""Prepare arguments to a C function call."""

	args_count = len(args)
	if args_count == 1 and args[0] == 'void':
		return  # no arguments expected

	i = 0
	while i < args_count:
		i = __arg_to_c(args, i, args_count)


#
def __get_rval_name(i):
	return 'rval' + str(i)


def __rval_from_c(rvals):
	global __header, __source

	rval_count = len(rvals)

	# void return value
	if rval_count == 1 and rvals[0] == 'void':
		__source += __templates['void_rval_from_c']() + '\n'
		return

	for i, rval in enumerate(rvals):
		decl = __type_infos[rval]

		name = __get_rval_name(i)

		# by value
		__source += __templates['rval_from_c'](i, rval_count, '&' + name, decl['__from_c_func']) + '\n'





#
def __prepare_types(types, template):
	if not type(types) is type([]):
		types = [types]
	return [parse(type, template) for type in types]


def prepare_args(args):
	return __prepare_types(args, __CArg)


def prepare_rval(rval):
	return __prepare_types(rval, __CType)


#
def types_to_string(types):
	return ','.join([repr(type) for type in types])


# --
def get_bind_function_name(name):
	return '_' + name


def bind_function(name, rval, args):
	rval = prepare_rval(rval)
	args = prepare_args(args)

	global __header, __source
	insert_comment('%s %s(%s)' % (types_to_string(rval), name, types_to_string(args)), True, False)

	__source += "static int " + get_bind_function_name(name) + "(lua_State *L) {\n"
	__args_to_c(args)  # convert args

	if rval != 'void':
		__source += "%s %s = " % (rval, __get_rval_name(0))




	__source += name + '(' + ', '.join(args_to_c_cast) + ');\n'  # function call

	rvals = [rval]  # implement *OUT (SWIG style) here
	__rval_from_c(rvals)

	__source += "}\n\n"












#
def reset_generator():
	global __header, __source
	__header = ""
	__source = ""

	__source += '''
// native object wrapper
enum OwnershipPolicy { NonOwning, ByValue, ByAddress };

struct NativeObjectWrapper {
	virtual ~NativeObjectWrapper() = 0

	virtual void *GetObj() const = 0;
	virtual const char *GetType() const = 0;
};

template <typename T> struct NativeObjectValueWrapper : NativeObjectWrapper {
	NativeObjectValueWrapper(T *obj_, const char *type_) : obj(*obj_), type(type_) {}

	void *GetObj() const override { return &obj; }
	const char *GetType() const override { return type; }

private:
	T obj;
	const char *type;
};

struct NativeObjectPtrWrapper : NativeObjectWrapper {
	NativeObjectPtrWrapper(void *obj_, const char *type_) : obj(obj_), type(type_) {}

	void *GetObj() const { return obj; }
	const char *GetType() const { return type; }

private:
	void *obj;
	const char *type;
};

template <typename T> struct NativeObjectUniquePtrWrapper : NativeObjectWrapper {
	NativeObjectUniquePtrWrapper(T *obj_, const char *type_) : obj(obj_), type(type_) {}

	void *GetObj() const { return obj.get(); }
	const char *GetType() const { return type; }

private:
	std::unique_ptr<T> obj;
	const char *type;
};

template <typename T> struct NativeObjectSharedPtrWrapper : NativeObjectWrapper {
	NativeObjectSharedPtrWrapper(std::shared_ptr<T> *obj_, const char *type_) : obj(*obj_), type(type_) {}

	void *GetObj() const { return obj.get(); }
	const char *GetType() const { return type; }

private:
	std::shared_ptr<T> obj;
	const char *type;
};
'''

	global __templates, __type_infos
	__templates = {}
	__type_infos = {}


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
