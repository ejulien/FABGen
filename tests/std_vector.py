def bind_test(gen):
	gen.start('my_test')

	# inject test code in the wrapper
	gen.insert_code('''\
''', True, False)

	gen.add_include('vector', is_system=True)

	class StdVectorSequence:
		def __init__(self, wrapped_conv):
			self.wrapped_conv = wrapped_conv

		def init_type_converter(self, gen, conv):
			pass

		def get_size(self, self_var, out_var):
			return '%s = %s->size();\n' % (out_var, self_var)

		def get_item(self, self_var, idx, out_var):
			return '%s = %s->at(%s);\n' % (out_var, self_var, idx)

	std_vector_int = gen.begin_class('std::vector<int>', features={'sequence': StdVectorSequence(gen.get_conv('int'))})
	gen.bind_constructor(std_vector_int, [])

	gen.bind_method(std_vector_int, 'size', 'int', [])
	gen.bind_method(std_vector_int, 'push_back', 'void', ['int v'])
	gen.bind_method(std_vector_int, 'at', 'int&', ['int pos'])

	gen.end_class(std_vector_int)

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

from tests_api import expect_eq

#
#expect_eq(n.v, 4)

'''
