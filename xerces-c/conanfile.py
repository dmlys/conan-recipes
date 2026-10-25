from __future__ import annotations

import os, platform

from enum import Enum
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

from conan.tools.files import get, copy, patch
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs, can_run
from conan.tools.cmake import cmake_layout, CMakeConfigDeps, CMakeToolchain, CMake
from conan.tools.gnu   import AutotoolsToolchain, AutotoolsDeps, Autotools


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
		if self.settings.compiler == "msvc":
			basic_layout(self, "src_folder")
		else:
			cmake_layout(self, src_folder="src")

	def generate(self):
		if self.settings.compiler == "msvc":
			cd = CMakeConfigDeps(self)
			cd.generate()
			
			ct = CMakeToolchain(self)
			ct.cache_variables["network"] = False
			ct.cache_variables["transcoder"] = "windows"
			ct.cache_variables["message-loader"] = "inmemory"
			ct.cache_variables["xmlch-type"] = "char16_t"
			ct.cache_variables["mutex-manager"] = "standard"
		
			ct.generate()
		else:
			atc = AutotoolsToolchain(self)
			atc.configure_args.append("--disable-network")
			atc.configure_args.append("--enable-mutexmgr-standard")
			atc.configure_args.append("--enable-transcoder-iconv")
			atc.configure_args.append("--enable-msgloader-inmemory")
			atc.configure_args.append("--enable-xmlch-char16_t")
			atc.generate()

			ad  = AutotoolsDeps(self)
			ad.generate()

	def build(self):
		if self.settings.compiler == "msvc":
			cmake = CMake(self)
			cmake.configure()
			cmake.build()
			
			if can_run(self):
				cmake.ctest(cli_args=["--output-on-failure"])
		else:
			autotools = Autotools(self)
			autotools.configure()
			autotools.make()
		
	def package(self):
		if self.settings.compiler == "msvc":
			cmake = CMake(self)
			cmake.install()
		else:
			autotools = Autotools(self)
			autotools.install()

	def package_info(self):
		pass
	