import importlib
import tempfile
import subprocess
import argparse
import shutil
import lib
import sys
import os

import lang.cpython
import lang.lua


start_path = os.path.dirname(__file__)

parser = argparse.ArgumentParser(description='Run generator unit tests.')
parser.add_argument('--pybase', dest='python_base_path', help='Specify the base path of the Python interpreter location')
parser.add_argument('--sdkbase', dest='sdk_base_path', help='Specify the base path of the Harfang SDK')
parser.add_argument('--debug', dest='debug_test', help='Generate a working solution to debug a test')
parser.add_argument('--x64', dest='x64', help='Build for 64 bit architecture', action='store_true', default=False)

args = parser.parse_args()

# -- interpreter settings
if args.python_base_path:
	python_include_dir = args.python_base_path + '/' + 'include'
	python_library = args.python_base_path + '/' + 'libs/python3.lib'
	python_site_package = args.python_base_path + '/' + 'Lib/site-packages'
	python_interpreter = args.python_base_path + '/' + 'python.exe'


# -- CMake generator
if args.x64:
	cmake_generator = 'Visual Studio 15 2017 Win64'
else:
	cmake_generator = 'Visual Studio 15 2017'

print("Using CMake generator: %s" % cmake_generator)

msvc_arch = 'x64' if args.x64 else 'Win32'


# --
run_test_list = []
failed_test_list = []


def run_test(gen, name, testbed):
	work_path = tempfile.mkdtemp()
	print('Working directory is ' + work_path)

	test_module = importlib.import_module(name)

	# generate the interface file
	header, source = test_module.bind_test(gen)

	header_path = os.path.join(work_path, 'test_module.h')
	source_path = os.path.join(work_path, 'test_module.cpp')

	with open(header_path, 'w') as file:
		file.write(header)
	with open(source_path, 'w') as file:
		file.write(source)

	run_test_list.append(name)
	result = testbed.build_and_test_extension(work_path, test_module)

	if result:
		print("[OK]")
	else:
		print("[FAILED]")
		failed_test_list.append(name)

	if args.debug_test:
		subprocess.Popen('explorer "%s"' % work_path)
	else:
		shutil.rmtree(work_path, ignore_errors=True)


def run_tests(gen, names, testbed):
	print("Starting tests with fabgen generator %s" % gen.get_language())

	test_count = len(names)
	print("Running %d tests\n" % test_count)

	for i, name in enumerate(names):
		print('[%d/%d] Running test "%s"' % (i+1, test_count, name))
		run_test(gen, name, testbed)
		print('')

	run_test_count = len(run_test_list)
	failed_test_count = len(failed_test_list)

	print("[Test summary: %d run, %d failed]" % (run_test_count, failed_test_count))
	print("Done with fabgen generator %s" % gen.get_language())


# CPython test bed
def create_cpython_cmake_file(module, work_path, site_package, include_dir, python_lib):
	cmake_path = os.path.join(work_path, 'CMakeLists.txt')

	with open(cmake_path, 'w') as file:
		file.write('''
cmake_minimum_required(VERSION 3.1)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/")

project(%s)
enable_language(C CXX)

add_library(my_test SHARED test_module.cpp)
set_target_properties(my_test PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELWITHDEBINFO "%s" RUNTIME_OUTPUT_DIRECTORY_RELEASE "%s" SUFFIX .pyd)
target_include_directories(my_test PRIVATE "%s")
target_link_libraries(my_test "%s")
''' % (module, site_package, site_package, include_dir, python_lib))


def build_and_deploy_cpython_extension(work_path, build_path, python_interpreter):
	print("Generating build system...")
	try:
		subprocess.check_output('cmake .. -G "%s"' % cmake_generator)
	except subprocess.CalledProcessError as e:
		print(e.output.decode('utf-8'))
		return False

	if args.debug_test:
		with open(os.path.join(build_path, 'my_test.vcxproj.user'), 'w') as file:
			file.write('''\
<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="12.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='RelWithDebInfo|%s'">
    <LocalDebuggerCommand>%s</LocalDebuggerCommand>
    <DebuggerFlavor>WindowsLocalDebugger</DebuggerFlavor>
    <LocalDebuggerCommandArguments>test.py</LocalDebuggerCommandArguments>
    <LocalDebuggerWorkingDirectory>%s</LocalDebuggerWorkingDirectory>
  </PropertyGroup>
</Project>''' % (msvc_arch, python_interpreter, work_path))

	print("Building extension...")
	try:
		subprocess.check_output('cmake --build . --config Release')
	except subprocess.CalledProcessError as e:
		print(e.output.decode('utf-8'))
		return False

	return True


