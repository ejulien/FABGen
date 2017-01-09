import gen


#
class PythonTypeConverterCommon(gen.TypeConverter):
	def __init__(self, type):
		super().__init__(type)

	def return_void_from_c(self):
		return 'return 0;'


class PythonNativeTypeConverter(PythonTypeConverterCommon):
	def __init__(self, type):
		super().__init__(type)

	def new_var(self, name):
		out = '%s %s;\n' % (gen.get_fully_qualified_ctype_name(self.ctype), name)
		return (out, '&%s' % name)

	def to_c_ptr(self, var, var_p):
		return '%s(%s, %s);\n' % (self.to_c, var, var_p)

	def from_c_ptr(self, var, var_p):
		return "PyObject *%s = %s(%s, ByValue);\n" % (var, self.from_c, var_p)


#
class PythonGenerator(gen.FABGen):
	def start(self, namespace = None):
		super().start(namespace)

		# templates for class type exchange
		self.insert_code('''
#define Py_LIMITED_API

#include "Python.h"

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
				self.tmpl_to_c = "*val = PyLong_AsLong(o);"
				self.tmpl_from_c = "return PyLong_FromLong(*val);"

		self.bind_type(PythonIntConverter('int'))

		class PythonFloatConverter(PythonNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return PyFloat_Check(o) ? true : false;"
				self.tmpl_to_c = "*val = PyFloat_AsDouble(o);"
				self.tmpl_from_c = "return PyFloat_FromDouble(*val);"

		self.bind_type(PythonFloatConverter('float'))

		class PythonStringConverter(PythonNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return PyUnicode_Check(o) ? true : false;"
				self.tmpl_to_c = "*val = PyUnicode_AS_DATA(o);"
				self.tmpl_from_c = "return PyUnicode_FromString(val->c_str());"

		self.bind_type(PythonStringConverter('std::string'))

		class PythonConstCharPtrConverter(PythonNativeTypeConverter):
			def __init__(self, type):
				super().__init__(type)
				self.tmpl_check = "return PyUnicode_Check(o) ? true : false;"
				self.tmpl_to_c = "*val = PyUnicode_AS_DATA(o);"
				self.tmpl_from_c = "return PyUnicode_FromString(*val);"

		self.bind_type(PythonConstCharPtrConverter('const char *'))

	def proto_check(self, name, ctype):
		return 'bool %s(PyObject *o)' % (name)

	def proto_to_c(self, name, ctype):
		return 'void %s(PyObject *o, %s *obj)' % (name, gen.get_fully_qualified_ctype_name(ctype))

	def proto_from_c(self, name, ctype):
		return 'PyObject *%s(%s *obj, OwnershipPolicy own_policy)' % (name, gen.get_fully_qualified_ctype_name(ctype))

	def new_function(self, name, args):
		return "static PyObject *%s(PyObject **arg_pyobj) {\n" % name

	def get_arg(self, i, args):
		return "arg_pyobj[%d]" % i

	def commit_rvals(self, rvals, rval_names):
		rval_count = len(rvals)

		if rval_count == 0:
			return 'return Py_None;\n'
		if rval_count == 1:
			return 'return %s;\n' % rval_names[0]

		return 'FIXME make tuple, append rvals, return tuple'
