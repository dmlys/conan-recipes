import os

from conan import ConanFile
from conan.tools.files import copy, download, get
from conan.errors import ConanInvalidConfiguration

class JomRecipe(ConanFile):
	name = "jom"
	
	description = "jom is a clone of nmake to support the execution of multiple independent commands in parallel"
	homepage = "http://wiki.qt.io/Jom"
	
	license = "GPL-3.0-only"
	
	package_type = "application"
	settings = "os", "arch"
	
	def set_version(self):
		self.version = self.version or "1.1.4"
	
	def validate(self):
		if self.settings.os != "Windows":
			raise ConanInvalidConfiguration("jom is windows only")
			
	def build(self):
		get(self, f"http://download.qt.io/official_releases/jom/jom_{self.version.replace('.', '_')}.zip")
	
	def layout(self):
		self.folders.source = "src"
		self.folders.build = "build"
		self.folders.generators  = self.folders.build
		
	def package(self):
		copy(self, "*.exe", src=self.build_folder, dst=self.package_folder)
		
	def package_info(self):
		pass