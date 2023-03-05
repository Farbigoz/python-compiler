import os
import sys

from typing import Optional, List, Union

from distutils.ccompiler import new_compiler
from distutils.dist import Distribution
from distutils.command.build import build

from .resources import PythonFile, CythonFile, CFile, ExecResourceFile, DataFile, ResourcesFromFileName
from .deps import MakeDeps


_TCompileRes = Union[PythonFile, CythonFile, CFile]
_TDataFiles = Union[DataFile, List['_TDataFiles']]


PYTHON_DIR = sys.base_prefix
PYTHON_INCLUDE_DIR = os.path.join(PYTHON_DIR, "include")
PYTHON_LIBS_DIR = os.path.join(PYTHON_DIR, "libs")


def _extFileName(extName: str):
    from distutils.sysconfig import get_config_var
    ext_path = extName.split('.')
    ext_suffix = get_config_var('EXT_SUFFIX')
    return os.path.join(*ext_path) + ext_suffix


def _getBuildCmd(buildDir: Optional[str] = None) -> build:
    buildCmd = build(Distribution())
    if buildDir is not None:
        buildCmd.build_base = buildDir

    buildCmd.finalize_options()

    buildCmd.build_temp = os.path.join(buildCmd.build_temp, "Release")

    return buildCmd


class BaseProcessor:
    def __init__(self, buildDir: Optional[str] = None):
        self.buildCmd = _getBuildCmd(buildDir)

    @property
    def buildDir(self) -> str:
        return self.buildCmd.build_base

    @buildDir.setter
    def buildDir(self, buildDir: str):
        self.buildCmd = _getBuildCmd(buildDir)

    def process(self):
        pass

    def clean(self):
        pass


class BaseCompiler(BaseProcessor):
    def __init__(self,
                 includeDirs: Optional[List[str]] = None,
                 libraryDirs: Optional[List[str]] = None,
                 buildDir: Optional[str] = None):
        super().__init__(buildDir=buildDir)

        if includeDirs is None:
            includeDirs = []

        if libraryDirs is None:
            libraryDirs = []

        self.compiler = new_compiler()

        self.incDirs = [PYTHON_INCLUDE_DIR]
        self.libDirs = [PYTHON_LIBS_DIR]

        self.incDirs.extend(includeDirs)
        self.libDirs.extend(libraryDirs)

        self._cache = []

    def addIncludeDir(self, includeDir: str):
        self.incDirs.append(includeDir)

    def addLibraryDir(self, libraryDir: str):
        self.libDirs.append(libraryDir)

    def _compileLib(self, sources: List[str], outputFile: str, exportSymbols: Optional[List[str]] = None):
        if exportSymbols is None:
            exportSymbols = []

        self.compiler.set_include_dirs(self.incDirs)
        self.compiler.set_library_dirs(self.libDirs)

        objects = self.compiler.compile(sources, output_dir=self.buildCmd.build_temp)

        self.compiler.link_shared_object(
            objects=objects,
            output_filename=os.path.join(self.buildCmd.build_platlib, outputFile),
            target_lang="c++",
            build_temp=self.buildCmd.build_base,
            export_symbols=exportSymbols
        )

        self._cache.extend(sources)
        self._cache.extend(objects)

    def _compileExec(self, sources: List[str], outputFileName: str):
        self.compiler.set_include_dirs(self.incDirs)
        self.compiler.set_library_dirs(self.libDirs)

        objects = self.compiler.compile(sources, output_dir=self.buildCmd.build_temp)

        self.compiler.link_executable(
            objects=objects,
            output_progname=os.path.join(self.buildCmd.build_platlib, outputFileName),
            target_lang="c++"
        )

        self._cache.extend(sources)
        self._cache.extend(objects)

    def clean(self):
        for file in self._cache:
            if os.path.exists(file):
                print(f"Remove {file}")
                os.remove(file)


class Data(BaseProcessor):
    data: List[DataFile]

    def __init__(self,
                 data: Union[str, List[str], DataFile, List[DataFile]],
                 homePath: Optional[str] = None,
                 buildDir: Optional[str] = None):

        super().__init__(buildDir=buildDir)

        if isinstance(data, str) or isinstance(data, DataFile):
            data = [data]

        self.data = []
        for _data in data:
            if isinstance(_data, DataFile):
                self.data.append(_data)
            elif isinstance(_data, str):
                self.data.extend(ResourcesFromFileName(_data, clone=True, homePath=homePath))

    def process(self):
        for data in self.data:
            data.clone(self.buildCmd.build_platlib)


