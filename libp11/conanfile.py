from __future__ import annotations

import os, shutil

from enum import Enum
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

from conan.tools.files import get, copy, patch
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs, can_run
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, AutotoolsDeps
from conan.tools.microsoft import VCVars


class Libp11Recipe(ConanFile):
	name = "libp11"
	
	description = "OpenSC libp11 library"
	license = "LGPL-2.1 license"
	homepage = "https://github.com/OpenSC/libp11"
	
	languages = "C"
	settings = "os", "compiler", "arch", "build_type"

	options = {"shared": [True, False], "fPIC": [True, False]}
	default_options = {"shared": False, "fPIC": False}
	
	no_copy_source = True
	
	def set_version(self):
		self.version = self.version or "0.4.21"
	
	def validate(self):
		pass
	
	def config_options(self):
		# shared and fPIC are not supported on windows/msvc
		if self.settings.compiler == "msvc":
			del self.options.fPIC
			#del self.options.shared

	def configure(self):
		if self.options.get_safe("shared"):
			self.options.rm_safe("fPIC")
	
	def requirements(self):			
		self.requires("openssl/[>=1]")

	def source(self):	
		get(self, f"https://github.com/OpenSC/libp11/releases/download/libp11-{self.version}/libp11-{self.version}.tar.gz", strip_root=True)

	def layout(self):
		basic_layout(self, src_folder="src")

	def generate(self):
		if self.settings.compiler == "msvc":
			msvc_env = VCVars(self)
			msvc_env.generate()
		
		atc = AutotoolsToolchain(self)
		atc.generate()
		ad  = AutotoolsDeps(self)
		ad.generate()
			

	def build(self):
		if self.settings.compiler != "msvc":
			autotools = Autotools(self)
			autotools.configure()
			autotools.make()
		else:
			cxxflags = "/Z7 /Gm-"
			cxxflags += " /D WIN32 /D_WIN32_WINNT=0x0600 /DWIN32_LEAN_AND_MEAN /D _WIN32_WINNT=0x0A00 /D _CRT_SECURE_NO_DEPRECATE"
			
			if self.options.get_safe('shared'):
				cxxflags += " /D_USRDLL /D_WINDLL"
			
			sources = [r"src\libpkcs11.c", r"src\p11_*.c"]
			
			fo = self.build_folder.replace("\\", "\\\\") + "\\\\"
			fo = f'/Fo"{fo}"'
			
			clcmd = f'call cl /c {cxxflags} %CXXFLAGS% %CPPFLAGS% /I . {fo} {" ".join(sources)}'
			if not self.options.get_safe('shared'):
				ldcmd = f'call lib *.obj -out:libp11.lib'
			else:				
				self.run(f'call rc /fo libp11.res "{self.source_folder}\\src\\libp11.rc"', env='conanbuild')
				self.run(f'echo LIBRARY libp11 > libp11.def && echo EXPORTS >> libp11.def && type "{self.source_folder}\\src\\libp11.exports" >> libp11.def', env='conanbuild')
				
				libs  = ["openssl-crypto.lib"]
				libs += ["ws2_32.lib", "crypt32.lib", "Advapi32.lib", "user32.lib"]
				ldcmd = f'call link /DLL /DEBUG %LDFLAGS% -out:libp11.dll /DEF:libp11.def *.obj libp11.res openssl-crypto.lib {" ".join(libs)}'
	
			self.run(clcmd, cwd=self.source_folder, env="conanbuild")
			self.run(ldcmd, cwd=self.build_folder, env="conanbuild")
		
	def package(self):
		if self.settings.compiler != "msvc":
			autotools = Autotools(self)
			autotools.install()
		else:
			os.makedirs(f"{self.package_folder}/include", exist_ok=True)
			os.makedirs(f"{self.package_folder}/lib", exist_ok=True)
			
			shutil.copyfile(src=f"{self.source_folder}/src/libp11.h", dst=f"{self.package_folder}/include/libp11.h")
			shutil.copyfile(src=f"{self.source_folder}/src/p11_ver.h", dst=f"{self.package_folder}/include/p11_ver.h")
			shutil.copyfile(src=f"{self.source_folder}/src/p11_err.h", dst=f"{self.package_folder}/include/p11_err.h")
			
			shutil.copyfile(src=f"{self.build_folder}/libp11.lib", dst=f"{self.package_folder}/lib/libp11.lib")
			if self.options.get_safe('shared'):
				os.makedirs(f"{self.package_folder}/bin", exist_ok=True)
				shutil.copyfile(src=f"{self.build_folder}/libp11.dll", dst=f"{self.package_folder}/bin/libp11.dll")
				shutil.copyfile(src=f"{self.build_folder}/libp11.pdb", dst=f"{self.package_folder}/bin/libp11.pdb")
	
	def package_info(self):
		self.cpp_info.defines = []
		