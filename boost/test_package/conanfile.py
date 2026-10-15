import os

from conan import ConanFile
from conan.tools.build import can_run

from conan.tools.build import build_jobs
from conan.tools.microsoft import VCVars

class BoostRecipeTest(ConanFile):
	
	settings = "os", "compiler", "build_type", "arch"
	
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
		deps_cpp = self.dependencies[self.tested_reference_str].cpp_info.aggregated_components()
		if self.settings.compiler == "msvc":
			includes = [f"/I \"{i}\"" for i in deps_cpp.includedirs]
			libdirs  = [f"/link /LIBPATH:\"{l}\"" for l in deps_cpp.libdirs]
			depstr = " ".join(includes + libdirs)
		else:
			includes = [f"-isystem \"{i}\"" for i in deps_cpp.includedirs]
			libdirs  = [f"-L\"{l}\"" for l in deps_cpp.libdirs]
			depstr = " ".join(includes + libdirs)
		
		defines  = " ".join([f"-D{d}" for d in deps_cpp.defines])
		includes = " ".join(includes)
		libdirs  = " ".join(libdirs)
		
		if self.settings.compiler == "msvc":
			libname = "boost_chrono.lib"
			if not self.dependencies[self.tested_reference_str].options.shared:
				libname = "lib" + libname
				
			self.run(f"cl {self._msvc_flags()} {includes} {defines} {os.path.join(self.source_folder, 'main.cpp')} /Fe:test.exe {libdirs} {libname}", env=["conanbuild"])
		else:
			self.run(f"$CXX $CXXFLAGS {includes} {defines} {libdirs} -lboost_chrono main.cpp -o test", env=["conanbuild"])
	
	def test(self):
		if can_run(self):
			cmd = os.path.join(".", "test")
			self.run(cmd, env="conanrun")
