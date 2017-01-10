import gen


#
class PythonTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type):
		super().__init__(type)


class PythonNativeTypeConverter(PythonTypeConverterCommon):
	def __init__(self, type):
		super().__init__(type)

	def to_c_ptr(self, var, var_p):
		return '%s(%s, %s);\n' % (self.to_c, var, var_p)

	def from_c_ptr(self, var, var_p):
		return "PyObject *%s = %s(%s, ByValue);\n" % (var, self.from_c, var_p)


#
class PythonGenerator(gen.FABGen):
	def output_includes(self):
		super().output_includes()

		self._source += '''#define Py_LIMITED_API // ensure a single build for Python 3.x (with x>2)
#include "Python.h"
\n'''

	def start(self, module_name, namespace = None):
		super().start(module_name, namespace)

		# templates for class type exchange
		self.insert_code('''
// wrap a C object
template<typename NATIVE_OBJECT_WRAPPER_T> int _wrap_obj(void *obj, const char *type_tag)
{
	auto p = lua_newuserdata(L, sizeof(NATIVE_OBJECT_WRAPPER_T));
	if (!p)
		return 0;

	new (p) NATIVE_OBJECT_WRAPPER_T(obj, type_tag);
	return 1;
}

class PythonReference
{
public:
	PythonReference(PyObject *o_) : o(o_) {}
	~PythonReference() { Py_DECREF(o); }

	operator PyObject *() const { return o; }

private:
	PyObject *o;
};

''', True, False)

		# bind basic types
		class PythonIntConverter(PythonNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return PyLong_Check(o) ? true : false;"
				self.tmpl_to_c = "*obj = PyLong_AsLong(o);"
				self.tmpl_from_c = "return PyLong_FromLong(*obj);"

		self.bind_type(PythonIntConverter('int'))

		class PythonFloatConverter(PythonNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return PyFloat_Check(o) ? true : false;"
				self.tmpl_to_c = "*obj = PyFloat_AsDouble(o);"
				self.tmpl_from_c = "return PyFloat_FromDouble(*obj);"

		self.bind_type(PythonFloatConverter('float'))

		class PythonStringConverter(PythonNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return PyUnicode_Check(o) ? true : false;"
				self.tmpl_to_c = "*obj = PyUnicode_AS_DATA(o);"
				self.tmpl_from_c = "return PyUnicode_FromString(obj->c_str());"

		self.bind_type(PythonStringConverter('std::string'))

		class PythonConstCharPtrConverter(PythonNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return PyUnicode_Check(o) ? true : false;"
				self.tmpl_to_c = "*obj = PyUnicode_AS_DATA(o);"
				self.tmpl_from_c = "return PyUnicode_FromString(*obj);"

		self.bind_type(PythonConstCharPtrConverter('const char *'))

	def proto_check(self, name, ctype):
		return 'bool %s(PyObject *o)' % (name)

	def proto_to_c(self, name, ctype):
		return 'void %s(PyObject *o, %s *obj)' % (name, gen.get_fully_qualified_ctype_name(ctype))

	def proto_from_c(self, name, ctype):
		return 'PyObject *%s(%s *obj, OwnershipPolicy own_policy)' % (name, gen.get_fully_qualified_ctype_name(ctype))

	def new_function(self, name, args):
		return "static PyObject *%s(PyObject *self, PyObject *args) {\n" % name

	def get_arg(self, i, args):
		return "arg_pyobj[%d]" % i

	# function call return values
	def begin_convert_rvals(self):
		pass

	def rval_from_c_ptr(self, rval, var, conv, rval_p):
		self._source += conv.from_c_ptr(var + '_pyobj', rval_p)

	def commit_rvals(self, rvals, rval_names):
		rval_count = len(rvals)

		if rval_count == 0:
			self._source += 'Py_INCREF(Py_None);\nreturn Py_None;\n'
		elif rval_count == 1:
			self._source += 'return %s_pyobj;\n' % rval_names[0]
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
		self._source += '	return PyModule_Create(&%s);\n' % module_def
		self._source += '}\n\n'

	def finalize(self):
		self._source += '// Module definitions starts here.\n\n'

		# self.output_summary()

		methods_table = self.output_module_functions_table()
		module_def = self.output_module_definition(methods_table)

		super().finalize()

		if self._namespace:
			module_def = '%s::%s' % (self._namespace, module_def)

		self.output_module_init_function(module_def)