class Module(BaseCompiler):
    resources: List[_TCompileRes]
    name: str

    def __init__(self,
                 resources: Union[str, List[str], _TCompileRes, List[_TCompileRes]],
                 package: Optional[bool] = False,
                 includeDirs: Optional[List[str]] = None,
                 libraryDirs: Optional[List[str]] = None,
                 buildDir: Optional[str] = None):

        super().__init__(includeDirs=includeDirs, libraryDirs=libraryDirs, buildDir=buildDir)

        if isinstance(resources, str):
            resources = [resources]
        elif isinstance(resources, (PythonFile, CythonFile, CFile)):
            resources = [resources]

        self.resources = []
        for resource in resources:
            if isinstance(resource, str):
                self.resources.extend(ResourcesFromFileName(resource))

            elif isinstance(resource, (PythonFile, CythonFile, CFile)):
                self.resources.append(resource)

        self.package = package

        if self.package:
            self.name = self.resources[0].name
        else:
            self.name = self.resources[0].fullName

        self.moduleFileName = _extFileName(self.name.split(".")[-1])
        self.moduleFilePath = os.path.join(*self.name.split(".")[:-1], self.moduleFileName)

    def process(self):
        sources: List[str] = []

        for resource in self.resources:
            if isinstance(resource, (PythonFile, CythonFile)):
                resource.cythonize(package=self.package)
                if self.package:
                    resource.freezePackage()
                sources.append(resource.outputFile)

            elif isinstance(resource, CFile):
                sources.append(resource.inputFile)

        exportSymbols = []
        if self.name.endswith("__init__"):
            exportSymbols.append("PyInit_" + self.name.split(".")[-2])
        else:
            exportSymbols.append("PyInit_" + self.name.split(".")[-1])

        self._compileLib(sources, self.moduleFilePath, exportSymbols)


class Package(Module):
    def __init__(self,
                 resources: List[Union[
                     str,
                     _TCompileRes
                 ]],
                 includeDirs: Optional[List[str]] = None,
                 libraryDirs: Optional[List[str]] = None,
                 buildDir: Optional[str] = None):

        tmpResources = []
        for resource in resources:
            if isinstance(resource, str):
                tmpResources.extend(ResourcesFromFileName(resource))

            elif isinstance(resource, (PythonFile, CythonFile, CFile)):
                tmpResources.append(resource)

        for resource in tmpResources:
            if resource.fullName.endswith("__init__"):
                initResource = resource
                break

        else:
            raise Exception(f"Not found '__init__' in package \"{'.'.join(tmpResources[0].name.split('.')[:-1])}\"")

        tmpResources.remove(initResource)
        tmpResources.insert(0, initResource)

        super().__init__(resources=tmpResources,
                         package=True,
                         includeDirs=includeDirs,
                         libraryDirs=libraryDirs,
                         buildDir=buildDir)


class Executable(BaseCompiler):
    def __init__(self,
                 main: Union[str, _TCompileRes],
                 resources: Optional[List[Union[
                     str,
                     PythonFile,
                     CythonFile,
                     CFile,
                     ExecResourceFile,
                     DataFile,
                     Module,
                     Package,
                     Data
                 ]]] = None,
                 name: Optional[str] = None,
                 includeDirs: Optional[List[str]] = None,
                 libraryDirs: Optional[List[str]] = None,
                 standalone: Optional[bool] = None,
                 pythonDepsDir: Optional[str] = None,
                 buildDir: Optional[str] = None):

        super().__init__(includeDirs=includeDirs, libraryDirs=libraryDirs, buildDir=buildDir)

        if isinstance(main, str):
            main = ResourcesFromFileName(main)[0]

        if resources is None:
            resources = []

        if name is None:
            name = main.name

        self.resources = []
        for resource in resources:
            if isinstance(resource, str):
                self.resources.extend(ResourcesFromFileName(resource))

            elif isinstance(resource, (PythonFile, CythonFile, CFile, ExecResourceFile, DataFile)):
                self.resources.append(resource)

            elif isinstance(resource, Module):
                self.resources.extend(resource.resources)

            elif isinstance(resource, Package):
                self.resources.extend(resource.resources)

            elif isinstance(resource, Data):
                self.resources.append(resource)

        self.main = main
        self.name = name

        self.standalone = standalone
        self.pythonDepsDir = pythonDepsDir

        if self.standalone:
            self.resources.append(Data("*.dll", homePath=sys.exec_prefix))

    def process(self):
        modules: List[Union[PythonFile, CythonFile, CFile]] = []
        sources: List[str] = []

        for resource in self.resources:
            if isinstance(resource, (PythonFile, CythonFile)):
                resource.cythonize(package=True)
                resource.freezePackage()
                sources.append(resource.outputFile)
                modules.append(resource)

            elif isinstance(resource, CFile):
                sources.append(resource.inputFile)
                modules.append(resource)

            elif isinstance(resource, ExecResourceFile):
                resource.generate()
                sources.append(resource.outputFile)

            elif isinstance(resource, DataFile):
                resource.clone(self.buildCmd.build_platlib)

            elif isinstance(resource, Data):
                resource.buildDir = self.buildDir
                resource.process()

        if isinstance(self.main, (PythonFile, CythonFile)):
            self.main.cythonize()
            self.main.freezeExecutable(modules, standalone=self.standalone, pythonDepsDir=self.pythonDepsDir)
            sources.insert(0, self.main.outputFile)

        elif isinstance(self.main, CFile):
            sources.insert(0, self.main.inputFile)

        self._compileExec(sources, self.name)

        if self.standalone:
            MakeDeps(self.main.inputFile, os.path.join(self.buildCmd.build_platlib, self.pythonDepsDir or "bin"))


def ProcessAll(*processors: Union[BaseProcessor, List[BaseProcessor]], buildDir: Optional[str] = None, cleanCache: Optional[bool] = False):
    for processor in processors:
        if isinstance(processor, (list, tuple)):
            ProcessAll(*processor, buildDir=buildDir, cleanCache=cleanCache)
            break

        processor.buildDir = buildDir
        processor.process()

        if cleanCache:
            processor.clean()
