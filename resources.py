import os

from typing import Optional, List, Tuple, TypeVar, Union

from Cython.Build.Dependencies import cythonize_one
from Cython.Compiler.Main import CompilationOptions

from .freeze.package import FreezePackage, AddPackageFinderCode
from .freeze.executable import AddExecutableFreezeCode
from .freeze.rc import GetRcCode


CPP_EXT = ".cpp"

COMPILER_DIRECTIVES = {
    'language_level': "3",
    'always_allow_keywords': True,
}


def _getExtensionName(fileName: str, withoutInit: bool = True) -> str:
    tmpName = os.path.splitext(fileName)[0]
    name = ""
    while tmpName:
        tmpName, level = os.path.split(tmpName)

        if withoutInit and level == "__init__":
            continue

        name = f"{level}.{name}"

    return name.strip(".")


class BaseResource:
    supportExt: Optional[List[str]] = None

    def __init__(self, inputFile: Optional[str] = None, outputFile: Optional[str] = None, homePath: Optional[str] = None):
        self.inputFile = inputFile
        self.outputFile = outputFile
        self.homePath = homePath
        self.inputFilePath = inputFile

        if (self.inputFile is not None) and (self.homePath is not None):
            self.inputFilePath = os.path.join(homePath, inputFile)

        if (inputFile is not None) and (self.supportExt is not None):
            fileExt = os.path.splitext(self.inputFile)[1]
            if fileExt not in self.supportExt:
                raise Exception(f"Not support ext: \"{fileExt}\"")

    def __repr__(self) -> str:
        return f"<{self.__module__}.{self.__class__.__name__} resource: " \
               f"(inputFile=\"{self.inputFile}\", outputFile=\"{self.outputFile}\")>"

    def getInputFileName(self) -> str:
        return os.path.splitext(os.path.split(self.inputFile)[1])[0]

    def getOutputFileName(self) -> str:
        return os.path.splitext(os.path.split(self.outputFile)[1])[0]


class BaseResourceWithName(BaseResource):
    name: str
    fullName: str

    def __init__(self, inputFile: str, outputFile: Optional[str] = None, name: Optional[str] = None):
        super().__init__(inputFile, outputFile)

        if name is None:
            name = _getExtensionName(self.inputFile)

        self.name = name
        self.fullName = _getExtensionName(self.inputFile, False)

    def __repr__(self) -> str:
        return f"<{self.__module__}.{self.__class__.__name__} resource: " \
               f"(inputFile=\"{self.inputFile}\", outputFile=\"{self.outputFile}\", name=\"{self.name}\")>"


class CythonizeResource(BaseResourceWithName):
    def __init__(self, inputFile: str, name: Optional[str] = None):
        super().__init__(inputFile, None, name)

        self._cythonized = False
        self.package = False

        self.cppOptions = CompilationOptions(compiler_directives=COMPILER_DIRECTIVES)
        self.cppOptions.cplus = True

        self.outputFile = os.path.splitext(self.inputFile)[0] + CPP_EXT

    def _checkCythonized(self):
        if not self._cythonized:
            raise Exception(f"File '{self.inputFile}' not cythonized!")

    def _getCythonizedCode(self) -> str:
        self._checkCythonized()

        with open(self.outputFile, "r") as f:
            content = f.read()

        return content

    def _setCythonizedCode(self, content):
        self._checkCythonized()

        with open(self.outputFile, "w") as f:
            f.write(content)

    def cythonize(self, package: Optional[bool] = None):
        if self._cythonized:
            return

        if package is not None:
            self.package = package

        if self.package:
            name = self.name.replace(".", "_")
        else:
            name = self.name.split(".")[-1]

        cythonize_one(
            pyx_file=self.inputFile,
            c_file=self.outputFile,
            fingerprint=None,
            quiet=False,
            options=self.cppOptions,
            full_module_name=name
        )

        self._cythonized = True

    def freezePackage(self):
        self._checkCythonized()

        if not self.package:
            raise Exception("Cythonized without 'package=True' arg")

        packageName = None
        packagePath = None
        addPackageFinder = False

        if self.fullName.endswith("__init__"):
            packageName = self.name.split(".")[-1]
            packagePath = self.name
            addPackageFinder = True

        elif len(self.name.split(".")) > 1:
            packageName = self.name.split(".")[-2]
            packagePath = ".".join(self.name.split(".")[:-1])

        if (packageName is not None) and (packagePath is not None):
            code = self._getCythonizedCode()

            code = FreezePackage(code, packageName=packageName, packagePath=packagePath)

            if addPackageFinder:
                code = AddPackageFinderCode(code)

            self._setCythonizedCode(code)

    def freezeExecutable(self,
                         modules: Optional[List["CythonizeResource"]] = None,
                         standalone: Optional[bool] = False,
                         pythonDepsDir: Optional[str] = None):
        self._checkCythonized()

        if modules is None:
            modules = []

        moduleNames = [module.name for module in modules]

        code = self._getCythonizedCode()

        code = AddExecutableFreezeCode(code, self.name, moduleNames, standalone=standalone, pythonDepsDir=pythonDepsDir)

        self._setCythonizedCode(code)


