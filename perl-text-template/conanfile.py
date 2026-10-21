import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

from conan.tools.files import get, copy
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs

class PerlTextTemplateRecipe(ConanFile):

	name = "perl-text-template"
	#version = "1.61"

	description = "Text::Template - Expand template text with embedded Perl"
	license = "perl license"
	homepath = "https://metacpan.org/pod/Text::Template"
	
	languages = "C++"
	settings = "os"

	no_copy_source = True
	
	def set_version(self):
		self.version = self.version or "1.61"

	def requirements(self):
		if self.settings.os == "Windows":
			self.tool_requires("strawberry-perl/[~5]")
		else:
			self.tool_requires("system-perl/[~5]")

	def validate(self):
		pass

	def source(self):
		get(self, f"https://cpan.metacpan.org/authors/id/M/MS/MSCHOUT/Text-Template-{self.version}.tar.gz", strip_root=True)

	def layout(self):
		self.folders.source = "src"
		self.folders.build = "build"
		self.folders.generators  = self.folders.build
	
	# NOTE: perl пакеты обычно не поддерживают out of tree сборку, 
	# поэтому perl Makefile.PL нужно делать внутри папки с исходниками. Копируем исходники в build-folder
	def build(self):
		copy(self, "*", src=self.source_folder, dst=self.build_folder)
		self.run(f"perl Makefile.PL INSTALL_BASE=install-dir", env=["conanbuild"])
		self.run("gmake && gmake install", env=["conanbuild"])
	
	def package(self):
		copy(self, "*", src=os.path.join(self.build_folder, 'install-dir'), dst=self.package_folder)
		
	def package_info(self):
		self.buildenv_info.prepend_path("PERL5LIB", os.path.join(self.package_folder, "lib", "perl5"))