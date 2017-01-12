import gen


#
class PythonTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type, storage_type=None):
		super().__init__(type, storage_type)

	def output_type_api(self, module_name):
		return '// type API for %s\n' % self.fully_qualified_name +\
		'bool check_%s(PyObject *o);\n' % self.clean_name +\
		'void to_c_%s(PyObject *o, void *obj);\n' % self.clean_name +\
		'PyObject *from_c_%s(void *obj, OwnershipPolicy);\n' % self.clean_name

	def to_c_call(self, var, var_p):
		return 'to_c_%s(L, %s, %s);\n' % (self.clean_name, var, var_p)

	def from_c_call(self, ctype, var, var_p):
		return "from_c_%s(L, %s, %s);\n" % (self.clean_name, var_p, self.get_ownership_policy(ctype.get_ref()))


#
class PythonClassTypeDefaultConverter(gen.TypeConverter):
	def __init__(self, type):
		super().__init__(type, type + '*')

	def output_type_glue(self, module_name):
		out = '''typedef struct {
	PyObject_HEAD
} %s_PyObject;
''' % self.clean_name

		out += '''
static PyTypeObject %s_PyType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"%s.%s", /* tp_name */
	sizeof(%s_PyObject), /* tp_basicsize */
	0,  /* tp_itemsize */
	0, /* tp_dealloc */
	0, /* tp_print */
	0, /* tp_getattr */
	0, /* tp_setattr */
	0, /* tp_as_async */
	0, /* tp_repr */
	0, /* tp_as_number */
	0, /* tp_as_sequence */
	0, /* tp_as_mapping */
	0, /* tp_hash  */
	0, /* tp_call */
	0, /* tp_str */
	0, /* tp_getattro */
	0, /* tp_setattro */
	0, /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT, /* tp_flags */
	"FIXME DOC", /* tp_doc */
};
''' % (self.clean_name, module_name, self.bound_name, self.clean_name)

		out += '''
static bool Finalize_%s_Type() {
	%s_PyType.tp_new = PyType_GenericNew;
	return PyType_Ready(&%s_PyType) >= 0;
}
''' % (self.clean_name, self.clean_name, self.clean_name)

		return out

	def finalize_type(self):
		out = '''\
	%s_PyType.tp_new = PyType_GenericNew;
	if (PyType_Ready(&%s_PyType) < 0)
		return NULL;
	Py_INCREF(&%s_PyType);
	PyModule_AddObject(m, "%s", (PyObject *)&%s_PyType);

''' % (self.clean_name, self.clean_name, self.clean_name, self.bound_name, self.clean_name)
		return out


#
class PythonGenerator(gen.FABGen):
	def output_includes(self):
		super().output_includes()

		self._source += '''#define Py_LIMITED_API // ensure a single build for Python 3.x (with x>2)
#include "Python.h"
\n'''

	def start(self, module_name):
		super().start(module_name)

		# templates for class type exchange
		self.insert_code('''''', True, False)

		# bind basic types
		class PythonIntConverter(PythonTypeConverterCommon):
			def __init__(self, type):
				super().__init__(type)

			def output_type_glue(self, module_name):
				return 'bool check_%s(PyObject *o) { return PyLong_Check(o) ? true : false; }\n' % self.clean_name +\
				'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyLong_AsLong(o); }\n' % (self.clean_name, self.ctype) +\
				'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyLong_FromLong(*((%s*)obj)); }\n' % (self.clean_name, self.ctype)

		self.bind_type(PythonIntConverter('int'))

		class PythonFloatConverter(PythonTypeConverterCommon):
			def __init__(self, type):
				super().__init__(type)

			def output_type_glue(self, module_name):
				return 'bool check_%s(PyObject *o) { return PyFloat_Check(o) ? true : false; }\n' % self.clean_name +\
				'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyFloat_AsDouble(o); }\n' % (self.clean_name, self.ctype) +\
				'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyFloat_FromDouble(*((%s*)obj)); }\n' % (self.clean_name, self.ctype)

		self.bind_type(PythonFloatConverter('float'))

		class PythonStringConverter(PythonTypeConverterCommon):
			def __init__(self, type):
				super().__init__(type)

			def output_type_glue(self, module_name):
				return 'bool check_%s(PyObject *o) { return PyUnicode_Check(o) ? true : false; }\n' % self.clean_name +\
				'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyUnicode_AS_DATA(o); }\n' % (self.clean_name, self.ctype) +\
				'PyObject *from_c_%s(void *obj) { return PyUnicode_FromString(((%s*)obj)->c_str()); }\n' % (self.clean_name, self.ctype)

		self.bind_type(PythonStringConverter('std::string'))

		class PythonConstCharPtrConverter(PythonTypeConverterCommon):
			def __init__(self, type):
				super().__init__(type)

			def output_type_glue(self, module_name):
				return 'bool check_%s(PyObject *o) { return PyUnicode_Check(o) ? true : false; }\n' % self.clean_name +\
				'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyUnicode_AS_DATA(o); }\n' % (self.clean_name, self.ctype) +\
				'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyUnicode_FromString(*((%s*)obj)); }\n' % (self.clean_name, self.ctype)

		self.bind_type(PythonConstCharPtrConverter('const char *'))

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
			self._source += "if (!PyTuple_Check(args) || (PyTuple_GET_SIZE(args) != %d)) {\n" % arg_count
			self.raise_exception(None, 'invalid arguments object')
			self._source += "	return NULL;\n"
			self._source += "}\n"

			for i in range(arg_count):
				self._source += "PyObject *%s = PyTuple_GET_ITEM(args, %d);\n" % (self.get_arg(i, args), i)

			self._source += '\n'

	# function call return values
	def return_void_from_c(self):
		return 'return 0;'

	def rval_from_c_ptr(self, ctype, var, conv, rval_p):
		self._source += conv.from_c_call(ctype, var + '_pyobj', rval_p)

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
