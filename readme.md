Features

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

They are appended to the function return value and returned as a tuple.
