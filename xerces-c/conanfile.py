from __future__ import annotations

import os, platform

from enum import Enum
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

from conan.tools.files import get, copy, patch
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs, can_run
from conan.tools.cmake import cmake_layout, CMakeConfigDeps, CMakeToolchain, CMake


class XercesCRecipe(ConanFile):
	name = "xerces-c"

	description = "Xerces-C++ XML Parser"
	license = " Apache Software License, Version 2.0"
	homepage = "https://xerces.apache.org/xerces-c"
	
	languages = "C++"
	settings = "os", "compiler", "arch", "build_type"

	options = {"shared": [True, False], "fPIC": [True, False]}
	default_options = {"shared": False, "fPIC": False}
	
	exports_sources = "patches/*"
	
	no_copy_source = True
	
	def requirements(self):
		self.tool_requires("cmake/[>=3]")
	
	def set_version(self):
		self.version = self.version or "3.3.0"
	
	def config_options(self):
		if self.settings.compiler == "msvc":
			del self.options.fPIC

	def configure(self):
		if self.options.shared:
			self.options.rm_safe("fPIC")

	def source(self):
		get(self, f"https://dlcdn.apache.org//xerces/c/3/sources/xerces-c-{self.version}.tar.xz", strip_root=True)
		patch(self, patch_file="patches/libname.patch")

	def validate(self):
		check_min_cppstd(self, "11")

	def layout(self):
		cmake_layout(self, src_folder="src")

	def generate(self):
		cd = CMakeConfigDeps(self)
		cd.generate()
		
		ct = CMakeToolchain(self)
		ct.cache_variables["network"] = False
		if self.settings.compiler == "msvc":
			ct.cache_variables["transcoder"] = "windows"
		else:
			ct.cache_variables["transcoder"] = "iconv"
		ct.cache_variables["message-loader"] = "inmemory"
		ct.cache_variables["xmlch-type"] = "char16_t"
		ct.cache_variables["mutex-manager"] = "standard"
		
		ct.generate()

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
	