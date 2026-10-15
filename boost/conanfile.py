from __future__ import annotations

import os, platform

from enum import Enum
from conan import ConanFile
from conan.errors import ConanException, ConanInvalidConfiguration

from conan.tools.files import get, copy
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs
from conan.tools.microsoft import VCVars


class BoostRecipe(ConanFile):
	name = "boost"
	#version = "1.92.0"

	description = "Boost C++ Libraries"
	license = "boost software license"
	homepage = "https://www.boost.org/"
	
	languages = "C++"
	settings = "os", "compiler", "arch", "build_type"

	options = {"shared": [True, False], "fPIC": [True, False]}
	default_options = {"shared": False, "fPIC": False}
	
	no_copy_source = True
	
	def set_version(self):
		self.version = self.version or "1.92.0"
	
	@property
	def _boost_vername(self):
		return "boost_" + self.version.replace('.', '_')
	
	def config_options(self):
		if self.settings.compiler == "msvc":
			del self.options.fPIC

	def configure(self):
		if self.options.shared:
			# If compiler=msvc, fPIC will have been removed in config_options()
			# use rm_safe to avoid double delete errors
			self.options.rm_safe("fPIC")

	def source(self):
		# This is bad practice. source method should not depend on settings/options.
		if platform.system() == "Windows":
			get(self, f"https://archives.boost.io/release/1.92.0/source/{self._boost_vername}.zip")
		else:
			get(self, f"https://archives.boost.io/release/1.92.0/source/{self._boost_vername}.tar.bz2")

	def validate(self):
		check_min_cppstd(self, "11")

	def layout(self):
		self.folders.source = "src"
		self.folders.build = "build"
		self.folders.generators = self.folders.build
		
		# This is for editable package mode
		# TODO: test editable mode
		self.cpp.source.includedirs = self._boost_vername
		self.cpp.build.libdirs = "boost-stage/lib"


	def generate(self):
		if self.settings.compiler == "msvc":
			msvc_env = VCVars(self)
			msvc_env.generate()

	class B2Target(Enum):
		INSTALL = "install"
		STAGE = "stage"

	def _prepare_b2_command(self, target: BoostRecipe.B2Target):
	
		match target:
			case BoostRecipe.B2Target.INSTALL:
				target_cmd = f"install --prefix=\"{self.package_folder}\""
			case BoostRecipe.B2Target.STAGE:
				target_cmd = f"stage --stagedir=\"{os.path.join(self.build_folder, 'boost-stage')}\""
				
		cmd = "\"{}\" {} --build-dir=\"{}\" --abbreviate-paths --layout=system" \
			.format(os.path.join(self.build_folder, 'b2'),
					target_cmd,
					os.path.join(self.build_folder, 'boost-build'))

		match self.settings.build_type:
			case "Release":  cmd += " variant=release"
			case "Debug":	 cmd += " variant=debug"
			case _:
				if str(self.settings.build_type).find("Rel") >= 0:
					cmd += " variant=release"
				else:
					cmd += " variant=debug"
		
		cmd += f" link={'shared' if self.options.shared == True else 'static'}"
		if runtime := self.settings.compiler.get_safe('runtime'):
			cmd += f" runtime-link={'static' if runtime == 'static' else 'shared'}"
				
		# add explicit address-model for x86 architectures, for others, let boost decide itself for now
		match self.settings.get_safe('arch'):
			case "x86_64":  cmd += f" address-model=64"
			case "x86":     cmd += f" address-model=32"
		
		cxxflags = ""
		if self.options.get_safe('fPIC') and not self.options.shared:
			# if shared b2 will add fPIC implicitly, but if fPIC with static lib - we must add fPIC ourselves,
			# it is also probably good idea to add visibility=hidden
			#cxxflags += '-fPIC -fvisibility=hidden -fvisibility-inlines-hidden';
			cxxflags += '-fPIC visibility=hidden'
		
		if cxxflags: cmd += f' cxxflags="{cxxflags}"'
		
		jobs = build_jobs(self)
		cmd += f" -j {jobs}"

		return cmd
		

	def build(self):		
		
		boost_dir = f"{self.source_folder}/{self._boost_vername}"
		b2_file = "b2.exe" if self.settings.os == "Windows" else "b2"
		
		if not os.path.isfile(b2_file):
			bootstrap_file = "bootstrap.bat" if self.settings.os == "Windows" else "bootstrap.sh"
			
			copy(self, "*", src=f"{boost_dir}/tools/build/src", dst=f"{self.build_folder}/tools/build/src")
			copy(self, bootstrap_file, src=boost_dir, dst=self.build_folder)
			
			bootstrap_cmd = os.path.join(".", bootstrap_file)
			self.run(bootstrap_cmd, env="conanbuild")
		
		# Note, b2 must be ran from source_folder because it contains project bjam config file and it is looked from cwd.
		self.run(self._prepare_b2_command(BoostRecipe.B2Target.STAGE), cwd=boost_dir, env=["conanbuild", "conanrun"])
		
	def package(self):
		self.run(self._prepare_b2_command(BoostRecipe.B2Target.INSTALL), cwd=f"{self.source_folder}/{self._boost_vername}", env=["conanbuild", "conanrun"])

	def package_info(self):
		# linking will be done by consumer explicitly
		self.cpp_info.libs = []
		self.cpp_info.defines = ["BOOST_ALL_NO_LIB", "BOOST_AUTO_LINK_NOMANGLE"]
		if self.options.shared:
			self.cpp_info.defines += ["BOOST_ALL_DYN_LINK"]
	