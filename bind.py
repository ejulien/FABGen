# FABGen - The FABulous binding Generator for CPython and Lua
#	Copyright (C) 2018 Emmanuel Julien

import os
import sys
import importlib
import time

import argparse

import lang.lua
import lang.cpython

import lib.std
import lib.stl
import lib

print('''FABGen Copyright (C) 2018 Emmanuel Julien
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions.''')

parser = argparse.ArgumentParser(description='FABGen')
parser.add_argument('script', nargs=1)
parser.add_argument('--lua', help='Bind to Lua 5.2+', action='store_true')
parser.add_argument('--cpython', help='Bind to CPython', action='store_true')
parser.add_argument('--out', help='Path to output generated files', required=True)
parser.add_argument('--prefix', help='Prefix to append to all public symbols')
parser.add_argument('--embedded', help='Specify that the generated binding is for embedding and not expanding the target language', action='store_true')
parser.add_argument('--doc_md_folder', type=str, help='Retrieve symbol documentation using its bound name from a folder containing an MD file for each documented symbol')
parser.add_argument('--no_fabgen_api', help='Do not generate the fabgen.h API file', action='store_true')
args = parser.parse_args()


def output_binding(gen):
	t_start = time.perf_counter()

	if args.embedded:
		print("Generating embedded binding code")
		gen.embedded = args.embedded

	script.bind(gen)

	hdr, src, api = gen.get_output()

	hdr_path = os.path.join(args.out, 'bind_%s.h' % gen.get_language())
	cpp_path = os.path.join(args.out, 'bind_%s.cpp' % gen.get_language())

	with open(hdr_path, mode='w', encoding='utf-8') as f:
		f.write(hdr)
	with open(cpp_path, mode='w', encoding='utf-8') as f:
		f.write(src)

	print('Files written as %s and %s' % (hdr_path, cpp_path))

	if not args.no_fabgen_api:
		api_path = os.path.join(args.out, 'fabgen.h')

		with open(api_path, mode='w', encoding='utf-8') as f:
			f.write(api)

		print('FABgen API written as %s' % api_path)
	else:
		print('FABgen API (fabgen.h) not written')

	print('Done in %f sec.' % (time.perf_counter() - t_start))


# load binding script
split = os.path.split(args.script[0])
path = split[0]
mod = os.path.splitext(split[1])[0]

sys.path.append(path)
script = importlib.import_module(mod)


# set prefix
if args.prefix:
	import gen
	gen.api_prefix = args.prefix


# setup documentation hook
def setup_gen(gen):
	if args.doc_md_folder:
		def md_doc_hook(name):
			symbol_md_path = os.path.join(args.doc_md_folder, name + '.md')

			try:
				with open(symbol_md_path, 'r') as file:
					lines = file.readlines()
					return '\n'.join(lines)
			except IOError:
				return ""

		gen.get_symbol_doc_hook = md_doc_hook

	return gen


# execute through generators
if args.cpython:
	output_binding(setup_gen(lang.cpython.CPythonGenerator()))

if args.lua:
	output_binding(setup_gen(lang.lua.LuaGenerator()))
