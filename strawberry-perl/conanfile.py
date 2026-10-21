import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

from conan.tools.files import get, copy
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs

class StrawberryPerlRecipe(ConanFile):
	name = "strawberry-perl"
	
	description = "Strawberry Perl is a perl environment for MS Windows containing all you need to run and develop perl applications"
	license = "OSI-approved BSD 3-clause License"
	homepath = "https://strawberryperl.com/"
	
	package_type = "application"
	settings = "os", "arch"

	no_copy_source = True
	
	def set_version(self):
		self.version = self.version or "5.42.3.1"

	def validate(self):
		if self.settings.os != "Windows":
			raise ConanInvalidConfiguration("strawberry-perl is windows only")

	def build(self):
		get(self, f"https://github.com/StrawberryPerl/Perl-Dist-Strawberry/releases/download/SP_{self.version.replace('.', '')}_64bit/strawberry-perl-{self.version}-64bit-portable.zip")

	def layout(self):
		self.folders.source = "src"
		self.folders.build = "build"
		self.folders.generators  = self.folders.build
	
	def package(self):
		copy(self, "*", src=self.build_folder, dst=self.package_folder, excludes = "strawberry-perl-*.zip")
		
	def package_info(self):
		pathdirs = ["perl/bin", "perl/site/bin", "c/bin"]
		self.cpp_info.bindirs = [ os.path.normpath(p) for p in pathdirs ]