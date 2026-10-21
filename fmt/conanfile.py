from __future__ import annotations

import os, platform

from enum import Enum
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

from conan.tools.files import get, copy
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs, can_run
from conan.tools.cmake import cmake_layout, CMakeConfigDeps, CMakeToolchain, CMake


class FmtRecipe(ConanFile):
	name = "fmt"

	description = "{fmt} is an open-source formatting library providing a fast and safe alternative to C stdio and C++ iostreams."
	license = "MIT license"
	homepage = "https://fmt.dev"
	
	languages = "C++"
	settings = "os", "compiler", "arch", "build_type"

	options = {"shared": [True, False], "fPIC": [True, False]}
	default_options = {"shared": False, "fPIC": False}
	
	no_copy_source = True
	
	def requirements(self):
		self.tool_requires("cmake/[>=3]")
	
	def set_version(self):
		self.version = self.version or "12.2.0"
	
	def config_options(self):
		if self.settings.compiler == "msvc":
			del self.options.fPIC

	def configure(self):
		if self.options.shared:
			self.options.rm_safe("fPIC")

	def source(self):
		get(self, f"https://github.com/fmtlib/fmt/archive/refs/tags/{self.version}.tar.gz", strip_root=True)

	def validate(self):
		check_min_cppstd(self, "11")

	def layout(self):
		cmake_layout(self, src_folder="src")

	def generate(self):
		ct = CMakeToolchain(self)
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
	