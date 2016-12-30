import bind
import lua


lua.install()

bind.bind_function('add', 'int', ['int', 'int'])
bind.bind_function('set_name', 'void', ['const char *'])
bind.bind_function('get_name', 'const char *', ['void'])


header, source = bind.get_output()

print(header)
print(source)
