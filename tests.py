import importlib
import tempfile
import subprocess
import argparse
import shutil
import sys
import os

import python


start_path = os.path.dirname(__file__)


parser = argparse.ArgumentParser(description='Run generator unit tests.')
parser.add_argument('--pybase', dest='python_base_path', help='Specify the base path of the Python interpreter location', required=True)
parser.add_argument('--debug', dest='debug_test', help='Generate a working solution to debug a test')

args = parser.parse_args()

# -- interpreter settings
python_include_dir = args.python_base_path + '/' + 'include'
python_library = args.python_base_path + '/' + 'libs/python3.lib'
python_site_package = args.python_base_path + '/' + 'Lib/site-packages'
python_interpreter = args.python_base_path + '/' + 'python.exe'


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
	print("Starting tests with generator %s" % gen.get_langage())

	test_count = len(names)
	print("Running %d tests\n" % test_count)

	for i, name in enumerate(names):
		print('[%d/%d] Running test "%s"' % (i+1, test_count, name))
		run_test(gen, name, testbed)
		print('')

	run_test_count = len(run_test_list)
	failed_test_count = len(failed_test_list)

	print("[Test summary: %d run, %d failed]" % (run_test_count, failed_test_count))
	print("Done with generator %s" % gen.get_langage())


# --
# language CMake support
class PythonTestBed:
	def build_and_test_extension(self, work_path, module):
		cmake_path = os.path.join(work_path, 'CMakeLists.txt')

		with open(cmake_path, 'w') as file:
			file.write('''
cmake_minimum_required(VERSION 3.1)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/")

project(test)
enable_language(C CXX)

add_library(my_test SHARED test_module.cpp)
set_target_properties(my_test PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELWITHDEBINFO "%s" RUNTIME_OUTPUT_DIRECTORY_RELEASE "%s" SUFFIX .pyd)
target_include_directories(my_test PRIVATE "%s")
target_link_libraries(my_test "%s")
''' % (python_site_package, python_site_package, python_include_dir, python_library))

		build_path = os.path.join(work_path, 'build')

		os.mkdir(build_path)
		os.chdir(build_path)

		print("Generating build system...")
		try:
			subprocess.check_output('cmake .. -G "Visual Studio 15 2017')
		except subprocess.CalledProcessError as e:
			print(e.output.decode('utf-8'))
			return False

		if args.debug_test:
			with open(os.path.join(build_path, 'my_test.vcxproj.user'), 'w') as file:
				file.write('''\
<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="12.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='RelWithDebInfo|Win32'">
    <LocalDebuggerCommand>%s</LocalDebuggerCommand>
    <DebuggerFlavor>WindowsLocalDebugger</DebuggerFlavor>
    <LocalDebuggerCommandArguments>test.py</LocalDebuggerCommandArguments>
    <LocalDebuggerWorkingDirectory>%s</LocalDebuggerWorkingDirectory>
  </PropertyGroup>
</Project>''' % (python_interpreter, work_path))

		print("Building extension...")
		try:
			subprocess.check_output('cmake --build . --config Release')
		except subprocess.CalledProcessError as e:
			print(e.output.decode('utf-8'))
			return False

		# assert extension correctness
		test_path = os.path.join(work_path, 'test.py')
		with open(test_path, 'w') as file:
			file.write(module.test_python)
		shutil.copy(os.path.join(start_path, 'tests_api.py'), os.path.join(work_path, 'tests_api.py'))

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


# --
sys.path.append(os.path.join(start_path, 'tests'))

if args.debug_test:
	test_names = [args.debug_test]
else:
	test_names = [file[:-3] for file in os.listdir('./tests') if file.endswith('.py')]

run_tests(python.PythonGenerator(), test_names, PythonTestBed())
