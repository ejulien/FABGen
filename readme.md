# Fabgen - The fabulous generator

Fabgen is a set of Python scripts to generate C++ binding code to different languages (CPython 3.2+ only at the moment).

## License

Fabgen is MIT licensed.

## Goals

1. Support multiple target language.
1. Bidirectional binding. Bind C function to target language and target language function to C function.
1. Provide an API for embedding (runtime C type name to target name query, human-readable type conversion functions, etc...).

## Philosophy

1. Any feature that can be done using what's available should be culled (aka. no feature creep).
1. Keep as much code as possible on the generic part of the generator.
1. KISS

## Features

- Customizable type conversion from C/C++ and back.
- Can bind most C/C++ constructions.
- User specifiable bound name.
- Types can hidden in the generated binding.
- Simple and hopefully easy to dive into codebase.

### Supported target language

- CPython 3.2+ using the CPython limited API (`Py_Limited_API`) so that generated modules can be used on all Python 3.2+ versions of CPython.

## Contributions

All contributions are most welcome

## Basic usage

TODO

### Extending through features.

Type converters can be augmented with features:

- 'proxy': Class

Types using this feature are declared as wrapper for another underlying type.
This feature is used to unwrap arguments to a call or wrap its return value.

Support for std::shared_ptr is done with the proxy feature.

- 'sequence': Class

Provide native access for the target language to values stored in a container type.

Function calls can specify features:

- 'route': def router(var, args)

This feature redirects an object method (static or not) to a function with a compatible signature.
It can be used to extend classes with additional methods while not modifying the existing C++ class.

- 'argout': []

Dictionary of argument names to consider as output to the bound function.
Output arguments do not take part in overload resolution and are not provided by the function caller.

Argout arguments are appended to the function return value.