class PythonFile(CythonizeResource):
    supportExt = [".py"]


class CythonFile(CythonizeResource):
    supportExt = [".pyx", ".pxd"]


class CFile(BaseResourceWithName):
    supportExt = [".c", ".h", ".cpp", ".hpp"]


class ExecResourceFile(BaseResource):
    supportExt = [".rc"]

    def __init__(self,
                 outputFile: str,
                 iconPath: Optional[str] = None,
                 fileVersion: Optional[Tuple[int, int, int]] = None,
                 companyName: Optional[str] = None,
                 fileDescription: Optional[str] = None,
                 internalName: Optional[str] = None,
                 originalFilename: Optional[str] = None,
                 productName: Optional[str] = None,
                 productVersion: Optional[Tuple[int, int, int]] = None,
                 comments: Optional[str] = None,
                 legalCopyright: Optional[str] = None):

        super().__init__(None, outputFile)

        self.iconPath = iconPath
        self.fileVersion = fileVersion
        self.companyName = companyName
        self.fileDescription = fileDescription
        self.internalName = internalName
        self.originalFilename = originalFilename
        self.productName = productName
        self.productVersion = productVersion
        self.comments = comments
        self.legalCopyright = legalCopyright

    def generate(self):
        print(f"Generate {self.outputFile}.rc")

        code = GetRcCode(iconPath=self.iconPath,
                         fileVersion=self.fileVersion,
                         companyName=self.companyName,
                         fileDescription=self.fileDescription,
                         internalName=self.internalName,
                         originalFilename=self.originalFilename,
                         productName=self.productName,
                         productVersion=self.productVersion,
                         comments=self.comments,
                         legalCopyright=self.legalCopyright)

        with open(self.outputFile, "w") as f:
            f.write(code)

    def fileExtCheck(self, fileExt: str) -> bool:
        return fileExt in [".rc"]


class DataFile(BaseResource):
    def __init__(self, inputFile: str, homePath: Optional[str] = None):
        super().__init__(inputFile, homePath=homePath)

        if not os.path.exists(self.inputFilePath):
            raise Exception(f"File \"{self.inputFilePath}\' not exist")

    def clone(self, path: str):
        print(f"Clone data file {self.inputFilePath}")

        outputFile = os.path.join(path, self.inputFile)
        outputPath, _ = os.path.split(outputFile)

        if not os.path.exists(outputPath):
            os.makedirs(outputPath, exist_ok=True)

        with open(self.inputFilePath, "rb") as src:
            with open(outputFile, "wb") as dst:
                dst.write(src.read())


RESOURCE_CLASSES = [
    PythonFile,
    CythonFile,
    CFile,
    ExecResourceFile
]


_TBaseRes = TypeVar('_TBaseRes', bound=BaseResource)
_TStr = Union[str, List['_TStr']]


def ResourcesFromFileName(inputFile: _TStr, clone: bool = False, homePath: Optional[str] = None) -> List[_TBaseRes]:
    resources: List[_TBaseRes] = []

    if homePath is None:
        homePath = ""

    if isinstance(inputFile, (list, tuple)):
        for _inputFile in inputFile:
            resources.extend(ResourcesFromFileName(_inputFile, clone, homePath=homePath))

        return resources

    fileDir, fullFileName = os.path.split(inputFile)
    fileName, fileExt = os.path.splitext(fullFileName)

    if fileName == "*" or fileExt == ".*":
        for fileInDir in os.listdir(os.path.join(homePath, fileDir)):
            if not os.path.isfile(os.path.join(homePath, fileDir, fileInDir)):
                continue

            fileInDirName, fileInDirExt = os.path.splitext(fileInDir)

            if fileName not in ["*", fileInDirName]:
                continue

            if fileExt not in [".*", fileInDirExt]:
                continue

            resources.extend(ResourcesFromFileName(os.path.join(fileDir, fileInDir), clone, homePath=homePath))

    elif clone:
        resources.append(DataFile(inputFile, homePath=homePath))

    else:
        for resCls in RESOURCE_CLASSES:
            if fileExt in resCls.supportExt:
                resources.append(resCls(inputFile))
                break
        else:
            resources.append(BaseResource(inputFile))

    return resources

