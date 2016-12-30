__header = ""
__source = ""


def insert_comment(comment, in_source=True, in_header=True):
	global __header, __source
	if in_header:
		__header += '// ' + comment + '\n'
	if in_source:
		__source += '// ' + comment + '\n'


#--
__namespace = None


def set_namespace(ns):
	global __namespace
	__namespace = ns


#--
__templates = None


def set_templates(template):
	global __templates
	__templates = template


#--
__type_decls = {}


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


def get_type_typemap_op_function_name(type, op):
	""" Return the name of the function implementing a typemap operator for a given type in the generator output."""
	return "_" + get_type_clean_name(type) + "_" + op


def __output_type_typemap_op_function(decl, type, op):
	name = get_type_typemap_op_function_name(type, op)
	decl['__' + op + '_func'] = name

	proto = __templates[op]
	proto = proto.replace('$name', name)

	if 'intermediate' in decl:
		intermediate_decl = decl['intermediate']
		proto = proto.replace('$type', intermediate_decl['type'])
	else:
		proto = proto.replace('$type', type)

	global __header, __source

	__header += proto + ';\n'

	__source += proto + ' { ' + decl[op] + ' }\n'


def __output_type_intermediate_functions(decl, type):
	global __header, __source

	to_type_name = "_" + get_type_clean_name(type) + "_from_" + get_type_clean_name(decl['type'])
	from_type_name = "_" + get_type_clean_name(type) + "_to_" + get_type_clean_name(decl['type'])
	decl['__to_type_func'] = to_type_name
	decl['__from_type_func'] = from_type_name

	body = decl['to_type']
	body = body.replace('$in', 'in')
	body = body.replace('$out', 'out')
	__source += 'void %s(%s *in, %s *out) { %s }\n' % (to_type_name, decl['type'], type, body)

	body = decl['from_type']
	body = body.replace('$in', 'in')
	body = body.replace('$out', 'out')
	__source += 'void %s(%s *in, %s *out) { %s }\n' % (from_type_name, type, decl['type'], body)

	__source += '\n'


def register_type(type, decl):
	global __type_decls

	__type_decls[type] = decl

	# output type conversion functions
	global __header, __source

	comment = 'typemap for ' + type
	if 'intermediate' in decl:
		comment += ' (through intermediate ' + decl['intermediate']['type'] + ')'

	insert_comment(comment)

	__output_type_typemap_op_function(decl, type, 'check')
	__output_type_typemap_op_function(decl, type, 'to_c')
	__output_type_typemap_op_function(decl, type, 'from_c')

	__header += '\n'
	__source += '\n'

	if 'intermediate' in decl:
		__output_type_intermediate_functions(decl['intermediate'], type)


#--
def get_bind_function_name(name):
	return '_' + name


def get_arg_name(i):
	return 'arg' + str(i)


def args_to_c(args):
	global __header, __source

	args_to_c_cast = []  # argument temporaries cast to the function signature

	args_len = len(args)
	if args_len == 1 and args[0] == 'void':
		return args_to_c_cast

	for i, type in enumerate(args):
		decl = __type_decls[type]

		name = get_arg_name(i)

		# by value
		__source += type + ' ' + name + ';\n'
		__source += __templates['arg_to_c'](i, args_len, '&' + name, decl['__to_c_func']) + '\n'
		args_to_c_cast.append(name)

		# by ref

		# by pointer

	return args_to_c_cast


def get_rval_name(i):
	return 'rval' + str(i)


def rval_from_c(rvals):
	global __header, __source

	rvals_len = len(rvals)

	# void return value
	if rvals_len == 1 and rvals[0] == 'void':
		__source += __templates['void_rval_from_c'] + '\n'
		return

	for i, rval in enumerate(rvals):
		decl = __type_decls[rval]

		name = get_rval_name(i)

		# by value
		__source += __templates['rval_from_c'](i, rvals_len, '&' + name, decl['__from_c_func']) + '\n'


def bind_function(name, rval, args):
	global __header, __source
	insert_comment('%s %s(%s)' % (rval, name, ', '.join(args)), True, False)

	__source += "static int " + get_bind_function_name(name) + "(lua_State *L) {\n"
	args_to_c_cast = args_to_c(args)  # convert args

	if rval != 'void':
		__source += "%s %s = " % (rval, get_rval_name(0))

	__source += name + '(' + ', '.join(args_to_c_cast) + ');\n'  # function call

	rvals = [rval]  # implement *OUT (SWIG style) here
	rval_from_c(rvals)

	__source += "}\n\n"


#--
def reset_generator():
	global __header, __source
	__header = ""
	__source = ""

	global __templates, __type_decls
	__templates = None
	__type_decls = {}


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
