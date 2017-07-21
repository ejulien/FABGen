def bind_std(gen, PythonTypeConverterCommon):
	class PythonBoolConverter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def get_type_glue(self, module_name):
			return 'bool check_%s(PyObject *o) { return PyBool_Check(o) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = o == Py_True; }\n' % (self.bound_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyBool_FromLong(*((%s*)obj)); }\n' % (self.bound_name, self.ctype)

	gen.bind_type(PythonBoolConverter('bool'))

	class PythonIntConverter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def get_type_glue(self, module_name):
			return 'bool check_%s(PyObject *o) { return PyLong_Check(o) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyLong_AsLong(o); }\n' % (self.bound_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyLong_FromLong(*((%s*)obj)); }\n' % (self.bound_name, self.ctype)

	gen.bind_type(PythonIntConverter('int'))
	gen.bind_type(PythonIntConverter('int8_t'))
	gen.bind_type(PythonIntConverter('int16_t'))
	gen.bind_type(PythonIntConverter('int32_t'))

	class PythonUnsignedIntConverter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def get_type_glue(self, module_name):
			return 'bool check_%s(PyObject *o) { return PyLong_Check(o) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyLong_AsUnsignedLong(o); }\n' % (self.bound_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyLong_FromUnsignedLong(*((%s*)obj)); }\n' % (self.bound_name, self.ctype)

	gen.bind_type(PythonUnsignedIntConverter('uint8_t'))
	gen.bind_type(PythonUnsignedIntConverter('uint16_t'))
	gen.bind_type(PythonUnsignedIntConverter('uint32_t'))

	class PythonInt64Converter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def get_type_glue(self, module_name):
			return 'bool check_%s(PyObject *o) { return PyLong_Check(o) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyLong_AsLongLong(o); }\n' % (self.bound_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyLong_FromLongLong(*((%s*)obj)); }\n' % (self.bound_name, self.ctype)

	gen.bind_type(PythonInt64Converter('int64_t'))

	class PythonUnsignedInt64Converter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def get_type_glue(self, module_name):
			return 'bool check_%s(PyObject *o) { return PyLong_Check(o) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyLong_AsUnsignedLongLong(o); }\n' % (self.bound_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyLong_FromUnsignedLongLong(*((%s*)obj)); }\n' % (self.bound_name, self.ctype)

	gen.bind_type(PythonUnsignedInt64Converter('uint64_t'))

	class PythonFloatConverter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def get_type_glue(self, module_name):
			return 'bool check_%s(PyObject *o) { return PyFloat_Check(o) ? true : false; }\n' % self.bound_name +\
			'void to_c_%s(PyObject *o, void *obj) { *((%s*)obj) = PyFloat_AsDouble(o); }\n' % (self.bound_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyFloat_FromDouble(*((%s*)obj)); }\n' % (self.bound_name, self.ctype)

	gen.bind_type(PythonFloatConverter('float'))

	class PythonConstCharPtrConverter(PythonTypeConverterCommon):
		def __init__(self, type):
			super().__init__(type)

		def get_type_glue(self, module_name):
			return 'bool check_%s(PyObject *o) { return PyUnicode_Check(o) ? true : false; }\n' % self.bound_name +\
			'''void to_c_%s(PyObject *o, void *obj) {
PyObject *utf8_pyobj = PyUnicode_AsUTF8String(o);
*((%s*)obj) = PyBytes_AsString(utf8_pyobj);
Py_DECREF(utf8_pyobj);
}
''' % (self.bound_name, self.ctype) +\
			'PyObject *from_c_%s(void *obj, OwnershipPolicy) { return PyUnicode_FromString(*((%s*)obj)); }\n' % (self.bound_name, self.ctype)

	gen.bind_type(PythonConstCharPtrConverter('const char *'))
