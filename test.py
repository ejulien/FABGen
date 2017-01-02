import bind
import lua


lua.install()











#['int', 'const float *']  # define this type map, 'to_c' takes a script iterable object and should prepare an int and a const float *
#transform_to_c(['int', 'int', 'float *'])  # should become ['int', 'int $and$ const_float *']






bind.bind_struct('simple_struct')


bind.bind_function('add', 'int', ['int a', 'int'])
bind.bind_function('set_name', 'void', ['const char *'])
bind.bind_function('get_name', 'const char *', ['void'])

bind.bind_function('add_by_ref', 'int', ['int &', 'int &'])
bind.bind_function('add_by_ptr', 'int', ['int *', 'int *'])



header, source = bind.get_output()

print(header)
print(source)
