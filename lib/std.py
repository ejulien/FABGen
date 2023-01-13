# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

class VectorSequenceFeature:
	def __init__(self, wrapped_conv):
		self.wrapped_conv = wrapped_conv

	def get_size(self, self_var, out_var):
    		
		''' It returns a string that contains the C++ code to get the size of a vector
		
		:param self_var: the name of the variable that represents the object
		:param out_var: the variable to store the output in
		:return: The size of the array. '''
		
		return '%s = %s->size();\n' % (out_var, self_var)

	def get_item(self, self_var, idx, out_var, error_var):
    		
		''' If the size of the list is greater than zero and the index is less than the size of the list, then
		set the output variable to the value of the list at the given index, otherwise set the error
		variable to true
		
		:param self_var: the name of the variable that holds the vector
		:param idx: the index of the item to get
		:param out_var: The variable to store the output in
		:param error_var: The name of the variable that will be set to true if the index is out of bounds
		:return: A string. '''
		
		out = 'if ((%s->size() > 0) && (size_t(%s) < %s->size()))\n' % (self_var, idx, self_var)
		out += '	%s = (*%s)[%s];\n' % (out_var, self_var, idx)
		out += 'else\n'
		out += '	%s = true;\n' % error_var
		return out

	def set_item(self, self_var, idx, in_var, error_var):
    		
		''' It takes a variable, an index, and a value, and sets the value at the index in the variable
		
		:param self_var: the name of the variable that holds the vector
		:param idx: the index of the item to set
		:param in_var: The variable to be set
		:param error_var: The name of the variable that will be set to true if an error occurs
		:return: A string. '''
		
		t_in_var = self.wrapped_conv.prepare_var_from_conv(in_var, self.wrapped_conv.ctype.get_ref())
		out = 'if ((%s->size() > 0) && (size_t(%s) < %s->size()))\n' % (self_var, idx, self_var)
		out += '	(*%s)[%s] = %s;\n' % (self_var, idx, t_in_var)
		out += 'else\n'
		out += '	%s = true;\n' % error_var
		return out
