# Fabgen - The fabulous generator

Fabgen is a set of Python scripts to generate C++ binding code to different languages (CPython 3.2+ only at the moment).
It was written as a SWIG replacement for the Harfang Multimedia Framework (http://www.harfang3d.com).

## Author

Fabgen is written and maintained by Emmanuel Julien for the Harfang Multimedia Framework (http://www.harfang3d.com).

## License

Fabgen is licensed under the GPLv3.

## Goals

1. Support multiple target language.
1. Bidirectional binding. Bind C function to target language and target language function to C function.
1. Provide an API for embedding (runtime C type name to target name query, human-readable type conversion functions, etc...).

## Philosophy

1. Any feature that can be done using what's available should be culled (aka. no feature creep).
1. Keep as much code as possible on the generic part of the generator.
1. Support for more complex transformation should be written over the current API if possible.

## Features

- Customizable type conversion from C/C++ and back.
- Can bind most C/C++ constructions.
- User specifiable bound name.
- Types can hidden in the generated binding.
- Simple and hopefully easy to dive into codebase.

### Supported target language

- CPython 3.2+ using the CPython limited API (`Py_Limited_API`) so that generated modules can be used on all Python 3.2+ versions of CPython.

## Contributions

Contributions are welcome. Please submit merge requests with working unit test to the project Github directly.

## Basic usage

TODO

## Extending through feature

Type converters and function prototypes all accept a list or dictionary of features when declared.

### Extending type converter with feature

- 'proxy': class ProxyFeature

Types using this feature are declared as wrapper for another underlying type.
This feature is used to unwrap arguments to a call and wrap its return value.

Note: A type converter proxy feature is consumed by prototypes proxy feature, see the prototype feature documentation.

Support for std::shared_ptr is done with the proxy feature.

```python
class StdSharedPtrProxyFeature:
    def __init__(self, wrapped_conv):
        self.wrapped_conv = wrapped_conv

    def init_type_converter(self, gen, conv):
        # declare shared_ptr<T> to T cast support
        gen.add_cast(conv, self.wrapped_conv, lambda in_var, out_var: '%s = ((%s *)%s)->get();\n' % (out_var, conv.ctype, in_var))

    def unwrap(self, in_var, out_var):
        return '%s = %s->get();\n' % (out_var, in_var)

    def wrap(self, in_var, out_var):
        return '%s = new std::shared_ptr<%s>(%s);\n' % (out_var, self.wrapped_conv.ctype, in_var)
```

- 'sequence': Class

Provide native access for the target language to values stored in a container type.

### Extending function prototype with feature

- 'route': def router(var, args)

This feature redirects an object method (static or not) to a function with a compatible signature.
It can be used to extend classes with additional methods while not modifying the existing C++ class.

- 'arg_out': []

Dictionary of argument names to consider as output to the bound function.
Output arguments do not take part in overload resolution and are not provided by the function caller.

Argout arguments are appended to the function return value.

- 'proxy': None

Route a method call to the type wrapped by the 'proxy' feature of the converter used of the declaration.
This feature does not provide any value.
This feature can be used to wrap constructors.

```python
# With shared_ptr_to_obj_conv being a TypeConverter with a proxy feature,
# call the PrintState method through the shared pointer.
gen.bind_method(shared_ptr_to_obj_conv, 'PrintState', 'void', [], features=['proxy'])
```

- 'new_obj': None

By default, values returned by reference or pointer are assumed C++ ownership.
This feature transfers the returned object ownership to the target language.

- 'check_rval': def check(rvals):

Insert return value checking code right after the native call.
