import os
import sys
import importlib

import argparse

import lang.lua
import lang.cpython

import lib.std
import lib.stl
import lib


parser = argparse.ArgumentParser(description='FabGen binding script')
parser.add_argument("script", nargs=1)
parser.add_argument('--lua', help='Bind to Lua 5.2+', action="store_true")
parser.add_argument('--cpython', help='Bind to CPython', action="store_true")
parser.add_argument('--out', help='Path to output generated files', required=True)
args = parser.parse_args()


def output_binding(gen):
	script.bind(gen)

	hdr, src = gen.get_output()

	with open(os.path.join(args.out, 'bind_%s.h' % gen.get_language()), mode='w', encoding='utf-8') as f:
		f.write(hdr)
	with open(os.path.join(args.out, 'bind_%s.cpp' % gen.get_language()), mode='w', encoding='utf-8') as f:
		f.write(src)


# load binding script
split = os.path.split(args.script[0])
path = split[0]
mod = os.path.splitext(split[1])[0]

sys.path.append(path)
script = importlib.import_module(mod)


# execute through generators
if args.cpython:
	output_binding(lang.cpython.CPythonGenerator())

if args.lua:
	output_binding(lang.lua.LuaGenerator())
