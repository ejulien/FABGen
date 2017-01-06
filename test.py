import lua

lua = lua.LuaGenerator()
lua.start("gs")

lua.bind_function('add', 'int', ['int a', 'int'])
lua.bind_function('set_name', 'void', ['const char *'])
lua.bind_function('get_name', 'const char *', ['void'])

lua.bind_function('add_by_ref', 'int', ['int &', 'int &'])
lua.bind_function('add_by_ptr', 'int', ['int *', 'int *'])

#lua.bind_class('simple_struct', None, None, None)

header, source = lua.get_output()

print(header)
print(source)
