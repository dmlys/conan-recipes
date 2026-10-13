import os

from conan import ConanFile
from conan.errors import ConanException, ConanInvalidConfiguration

from conan.tools.files import get, copy
from conan.tools.build import check_max_cppstd, check_min_cppstd
from conan.tools.build import build_jobs

class CMakeRecipe(ConanFile):

	name = "cmake"
	#version = "4.4.4"

	description = "CMake is a cross-platform, open-source build system generator"
	license = "OSI-approved BSD 3-clause License"
	homepath = "https://github.com/Kitware/CMake"
	
	package_type = "application"
	languages = "C++"
	settings = "os", "compiler", "arch", "build_type"

	no_copy_source = True
	
	def set_version(self):
		self.version = self.version or "4.4.4"

	def validate(self):
		if self.settings.os != "Windows":
			check_min_cppstd(self, "11")

	def source(self):
		pass

	def layout(self):
		self.folders.source = "src"
		self.folders.build = "build"
		self.folders.generators  = self.folders.build

		# This is for editable package mode
		# TODO: test editable mode
		#self.cpp.source.includedirs =
		#self.cpp.build.libdirs = 


	# Самым правильным путем является сборка cmake из исходников, особенно на POSIX/Linux системах с их зоопарком дистрибутивов/окружений.
	# Но на Windows что бы собрать cmake нужно POSIX окружение - MinGW. Не очень хочется делать зависимость от MinGW. 
	# К тому же для windows cmake поставляет precompiled binaries.
	# Поэтому для windows качаем уже собранные исходники, а для остальных случаев собираем(POSIX environment assumed)
	#
	# В conan сборка и install разделены на 2 разных шага и определенны папка build_folder и package_folder.
	# В обычном flow они обе заданны для все шагов, поэтому --prefix можно указать в build шаге с помощью package_folder и он будет корректным.
	# Но в случае с local flow(conan build), а также editable packages package_folder на этапе build будет равен build_folder - 
	# из-за чего conan export-pkg по факту сделает make install в build_folder и создаться пустой пакет.
	#
	# cmake bootstrap сначала собирает минимальную сборку, после чего сам себя собирает cmake'ом. 
	# make install же по факту вызывает bin/cmake -P cmake_install.cmake. 
	# Мы может явно дернуть bin/cmake -DCMAKE_INSTALL_PREFIX=$package_folder -P cmake_install.cmake 
	# Тем самым указать актуальный package_folder. cmake это позволяет и нормально обрабатывает.
	def build(self):
		if self.settings.os == "Windows":
			arname = f"cmake-{self.version}-windows-{self.settings.arch}"
			get(self, f"https://github.com/Kitware/CMake/releases/download/v{self.version}/{arname}.zip")
		else:
			arname = f"cmake-{self.version}"
			get(self, f"https://github.com/Kitware/CMake/releases/download/v{self.version}/{arname}.tar.gz")

		if self.settings.os != "Windows":
			srcdir = f"{self.build_folder}/{arname}"
			jobs = build_jobs(self)

			cmd = "{} --prefix=\"{}\" --parallel={}".format(os.path.join(srcdir, "bootstrap"), self.package_folder, jobs)
			self.run(cmd, env="conanbuild")
			self.run(f"make -j{jobs}", env="conanbuild")

	def package(self):
		if self.settings.os != "Windows":
			#self.run("make install", env="conanbuild")
			self.run(f"bin/cmake -DCMAKE_INSTALL_PREFIX=\"{self.package_folder}\" -P cmake_install.cmake", env="conanbuild")
		else:
			arname = f"cmake-{self.version}-windows-{self.settings.arch}"
			copy(self, "*", src=arname, dst=self.package_folder)

	def package_info(self):
		pass

	def package_id(self):
		del self.info.settings.compiler
		del self.info.settings.build_type
