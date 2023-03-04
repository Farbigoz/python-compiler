import sys
import importlib.abc
import importlib.util
import importlib.machinery


class CythonPackageMetaPathFinder(importlib.abc.MetaPathFinder):
    def __init__(self, packageName, packageFilePath):
        super().__init__()
        self._packageFilePath = packageFilePath
        self._packageName = packageName

    def find_spec(self, fullname, path, target=None):
        splitName = fullname.split('.')
        if len(splitName) > 1 and splitName[-2] == self._packageName:
            fullname = fullname.replace('.', '_')
            loader = importlib.machinery.ExtensionFileLoader(fullname, self._packageFilePath)
            return importlib.util.spec_from_loader(fullname, loader)


sys.meta_path.append(CythonPackageMetaPathFinder('%s', r'%s'))
