from __future__ import annotations

import os

from enum import Enum
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

from conan.tools.files import get, copy, patch
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs, can_run
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, AutotoolsDeps
from conan.tools.microsoft import VCVars


class XmlSecurityCRecipe(ConanFile):
	name = "xml-security-c"
	
	description = "Apache Santuario xml-security-c library"
	license = "Apache 2.0 license"
	homepage = "https://santuario.apache.org/"
	
	languages = "C++"
	settings = "os", "compiler", "arch", "build_type"

	options = {"shared": [True, False], "fPIC": [True, False]}
	default_options = {"shared": False, "fPIC": False}

	exports_sources = "patches/*"
	
	no_copy_source = True
	
	def set_version(self):
		self.version = self.version or "2.0.4"
	
	def validate(self):
		pass
	
	def config_options(self):
		# shared and fPIC are not supported on windows/msvc
		if self.settings.compiler == "msvc":
			del self.options.fPIC
			del self.options.shared

	def configure(self):
		if self.options.get_safe("shared"):
			self.options.rm_safe("fPIC")
	
	def requirements(self):			
		self.requires("openssl/[>=1]")
		self.requires("xerces-c/[>=3]")

	def source(self):
		get(self, f"https://archive.apache.org/dist/santuario/c-library/xml-security-c-{self.version}.tar.bz2", strip_root=True)
		patch(self, patch_file="patches/xml-security-c.sha256.patch")

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
			cxxflags = "/EHsc /Z7 /Gm-"
			cxxflags += " /D WIN32 /D _WIN32_WINNT=0x0A00 /D _SCL_SECURE_NO_WARNINGS /D _CRT_SECURE_NO_DEPRECATE /D XSEC_BUILDING_LIBRARY /D XSEC_HAVE_OPENSSL /D XSEC_HAVE_WINCAPI"
			
			if self.options.get_safe('shared'):
				cxxflags += " /D_USRDLL /D_WINDLL"
			
			sources  = r"xsec\canon\*.cpp xsec\dsig\*.cpp xsec\enc\*.cpp xsec\enc\OpenSSL\*.cpp xsec\enc\WinCAPI\*.cpp xsec\enc\XSCrypt\*.cpp".split(" ")
			sources += r"xsec\framework\*.cpp xsec\transformers\*.cpp xsec\utils\*.cpp xsec\xenc\impl\*.cpp".split(" ")
			fo = self.build_folder.replace("\\", "\\\\") + "\\\\"
			fo = f'/Fo"{fo}"'
			
			clcmd = f'call cl /c {cxxflags} %CXXFLAGS% %CPPFLAGS% /I . {fo} {" ".join(sources)}'
			if not self.options.get_safe('shared'):
				ldcmd = f'call lib *.obj -out:xml-security-c.lib'
			else:
				libs  = ["xerces-c_3.lib", "openssl-crypto.lib"]
				libs += ["ws2_32.lib", "crypt32.lib", "Advapi32.lib", "user32.lib"]
				ldcmd = f'call link /DLL /DEBUG %LDFLAGS% -out:xml-security-c.dll *.obj xerces-c_3.lib openssl-crypto.lib {" ".join(libs)}'				
	
			self.run(clcmd, cwd=self.source_folder, env="conanbuild")
			self.run(ldcmd, cwd=self.build_folder, env="conanbuild")
		
	def package(self):
		if self.settings.compiler != "msvc":
			autotools = Autotools(self)
			autotools.install()
		else:
			copy(self, "*.hpp", src=f"{self.source_folder}/xsec", dst=f"{self.package_folder}/include/xsec")
			copy(self, "*.lib", src=f"{self.build_folder}", dst=f"{self.package_folder}/lib")
	
	def package_info(self):
		self.cpp_info.defines = ["XSEC_HAVE_OPENSSL", "XSEC_HAVE_WINCAPI"]
		