import gen
import lib.python.std as std
import lib.python.stl as stl


#
class PythonTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type, storage_type=None):
		super().__init__(type, storage_type)

	def output_type_api(self, module_name):
		return '// type API for %s\n' % self.fully_qualified_name +\
		'bool check_%s(PyObject *o);\n' % self.clean_name +\
		'void to_c_%s(PyObject *o, void *obj);\n' % self.clean_name +\
		'PyObject *from_c_%s(void *obj, OwnershipPolicy);\n' % self.clean_name

	def to_c_call(self, in_var, out_var_p):
		return 'to_c_%s(%s, %s);\n' % (self.clean_name, in_var, out_var_p)

	def from_c_call(self, out_var, in_var_p, ownership_policy):
		return "PyObject *%s = from_c_%s(%s, %s);\n" % (out_var, self.clean_name, in_var_p, ownership_policy)

	def output_type_glue(self, module_name, members, methods):
		check = '''bool check_%s(PyObject *o) {
	return PyFloat_Check(o) ? true : false;
}''' % (self.clean_name)

		to_c = '''void to_c_%s(PyObject *o, void *obj) {
*((%s*)obj) = PyFloat_AsDouble(o);
}''' % (self.clean_name, self.ctype)

		from_c = '''PyObject *from_c_%s(void *obj, OwnershipPolicy) {
return PyFloat_FromDouble(*((%s*)obj));
}''' % (self.clean_name, self.ctype)

		return check + to_c + from_c + '\n'


#
class PythonClassTypeDefaultConverter(PythonTypeConverterCommon):
	def __init__(self, type):
		super().__init__(type, type + '*')

	def output_members(self, members):
		out = ''
		for member, conv in members:
			out += '// get/set %s %s::%s\n' % (member.ctype, self.clean_name, member.name)

			getset_var = '((%s *)w->obj)->%s' % (self.clean_name, member.name)  # pointer to variable to get
			getset_var_conv = conv.prepare_var_for_conv(getset_var, member.ctype.get_ref())  # pointer to the converter supported type

			out += 'static PyObject *_%s_get_%s(PyObject *self, void */*closure*/) {\n' % (self.clean_name, member.name)
			out += '''\
	if (!test_wrapped_PyObject(self, %s))
		return NULL;
	wrapped_PyObject *w = (wrapped_PyObject *)self;\n''' % (self.type_tag)
			out += '\t' + conv.from_c_call('out', getset_var_conv, self.get_ownership_policy(member.ctype))
			out += '	return out;\n'
			out += '}\n'

			out += 'static int _%s_set_%s(PyObject *self, PyObject *value, void */*closure*/) {\n' % (self.clean_name, member.name)
			out += '''\
	if (!test_wrapped_PyObject(self, %s))
		return NULL;
	wrapped_PyObject *w = (wrapped_PyObject *)self;\n''' % (self.type_tag)
			out += '\t' + conv.to_c_call('value', getset_var_conv)
			out += '	return 0;\n'
			out += '}\n'

			out += '\n'

		out += 'static PyGetSetDef %s_tp_getset[] = {\n' % self.clean_name
		for member, conv in members:
			out += '	{"%s", (getter)%s, (setter)%s, "TODO doc"},\n' % (member.name, '_%s_get_%s' % (self.clean_name, member.name), '_%s_set_%s' % (self.clean_name, member.name))
		out += '	{NULL} /* Sentinel */'
		out += '};\n\n'

		return out

	def output_type_glue(self, module_name, members, methods):
		# type
		out = 'static PyObject *%s_type;\n\n' % self.clean_name

		# members
		out += self.output_members(members)

		# slots
		out += 'static PyType_Slot %s_slots[] = {\n' % self.clean_name
		out += '	{Py_tp_doc, "TODO doc"},\n'
		out += '	{Py_tp_dealloc, &wrapped_PyObject_tp_dealloc},\n'
		if members:
			out += '	{Py_tp_getset, &%s_tp_getset},\n' % self.clean_name
		out += '''	{0, NULL}
};\n\n'''

		# specification
		out += '''static PyType_Spec simple_struct_spec = {
	"%s.%s", /* name */
	sizeof(wrapped_PyObject), /* basicsize */
	0, /* itemsize*/
	Py_TPFLAGS_DEFAULT, /* flags */
	%s_slots
};\n\n''' % (module_name, self.bound_name, self.clean_name)

		# delete delegate
		out += 'static void delete_%s(void *o) { delete (%s *)o; }\n\n' % (self.clean_name, self.clean_name)

		# to/from C
		out += '''void to_c_%s(PyObject *o, void *obj) {
	wrapped_PyObject *pyobj = (wrapped_PyObject *)o;
	*(%s **)obj = (%s *)pyobj->obj;
}\n\n''' % (self.clean_name, self.clean_name, self.clean_name)

		out += '''PyObject *from_c_%s(void *obj, OwnershipPolicy own) {
	wrapped_PyObject *pyobj = PyObject_New(wrapped_PyObject, (PyTypeObject *)%s_type);
	if (own == ByValue)
		obj = new %s(*(%s *)obj);
	init_wrapped_PyObject(pyobj, __%s_type_tag, obj);
	if (own == ByValue)
		pyobj->on_delete = &delete_%s;
	return (PyObject *)pyobj;
}\n''' % (self.clean_name, self.clean_name, self.clean_name, self.clean_name, self.clean_name, self.clean_name)

		return out

	def finalize_type(self):
		out = '''\
	%s_type = PyType_FromSpec(&%s_spec);
	PyModule_AddObject(m, "%s", %s_type);
''' % (self.clean_name, self.clean_name, self.bound_name, self.clean_name)
		return out


