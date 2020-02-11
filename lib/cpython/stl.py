# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

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


def bind_function_T(gen, type, bound_name=None):
	class PythonStdFunctionConverter(lang.cpython.PythonTypeConverterCommon):
		def get_type_glue(self, gen, module_name):
			func = self.ctype.scoped_typename.parts[-1].template.function

			# check C
			check = 'bool %s(PyObject *o) { return PyCallable_Check(o) ? true : false; }\n' % self.check_func

			# to C
			rval = 'void' if hasattr(func, 'void_rval') else str(func.rval)

			args = []
			if hasattr(func, 'args'):
				args = [str(arg) for arg in func.args]

			rbind_helper = '_rbind_' + self.bound_name  # helper to call from C to Lua
			parms = ['%s v%d' % (arg, idx) for idx, arg in enumerate(args)]
			gen.rbind_function(rbind_helper, rval, parms, True)

			to_c = '''\
void %s(PyObject *o, void *obj) {
	auto ref = std::make_shared<PythonValueRef>(o);
	*((%s*)obj) = [=](%s) -> %s {
''' % (self.to_c_func, self.ctype, ', '.join(['%s v%d' % (parm, idx) for idx, parm in enumerate(args)]), rval)

			if rval != 'void':
				to_c += '		return '

			if len(args) > 0:
				to_c += '%s(ref->Get(), %s);\n' % (gen.apply_api_prefix(rbind_helper), ', '.join(['v%d' % idx for idx in range(len(args))]))
			else:
				to_c += '%s(ref->Get());\n' % gen.apply_api_prefix(rbind_helper)

			to_c += '''\
	};
}
'''

			# from C
			from_c = '''\
PyObject *%s(void *obj, OwnershipPolicy) {
	Py_INCREF(Py_None);
	return Py_None; // TODO
}
''' % (self.from_c_func)

			return check + to_c + from_c

	return gen.bind_type(PythonStdFunctionConverter(type))


class PySequenceToStdVectorConverter(lang.cpython.PythonTypeConverterCommon):
	def __init__(self, type, T_conv):
		native_type = 'std::vector<%s>' % T_conv.ctype
		super().__init__(type, native_type, None, native_type)
		self.T_conv = T_conv

	def get_type_glue(self, gen, module_name):
		out = 'bool %s(PyObject *o) { return PySequence_Check(o) ? true : false; }\n' % self.check_func

		type_ = ('%s*' % self.T_conv.ctype) if self.T_conv.ctype.is_pointer() else self.T_conv.to_c_storage_ctype
		
		out += '''void %s(PyObject *o, void *obj) {
	std::vector<%s> *sv = (std::vector<%s> *)obj;

	Py_ssize_t size = PySequence_Length(o);
	sv->resize(size);
	for (Py_ssize_t i = 0; i < size; ++i) {
		PyObject *itm = PySequence_GetItem(o, i);
		%s v;
		%s(itm, &v);
		(*sv)[i] = %s;
		Py_DECREF(itm);
	}
}\n''' % (self.to_c_func, self.T_conv.ctype, self.T_conv.ctype, type_, self.T_conv.to_c_func, self.T_conv.prepare_var_from_conv('v', ''))

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
