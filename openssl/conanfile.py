from __future__ import annotations

import os, platform

from enum import Enum
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

from conan.tools.files import get, copy
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs, can_run
from conan.tools.scm import Git
from conan.tools.microsoft import VCVars


class OpenSSLRecipe(ConanFile):
	name = "openssl"
	
	description = "OpenSSL libraries"
	license = "Apache 2.0 license"
	homepage = "https://www.openssl.org"
	
	languages = "C"
	settings = "os", "compiler", "arch", "build_type"

	options = {"shared": [True, False], "fPIC": [True, False]}
	default_options = {"shared": False, "fPIC": False}
	
	no_copy_source = True
	
	def set_version(self):
		self.version = self.version or "3.6.5"
	
	def validate(self):
		if self.settings.os == "Windows" and self.settings.compiler != "msvc":
			raise ConanInvalidConfiguration("On Windows currently only msvc supported")
	
	def config_options(self):
		if self.settings.compiler == "msvc":
			del self.options.fPIC

	def configure(self):
		if self.options.shared:
			self.options.rm_safe("fPIC")
	
	def requirements(self):
		if self.settings.os == "Windows":
			self.tool_requires("jom/[>=1]")
			self.tool_requires("strawberry-perl/[>=5]")
		else:
			self.tool_requires("system-perl/[>=5]")
			
		self.tool_requires("perl-text-template/[>=1]")

	def source(self):
		git = Git(self)
		git.fetch_commit("https://github.com/openssl/openssl.git", f"openssl-{self.version}")

	def layout(self):
		self.folders.source = "src"
		self.folders.build = "build"
		self.folders.generators = self.folders.build

	def generate(self):
		if self.settings.compiler == "msvc":
			msvc_env = VCVars(self)
			msvc_env.generate()

	def build(self):
	
		target = ""
		
		if self.settings.os == "Windows":
			if str(self.settings.build_type).find("Rel") < 0:
				target += "debug-"
		
			if self.settings.compiler == "msvc":
				target += "VC-"
			else:
				target += "mingw-"
		
			match self.settings.get_safe('arch'):
				case "x86_64":  target += "WIN64A"
				case "x86":     target += "WIN32"
		
		opts = "no-asm no-zlib no-module"
		if self.options.shared:
			opts += " shared"
		else:
			opts += " no-shared"
		
		if self.options.get_safe('fPIC') == False and not self.options.shared:
			opts += " no-pic"
		
		cmd = f"perl {self.source_folder}/Configure {target} {opts}"
		self.run(cmd, env=["conanbuild"])
	
		# fix some flags in generated makefile
		if self.settings.compiler == "msvc":
			perl_fix_cmd = ""
			# replace /MT ->  /MD and vice versa for runtime: dynamic, static
			match self.settings.compiler.get_safe('runtime'):
				case 'dynamic': perl_fix_cmd += "s/([\/-])MT(d?)/$1MD$2/g; "
				case 'static':  perl_fix_cmd += "s/([\/-])MD(d?)/$1MT$2/g; "
			
			if not self.options.shared:
				# change /Zi -> /Z7, remove /Fd<pdb>, remove ossl_static.pdb mentions
				perl_fix_cmd += r's/([\/-])\bZi\b/$1Z7/g; '
				perl_fix_cmd += r's/([\/-])\bFd\w*\.pdb\b//g; '
				perl_fix_cmd += r's/ossl_static\.pdb//g; '
				
			# rename libs: libsll.* -> openssl-ssl.* libcrypto.* -> openssl-crypto.*
			perl_fix_cmd += r's/\blibssl(?:-\d+.*?)?\.(lib|pdb|dll)\b/openssl-ssl.$1/g; '
			perl_fix_cmd += r's/\blibcrypto(?:-\d+.*?)?\.(lib|pdb|dll)\b/openssl-crypto.$1/g; '
		
			self.run(f'perl -i.bak -pe "{perl_fix_cmd}" makefile', env="conanbuild")
		
		if self.settings.compiler == "msvc":
			# jom able to build static lib, but fails with dll builds :(
			if self.options.shared:
				# generate def and rc files and correct library names there too
				self.run("nmake libcrypto.def libssl.def libcrypto.rc libssl.rc", env="conanbuild")
				self.run(r'perl -i.bak -pe "s/\blib(ssl|crypto)(-\d+.*)?\b/openssl-$1/" libcrypto.def libssl.def libcrypto.rc libssl.rc', env="conanbuild")
				
				#self.run("nmake build_generated", env="conanbuild")
				self.run("nmake", env="conanbuild")
			else:
				jobs = build_jobs(self)
				self.run(f"jom -j{jobs}", env="conanbuild")
		else:
			jobs = build_jobs(self)
			self.run(f"make -j{jobs}", env="conanbuild")
	
		#if can_run(self):
		#	self.settings.compiler == "msvc":
		#		self.run(f"nmake test", env=["conanbuild"])
		#	else:
		#		self.run(f"make test", env=["conanbuild"])
		
	def package(self):
		copy(self, "applink.c", src=f"{self.source_folder}/ms", dst=f"{self.package_folder}/include/openssl")
		copy(self, "*.h", src=f"{self.source_folder}/include/openssl", dst=f"{self.package_folder}/include/openssl")
		copy(self, "*.h", src=f"{self.build_folder}/include/openssl", dst=f"{self.package_folder}/include/openssl")
		
		if self.settings.compiler == "msvc": 
			copy(self, "openssl-*.lib", src=f"{self.build_folder}", dst=f"{self.package_folder}/lib")
			copy(self, "openssl-*.dll", src=f"{self.build_folder}", dst=f"{self.package_folder}/bin")
			copy(self, "openssl-*.pdb", src=f"{self.build_folder}", dst=f"{self.package_folder}/bin")
		else:
			copy(self, "lib*.a", src=f"{self.build_folder}", dst=f"{self.package_folder}/lib")
			copy(self, "lib*.so", src=f"{self.build_folder}", dst=f"{self.package_folder}/lib")
		
		if self.settings.os == "Windows":
			copy(self, "openssl.exe", src=f"{self.build_folder}/apps", dst=f"{self.package_folder}/bin")
			copy(self, "openssl.pdb", src=f"{self.build_folder}/apps", dst=f"{self.package_folder}/bin")
			copy(self, "openssl.cnf", src=f"{self.build_folder}/apps", dst=f"{self.package_folder}/bin")
		else:
			copy(self, "openssl",     src=f"{self.build_folder}/apps", dst=f"{self.package_folder}/bin")
			copy(self, "openssl.cnf", src=f"{self.build_folder}/apps", dst=f"{self.package_folder}/bin")
			

	def package_info(self):
		#self.cpp_info.bindirs = ["bin"]
		#self.cpp_info.libdirs = ["lib"]
		#self.cpp_info.includedirs = ["include"]
		pass
	