#
class PythonGenerator(gen.FABGen):
	def get_langage(self):
		return "Python"

	def output_includes(self):
		super().output_includes()

		self._source += '''#define Py_LIMITED_API // ensure a single build for Python 3.x (with x>2)
#include "Python.h"
\n'''

	def start(self, module_name):
		super().start(module_name)

		self._source += '''\
typedef struct {
	PyObject_HEAD

	char magic[4]; // ensure PyObject is a wrapped_PyObject
	const char *type_tag; // wrapped pointer type tag

	void *obj;

	void (*on_delete)(void *);
} wrapped_PyObject;

static void init_wrapped_PyObject(wrapped_PyObject *o, const char *type_tag, void *obj) {
	o->magic[0] = 'F';
	o->magic[1] = 'A';
	o->magic[2] = 'B';
	o->magic[3] = '!';
	o->type_tag = type_tag;

	o->obj = obj;

	o->on_delete = NULL;
}

static bool test_wrapped_PyObject(PyObject *o, const char *type_tag) {
	wrapped_PyObject *w = (wrapped_PyObject *)o;

	if (w->magic[0] != 'F' || w->magic[1] != 'A' || w->magic[2] != 'B' || w->magic[3] != '!')
		return false;

	return w->type_tag == type_tag;
}

static void wrapped_PyObject_tp_dealloc(PyObject *self) {
	wrapped_PyObject *w = (wrapped_PyObject *)self;

	if (w->on_delete)
		w->on_delete(w->obj);

	PyObject_Del(self); // tp_free should be used but PyType_GetSlot is 3.4+
}
\n'''

		std.bind_std(self, PythonTypeConverterCommon)
		stl.bind_stl(self, PythonTypeConverterCommon)

	#
	def raise_exception(self, type, reason):
		self._source += 'PyErr_SetString(PyExc_RuntimeError, "%s");\n' % reason

	#
	def new_function(self, name, args):
		return "static PyObject *%s(PyObject *self, PyObject *args) {\n" % name

	#
	def get_class_default_converter(self):
		return PythonClassTypeDefaultConverter

	#
	def get_arg(self, i, args):
		return "arg_pyobj_%d" % i

	def begin_convert_args(self, args):
		arg_count = len(args)

		if arg_count > 0:
			self._source += "if (!PyTuple_Check(args) || (PyTuple_Size(args) != %d)) {\n" % arg_count
			self.raise_exception(None, 'invalid arguments object')
			self._source += "	return NULL;\n"
			self._source += "}\n"

			for i in range(arg_count):
				self._source += "PyObject *%s = PyTuple_GetItem(args, %d);\n" % (self.get_arg(i, args), i)

			self._source += '\n'

	# function call return values
	def return_void_from_c(self):
		return 'return 0;'

	def rval_from_c_ptr(self, ctype, var, conv, rval_p):
		self._source += conv.from_c_call(var + '_pyobj', rval_p, conv.get_ownership_policy(ctype.get_ref()))

	def commit_rvals(self, rval):
		rval_count = 1 if repr(rval) != 'void' else 0

		if rval_count == 0:
			self._source += 'Py_INCREF(Py_None);\nreturn Py_None;\n'
		elif rval_count == 1:
			self._source += 'return rval_pyobj;\n'
		else:
			self._source += '// TODO make tuple, append rvals, return tuple\n'

	#
	def output_module_functions_table(self):
		table_name = '%s_Methods' % self._name
		self._source += "static PyMethodDef %s[] = {\n" % table_name

		rows = []
		for f in self._bound_functions:
			rows.append('	{"%s", %s, METH_VARARGS, "TODO doc"}' % (f['bound_name'][1:], f['bound_name']))
		rows.append('	{NULL, NULL, 0, NULL} /* Sentinel */')

		self._source += ',\n'.join(rows) + '\n'
		self._source += "};\n\n"
		return table_name

	def output_module_definition(self, methods_table):
		def_name = '%s_module' % self._name
		self._source += 'static struct PyModuleDef %s = {\n' % def_name
		self._source += '	PyModuleDef_HEAD_INIT,\n'
		self._source += '	"%s", /* name of module */\n' % self._name
		self._source += '	"TODO doc", /* module documentation, may be NULL */\n'
		self._source += '	-1, /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */\n'
		self._source += '	%s\n' % methods_table
		self._source += '};\n\n'
		return def_name

	def output_module_init_function(self, module_def):
		self._source += 'PyMODINIT_FUNC PyInit_%s(void) {\n' % self._name
		self._source += '	PyObject *m;\n'

		self._source += '''
	m = PyModule_Create(&%s);
	if (m == NULL)
		return NULL;

''' % module_def

		# finalize bound types
		self._source += '	// custom types finalization\n'
		for conv in self._bound_types:
			self._source += conv.finalize_type()

		self._source += '''\
	return m;
}
\n'''

	def finalize(self):
		self._source += '// Module definitions starts here.\n\n'

		# self.output_summary()

		methods_table = self.output_module_functions_table()
		module_def = self.output_module_definition(methods_table)

		super().finalize()

		self.output_module_init_function(module_def)
