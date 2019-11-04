# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

import lang.cpython


def bind_std(gen):
	class PyObjectPtrTypeConverter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return true; }\n' % self.check_func +\
			'void %s(PyObject *o, void *obj) { *(void **)obj = o; }\n' % self.to_c_func +\
			'PyObject *%s(void *o, OwnershipPolicy) { return *(PyObject **)o; }\n' % self.from_c_func

	gen.bind_type(PyObjectPtrTypeConverter('PyObject *'))

	gen.add_include('cstdint', True)

	class PythonBoolConverter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return PyBool_Check(o) ? true : false; }\n' % self.check_func +\
			'void %s(PyObject *o, void *obj) { *((%s*)obj) = o == Py_True; }\n' % (self.to_c_func, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyBool_FromLong(*((%s*)obj)); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonBoolConverter('bool'))

	class PythonIntConverter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return PyLong_CheckExact(o) ? true : false; }\n' % self.check_func +\
			'void %s(PyObject *o, void *obj) { *((%s*)obj) = (%s)PyLong_AsLong(o); }\n' % (self.to_c_func, self.ctype, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyLong_FromLong(*((%s*)obj)); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonIntConverter('char'))
	gen.bind_type(PythonIntConverter('short'))
	gen.bind_type(PythonIntConverter('int'))
	gen.bind_type(PythonIntConverter('long'))
	gen.bind_type(PythonIntConverter('int8_t'))
	gen.bind_type(PythonIntConverter('int16_t'))
	gen.bind_type(PythonIntConverter('int32_t'))
	gen.bind_type(PythonIntConverter('char16_t'))
	gen.bind_type(PythonIntConverter('char32_t'))

	class PythonUnsignedIntConverter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return PyLong_CheckExact(o) ? true : false; }\n' % self.check_func +\
			'void %s(PyObject *o, void *obj) { *((%s*)obj) = (%s)PyLong_AsUnsignedLong(o); }\n' % (self.to_c_func, self.ctype, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyLong_FromUnsignedLong(*((%s*)obj)); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonUnsignedIntConverter('unsigned char'))
	gen.bind_type(PythonUnsignedIntConverter('unsigned short'))
	gen.bind_type(PythonUnsignedIntConverter('unsigned int'))
	gen.bind_type(PythonUnsignedIntConverter('unsigned long'))
	gen.bind_type(PythonUnsignedIntConverter('uint8_t'))
	gen.bind_type(PythonUnsignedIntConverter('uint16_t'))
	gen.bind_type(PythonUnsignedIntConverter('uint32_t'))

	class PythonInt64Converter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return PyLong_CheckExact(o) ? true : false; }\n' % self.check_func +\
			'void %s(PyObject *o, void *obj) { *((%s*)obj) = PyLong_AsLongLong(o); }\n' % (self.to_c_func, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyLong_FromLongLong(*((%s*)obj)); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonInt64Converter('int64_t'))

	class PythonUnsignedInt64Converter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return PyLong_CheckExact(o) ? true : false; }\n' % self.check_func +\
			'void %s(PyObject *o, void *obj) { *((%s*)obj) = PyLong_AsUnsignedLongLong(o); }\n' % (self.to_c_func, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyLong_FromUnsignedLongLong(*((%s*)obj)); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonUnsignedInt64Converter('uint64_t'))

	class PythonVoidPtrConverter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return PyLong_CheckExact(o) ? true : false; }\n' % self.check_func +\
			'void %s(PyObject *o, void *obj) { *((%s*)obj) = (%s)PyLong_AsVoidPtr(o); }\n' % (self.to_c_func, self.ctype, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyLong_FromVoidPtr((void *)(*((%s*)obj))); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonVoidPtrConverter('intptr_t'))

	class PythonSize_tConverter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return PyLong_CheckExact(o) ? true : false; }\n' % self.check_func +\
			'void %s(PyObject *o, void *obj) { *((%s*)obj) = PyLong_AsSize_t(o); }\n' % (self.to_c_func, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyLong_FromSize_t(*((%s*)obj)); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonSize_tConverter('size_t'))

	class PythonFloatConverter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			return 'bool %s(PyObject *o) { return PyFloat_Check(o) || PyLong_Check(o) ? true : false; }\n' % self.check_func +\
			'void %s(PyObject *o, void *obj) { *((%s*)obj) = (%s)PyFloat_AsDouble(o); }\n' % (self.to_c_func, self.ctype, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyFloat_FromDouble(*((%s*)obj)); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonFloatConverter('float'))
	gen.bind_type(PythonFloatConverter('double'))

	class PythonConstCharPtrConverter(lang.cpython.PythonTypeConverterCommon):
		def __init__(self, type, to_c_storage_type=None, bound_name=None, from_c_storage_type=None):
			super().__init__(type, to_c_storage_type, bound_name, from_c_storage_type, True)

		def get_type_glue(self, gen, module_name):
			return 'struct %s { std::string s; };\n' % self.c_storage_class +\
			'bool %s(PyObject *o) { return PyUnicode_Check(o) ? true : false; }\n' % self.check_func +\
			'''void %s(PyObject *o, void *obj, %s &storage) {
	PyObject *utf8_pyobj = PyUnicode_AsUTF8String(o);
	storage.s = PyBytes_AsString(utf8_pyobj);
	*((%s*)obj) = storage.s.data();
	Py_DECREF(utf8_pyobj);
}
''' % (self.to_c_func, self.c_storage_class, self.ctype) +\
			'PyObject *%s(void *obj, OwnershipPolicy) { return PyUnicode_FromString(*((%s*)obj)); }\n' % (self.from_c_func, self.ctype)

	gen.bind_type(PythonConstCharPtrConverter('const char *'))
