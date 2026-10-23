from __future__ import annotations

import os, platform

from enum import Enum
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

from conan.tools.files import get, copy
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs, can_run
from conan.tools.cmake import cmake_layout, CMakeConfigDeps, CMakeToolchain, CMake


class Log4cplusRecipe(ConanFile):
	name = "log4cplus"

	description = "log4cplus is a simple to use C++23 logging API providing thread-safe, flexible, and arbitrarily granular control over log management and configuration. It is modeled after the Java log4j API."
	license = "Apache license 2.0"
	homepage = "https://github.com/log4cplus/log4cplus"
	
	languages = "C++"
	settings = "os", "compiler", "arch", "build_type"

	options = {"shared": [True, False], "fPIC": [True, False], "unicode": [True, False]}
	default_options = {"shared": False, "fPIC": False, "unicode": False}
	
	no_copy_source = True
	
	def requirements(self):
		self.tool_requires("cmake/[>=3]")
	
	def set_version(self):
		self.version = self.version or "2.2.1"
	
	def config_options(self):
		if self.settings.compiler == "msvc":
			del self.options.fPIC
		
		if self.settings.os == "Windows":
			self.options.unicode = True

	def configure(self):
		if self.options.shared:
			self.options.rm_safe("fPIC")

	def source(self):
		get(self, f"https://github.com/log4cplus/log4cplus/releases/download/REL_{self.version.replace('.', '_')}/log4cplus-{self.version}.tar.xz", strip_root=True)

	def validate(self):
		check_min_cppstd(self, "11")

	def layout(self):
		cmake_layout(self, src_folder="src")

	def generate(self):
		ct = CMakeToolchain(self)
		ct.cache_variables["LOG4CPLUS_ENABLE_DECORATED_LIBRARY_NAME"] = False
		ct.cache_variables["LOG4CPLUS_BUILD_LOGGINGSERVER"] = False
		ct.cache_variables["UNICODE"] = self.options.unicode
		ct.generate()
		cd = CMakeConfigDeps(self)
		cd.generate()

	def build(self):
		cmake = CMake(self)
		cmake.configure()
		cmake.build()
		
		if can_run(self):
			cmake.ctest(cli_args=["--output-on-failure"])
		
	def package(self):
		cmake = CMake(self)
		cmake.install()

	def package_info(self):
		pass
	