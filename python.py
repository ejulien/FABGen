import gen
import lib.python.std as std
import lib.python.stl as stl


#
class PythonTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type, storage_type=None):
		super().__init__(type, storage_type)

	def get_type_api(self, module_name):
		return 'bool check_%s(PyObject *o);\n' % self.clean_name +\
		'void to_c_%s(PyObject *o, void *obj);\n' % self.clean_name +\
		'PyObject *from_c_%s(void *obj, OwnershipPolicy);\n' % self.clean_name

	def to_c_call(self, in_var, out_var_p):
		return 'to_c_%s(%s, %s);\n' % (self.clean_name, in_var, out_var_p)

	def from_c_call(self, out_var, in_var_p, ownership_policy):
		return "PyObject *%s = from_c_%s(%s, %s);\n" % (out_var, self.clean_name, in_var_p, ownership_policy)

	def check_call(self, in_var):
		return "check_%s(%s)" % (self.clean_name, in_var)


#
class PythonClassTypeDefaultConverter(PythonTypeConverterCommon):
	def __init__(self, type):
		super().__init__(type, type + '*')

	def get_type_glue(self, module_name):
		# type
		out = 'static PyObject *%s_type;\n\n' % self.clean_name

		# constructor
		out += 'static PyObject *%s_tp_new(PyTypeObject *subtype, PyObject *args, PyObject *kwds) {\n' % self.clean_name
		if self.constructor:
			out += '	return %s(NULL, args);\n' % self.constructor['proxy_name']
		else:
			out += '	PyErr_Format(PyExc_TypeError, "cannot create %s.%s instances");\n' % (module_name, self.clean_name)
			out += '	return NULL;\n'
		out += '}\n\n'

		# members
		out += 'static PyGetSetDef %s_tp_getset[] = {\n' % self.clean_name
		for member in self.members:
			out += '	{"%s", (getter)%s, (setter)%s, "TODO doc"},\n' % (member.name, '_%s_get_%s' % (self.clean_name, member.name), '_%s_set_%s' % (self.clean_name, member.name))
		out += '	{NULL} /* Sentinel */\n'
		out += '};\n\n'

		# methods
		out += 'static PyMethodDef %s_tp_methods[] = {\n' % self.clean_name
		for method in self.get_all_methods():
			out += '	{"%s", (PyCFunction)%s, METH_VARARGS},\n' % (method['name'], method['proxy_name'])
		out += '	{NULL} /* Sentinel */\n'
		out += '};\n\n'

		# slots
		out += 'static PyType_Slot %s_slots[] = {\n' % self.clean_name
		out += '	{Py_tp_new, &%s_tp_new},\n' % self.clean_name
		out += '	{Py_tp_doc, "TODO doc"},\n'
		out += '	{Py_tp_dealloc, &wrapped_PyObject_tp_dealloc},\n'
		out += '	{Py_tp_getset, &%s_tp_getset},\n' % self.clean_name
		out += '	{Py_tp_methods, &%s_tp_methods},\n' % self.clean_name
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
	wrapped_PyObject *w = cast_to_wrapped_PyObject(o);
	*(%s **)obj = (%s *)_type_tag_upcast(w->obj, w->type_tag, %s);
}\n\n''' % (self.clean_name, self.clean_name, self.clean_name, self.type_tag)

		out += '''PyObject *from_c_%s(void *obj, OwnershipPolicy own) {
	wrapped_PyObject *pyobj = PyObject_New(wrapped_PyObject, (PyTypeObject *)%s_type);
	if (own == Copy)
		obj = new %s(*(%s *)obj);
	init_wrapped_PyObject(pyobj, __%s_type_tag, obj);
	if (own != NonOwning)
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
	PyObject_HEAD;

	char magic[4]; // wrapped_PyObject marker
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

static wrapped_PyObject *cast_to_wrapped_PyObject(PyObject *o) {
	wrapped_PyObject *w = (wrapped_PyObject *)o;
	if (w->magic[0] != 'F' || w->magic[1] != 'A' || w->magic[2] != 'B' || w->magic[3] != '!')
		return NULL;
	return w;
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
	def set_error(self, type, reason):
		self._source += 'PyErr_SetString(PyExc_RuntimeError, "%s");\n' % reason

	#
	def open_getter_function(self, name):
		self._source += "static PyObject *%s(PyObject *_self, void *closure) {\n" % name
		return ['_self']

	def close_getter_function(self):
		self._source += '''\
FAB_error:
	return NULL;
}
'''

	def open_setter_function(self, name):
		self._source += "static int %s(PyObject *_self, PyObject *_val, void *closure) {\n" % name
		return ['_self', '_val']

	def close_setter_function(self):
		self._source += '''\
	return 0;
FAB_error:;
	return -1;
}
'''

	def get_arg(self, i):
		return 'arg_pyobj[%d]' % i

	def open_function(self, name, max_arg_count):
		self._source += "static PyObject *%s(PyObject *_self, PyObject *args) {\n" % name

		self._source += '\
	if (!PyTuple_Check(args)) {\n\
		PyErr_SetString(PyExc_RuntimeError, "invalid arguments object (expected a tuple)");\n\
		return NULL;\n\
	}\n\
\n\
	int arg_count = PyTuple_Size(args);\n\
\n\
	PyObject *arg_pyobj[%d];\n\
	for (int _i = 0; _i < arg_count; ++_i)\n\
		arg_pyobj[_i] = PyTuple_GetItem(args, _i);\n\
\n' % max_arg_count

	def close_function(self):
		self._source += '''\
FAB_error:;
	return NULL;
}
'''

	def open_method(self, name):
		# function and methods share the same signature in C Python API...
		arg_vars = self.open_function(name)
		# ...but the generator expects self as the first argument variable in the returned list.
		arg_vars.insert(0, '_self')
		return arg_vars

	def close_method(self):
		self.close_function()

	#
	def get_class_default_converter(self):
		return PythonClassTypeDefaultConverter

	# function call return values
	def return_void_from_c(self):
		return 'return 0;'

	def rval_from_c_ptr(self, ctype, var, conv, rval_p, ownership_policy):
		self._source += conv.from_c_call(var + '_pyobj', rval_p, ownership_policy)

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
			rows.append('	{"%s", %s, METH_VARARGS, "TODO doc"}' % (f['name'], f['proxy_name']))
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
