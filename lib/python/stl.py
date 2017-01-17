def bind_stl(gen, PythonTypeConverterCommon):
	gen.add_include('string', True)

	class PythonStringConverter(PythonTypeConverterCommon):
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
			'PyObject *from_c_%s(void *obj) { return PyUnicode_FromString(((%s*)obj)->c_str()); }\n' % (self.clean_name, self.ctype)

	gen.bind_type(PythonStringConverter('std::string'))