class CPythonTestBed:
	def build_and_test_extension(self, work_path, module):
		create_cpython_cmake_file("test", work_path, python_site_package, python_include_dir, python_library)
		create_clang_format_file(work_path)

		build_path = os.path.join(work_path, 'build')
		os.mkdir(build_path)
		os.chdir(build_path)

		if not build_and_deploy_cpython_extension(work_path, build_path, python_interpreter):
			return False

		# run test to assert extension correctness
		test_path = os.path.join(work_path, 'test.py')
		with open(test_path, 'w') as file:
			file.write(module.test_python)

		print("Executing Python test...")
		os.chdir(work_path)

		success = True
		try:
			subprocess.check_output('%s -m test' % python_interpreter)
		except subprocess.CalledProcessError as e:
			print(e.output.decode('utf-8'))
			success = False

		print("Cleanup...")

		return success


# Lua test bed
def create_lua_cmake_file(module, work_path, sdk_path):
	cmake_path = os.path.join(work_path, 'CMakeLists.txt')

	with open(cmake_path, 'w') as file:
		file.write('''
cmake_minimum_required(VERSION 3.1)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/")

project(%s)
enable_language(C CXX)

link_directories("%s/lib/Debug")

#add_definitions(-DLUA_USE_APICHECK)
add_library(my_test SHARED test_module.cpp)
set_target_properties(my_test PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG %s)
target_include_directories(my_test PRIVATE %s/include/lua)
target_link_libraries(my_test lua)
''' % (module, sdk_path, work_path.replace('\\', '/'), sdk_path))


def build_and_deploy_lua_extension(work_path, build_path):
	print("Generating build system...")
	try:
		subprocess.check_output('cmake .. -G "%s"' % cmake_generator)
	except subprocess.CalledProcessError as e:
		print(e.output.decode('utf-8'))
		return False

	# deploy Lua runtime from the SDK to the work folder
	shutil.copyfile(args.sdk_base_path + '/bin/Debug/lua.exe', os.path.join(work_path, 'lua.exe'))
	shutil.copyfile(args.sdk_base_path + '/bin/Debug/lua53.dll', os.path.join(work_path, 'lua53.dll'))

	if args.debug_test:
		with open(os.path.join(build_path, 'my_test.vcxproj.user'), 'w') as file:
			file.write('''\
<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="12.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='Debug|%s'">
    <LocalDebuggerCommand>lua.exe</LocalDebuggerCommand>
    <DebuggerFlavor>WindowsLocalDebugger</DebuggerFlavor>
    <LocalDebuggerCommandArguments>test.lua</LocalDebuggerCommandArguments>
    <LocalDebuggerWorkingDirectory>%s</LocalDebuggerWorkingDirectory>
  </PropertyGroup>
</Project>''' % (msvc_arch, work_path))

	print("Building extension...")
	try:
		subprocess.check_output('cmake --build . --config Debug')
	except subprocess.CalledProcessError as e:
		print(e.output.decode('utf-8'))
		return False

	return True


class LuaTestBed:
	def build_and_test_extension(self, work_path, module):
		create_lua_cmake_file("test", work_path, args.sdk_base_path)
		create_clang_format_file(work_path)

		build_path = os.path.join(work_path, 'build')
		os.mkdir(build_path)
		os.chdir(build_path)

		if not build_and_deploy_lua_extension(work_path, build_path):
			return False

		# run test to assert extension correctness
		test_path = os.path.join(work_path, 'test.lua')
		with open(test_path, 'w') as file:
			file.write(module.test_lua)

		print("Executing Lua test...")
		os.chdir(work_path)

		success = True
		try:
			subprocess.check_output('lua.exe test.lua', stderr=subprocess.STDOUT)
		except subprocess.CalledProcessError as e:
			print(e.output.decode('utf-8'))
			success = False

		print("Cleanup...")

		return success


# Clang format
def create_clang_format_file(work_path):
	with open(os.path.join(work_path, '_clang-format'), 'w') as file:
		file.write('''ColumnLimit: 0
UseTab: Always
TabWidth: 4
IndentWidth: 4
IndentCaseLabels: true
AccessModifierOffset: -4
AlignAfterOpenBracket: DontAlign
AlwaysBreakTemplateDeclarations: false
AlignTrailingComments: false''')


#
sys.path.append(os.path.join(start_path, 'tests'))

if args.debug_test:
	test_names = [args.debug_test]
else:
	test_names = [file[:-3] for file in os.listdir('./tests') if file.endswith('.py')]

if args.python_base_path:
	gen = lang.cpython.CPythonGenerator()
	gen.verbose = False
	run_tests(gen, test_names, CPythonTestBed())

if args.sdk_base_path:
	gen = lang.lua.LuaGenerator()
	gen.verbose = False
	run_tests(gen, test_names, LuaTestBed())
