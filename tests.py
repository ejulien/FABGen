import importlib
import tempfile
import subprocess
import shutil
import time
import sys
import os

import python


start_path = os.path.dirname(__file__)


# -- interpreter settings
python_include_dir = 'c:/Python35-32/include'
python_library = 'c:/Python35-32/libs/python3.lib'
python_site_package = 'c:/Python35-32/Lib/site-packages'
python_interpreter = 'c:/Python35-32/python.exe'


# --
run_test_list = []
failed_test_list = []


def run_test(gen, name, testbed):
	try:
		with tempfile.TemporaryDirectory() as work_path:
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

	except PermissionError as e:
		print('\nWARNING: Failed to cleanup temporary directory ("%s").' % e.filename)


def run_tests(gen, names, testbed):
	test_count = len(names)
	print("Running %d tests\n" % test_count)

	for i, name in enumerate(names):
		print('[%d/%d] Running test "%s"' % (i+1, test_count, name))
		run_test(gen, name, testbed)
		print('')

	run_test_count = len(run_test_list)
	failed_test_count = len(failed_test_list)

	print("[Test summary: %d run, %d failed]" % (run_test_count, failed_test_count))


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
target_include_directories(my_test PRIVATE "%s")
target_link_libraries(my_test "%s")
''' % (python_include_dir, python_library))

		build_path = os.path.join(work_path, 'build')

		os.mkdir(build_path)
		os.chdir(build_path)

		print("Generating build system...")
		subprocess.check_output('cmake .. -G "Visual Studio 12 2013')
		print("Building extension...")
		subprocess.check_output('cmake --build . --config Release')

		# deploy extension to target interpreter
		ext_path = os.path.join(python_site_package, 'my_test.pyd')
		shutil.copy(os.path.join(build_path, 'Release', 'my_test.dll'), ext_path)

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
		except subprocess.CalledProcessError:
			success = False

		print("Cleanup...")
		os.unlink(ext_path)

		return success


# --
sys.path.append(os.path.join(start_path, 'tests'))

test_names = [
	'test_basic_type_exchange',
]

run_tests(python.PythonGenerator(), test_names, PythonTestBed())
