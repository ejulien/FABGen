def bind_std(gen, PythonTypeConverterCommon):
	class PythonBoolConverter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def output_type_glue(self, module_name, members, methods):
			return 'bool check_%s(PyObject *o) { return PyBool_Check(o) ? true : false; }\n' % self.clean_name +\
			'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = o == Py_True; }\n' % (self.clean_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyBool_FromLong(*((%s*)obj)); }\n' % (self.clean_name, self.ctype)

	gen.bind_type(PythonBoolConverter('bool'))

	class PythonIntConverter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def output_type_glue(self, module_name, members, methods):
			return 'bool check_%s(PyObject *o) { return PyLong_Check(o) ? true : false; }\n' % self.clean_name +\
			'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyLong_AsLong(o); }\n' % (self.clean_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyLong_FromLong(*((%s*)obj)); }\n' % (self.clean_name, self.ctype)

	gen.bind_type(PythonIntConverter('int'))

	class PythonFloatConverter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def output_type_glue(self, module_name, members, methods):
			return 'bool check_%s(PyObject *o) { return PyFloat_Check(o) ? true : false; }\n' % self.clean_name +\
			'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyFloat_AsDouble(o); }\n' % (self.clean_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyFloat_FromDouble(*((%s*)obj)); }\n' % (self.clean_name, self.ctype)

	gen.bind_type(PythonFloatConverter('float'))

	class PythonConstCharPtrConverter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def output_type_glue(self, module_name, members, methods):
			return 'bool check_%s(PyObject *o) { return PyUnicode_Check(o) ? true : false; }\n' % self.clean_name +\
			'''void to_c_%s(PyObject *o, void *obj) {
PyObject *utf8_pyobj = PyUnicode_AsUTF8String(o);
*((%s*)obj) = PyBytes_AsString(utf8_pyobj);
Py_DECREF(utf8_pyobj);
}
''' % (self.clean_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyUnicode_FromString(*((%s*)obj)); }\n' % (self.clean_name, self.ctype)

	gen.bind_type(PythonConstCharPtrConverter('const char *'))
