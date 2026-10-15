import os

from conan import ConanFile
from conan.tools.build import can_run

from conan.tools.build import build_jobs
from conan.tools.gnu import AutotoolsToolchain, AutotoolsDeps
from conan.tools.microsoft import VCVars, NMakeDeps


class BoostRecipeTest(ConanFile):
	
	settings = "os", "compiler", "build_type", "arch"
	generators = "AutotoolsToolchain", "AutotoolsDeps"
	
	def requirements(self):
		self.requires(self.tested_reference_str)
	
	def layout(self):
		self.folders.source = ""
		self.folders.build = "build"
		self.folders.generators  = self.folders.build
		
	def generate(self):
		if self.settings.compiler == "msvc":
			msvc_env = VCVars(self)
			msvc_env.generate()
	
	def _msvc_flags(self):
		flags = "/EHsc "
		flags += "/MT" if self.settings.compiler.runtime == "static" else "/MD"
		if self.settings.compiler.runtime_type == "Debug":
			flags += "d"
		
		return flags
	
	def build(self):
		if self.settings.compiler == "msvc":
			libs = ["boost_chrono.lib"]
			if not self.dependencies[self.tested_reference_str].options.shared:
				libs = ["lib" + l for l in libs]
				
			cmd = f"call cl %CXXFLAGS% %CPPFLAGS% {self._msvc_flags()} {os.path.join(self.source_folder, 'main.cpp')} /Fe:test.exe /link %LDFLAGS% {' '.join(libs)}"
		else:
			cmd = f"$CXX $CXXFLAGS $CPPFLAGS $LDFLAGS {os.path.join(self.source_folder, 'main.cpp')} -lboost_chrono -o test"
		
		self.run(cmd, env=["conanbuild", "conanrun"])
	
	def test(self):
		if can_run(self):
			cmd = os.path.join(".", "test")
			self.run(cmd, env="conanrun")
