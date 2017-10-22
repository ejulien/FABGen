import lang.cpython


def bind_stl(gen):
	gen.add_include('vector', True)

	gen.add_include('string', True)

	class PythonStringConverter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return PyUnicode_Check(o) ? true : false; }\n' % self.check_func +\
			'''void %s(PyObject *o, void *obj) {
PyObject *utf8_pyobj = PyUnicode_AsUTF8String(o);
*((%s*)obj) = PyBytes_AsString(utf8_pyobj);
Py_DECREF(utf8_pyobj);
}
''' % (self.to_c_func, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyUnicode_FromString(((%s*)obj)->c_str()); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonStringConverter('std::string'))


class PySequenceToStdVectorConverter(lang.cpython.PythonTypeConverterCommon):
	def __init__(self, type, T_conv):
		native_type = 'std::vector<%s>' % T_conv.ctype
		super().__init__(type, native_type, None, native_type)
		self.T_conv = T_conv

	def get_type_glue(self, gen, module_name):
		out = 'bool %s(PyObject *o) { return PySequence_Check(o) ? true : false; }\n' % self.check_func

		out += '''void %s(PyObject *o, void *obj) {
	std::vector<%s> *sv = (std::vector<%s> *)obj;

	int size = PySequence_Length(o);
	sv->resize(size);
	for (int i = 0; i < size; ++i) {
		PyObject *itm = PySequence_GetItem(o, i);
		%s v;
		to_c_%s(itm, &v);
		(*sv)[i] = %s;
		Py_DECREF(itm);
	}
}\n''' % (self.to_c_func, self.T_conv.ctype, self.T_conv.ctype, self.T_conv.arg_storage_ctype, self.T_conv.to_c_func, self.T_conv.prepare_var_from_conv('v', ''))

		out += '''PyObject *%s(void *obj, OwnershipPolicy) {
	std::vector<%s> *sv = (std::vector<%s> *)obj;

	size_t size = sv->size();
	PyObject *out = PyList_New(size);
	for (size_t i = 0; i < size; ++i) {
		PyObject *p = %s(&sv->at(i), Copy);
		PyList_SetItem(out, i, p);
	}
	return out;
}\n''' % (self.from_c_func, self.T_conv.ctype, self.T_conv.ctype, self.T_conv.from_c_func)
		return out
