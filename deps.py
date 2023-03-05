import os
import sys
import zipfile
import tempfile
import subprocess

from typing import List


def ModulesFromNames(names: list) -> dict:
    return {name: sys.modules[name] for name in names}


PYTHON_PATH = sys.exec_prefix
PYTHON_LIB_PATH = os.path.join(PYTHON_PATH, "lib")
PYTHON_DLLS_PATH = os.path.join(PYTHON_PATH, "DLLs")
PYTHON_SITE_PACKAGES_PATH = os.path.join(PYTHON_LIB_PATH, "site-packages")


REQUIRED_LIB_FILES = [
    "stringprep.py"
]

REQUIRED_DLL_FILES = [
    "unicodedata.pyd"
]


def AnalyzeDeps(file: str):
    deps = []

    stderrFile = tempfile.TemporaryFile()

    proc = subprocess.Popen([sys.executable, "-v", "-m", file],
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=stderrFile)

    print(f"Analyze \"{file}\"...")
    try:
        proc.wait(3)
    except:
        pass

    proc.terminate()
    proc.wait()

    print("read sdterr")

    stderrFile.seek(0)
    cacheLines = []
    while True:
        _r = stderrFile.readline()
        if _r == b"":
            break

        raw = _r.decode()
        line, raw = raw.split("\n", 1)

        # print("[RAW LINE]            ", line)

        if line.startswith("import"):
            depFiles: List[str]
            _importLine: str
            _importName: str
            _loaderClassName: str

            depFiles = []

            _importLine = line.replace("import", "", 1)
            _importName, _loaderClassName = _importLine.split(" # ")
            _importName = _importName.strip(" '")

            if _importName == "_ctypes":
                deps.append(os.path.join(PYTHON_DLLS_PATH, "libffi-7.dll"))

            for cacheLine in cacheLines:
                cacheLine: str
                cacheLine = cacheLine.replace("\\\\", "\\")

                pythonPathFindPos = cacheLine.rfind(PYTHON_PATH)
                while pythonPathFindPos != -1:
                    depPath = cacheLine[pythonPathFindPos:]
                    cacheLine = cacheLine[:pythonPathFindPos]

                    for ext in [".pyd", ".pyc", ".py"]:
                        extFindPos = depPath.find(ext)
                        if extFindPos != -1:
                            if ext != ".pyc":
                                depFiles.append(depPath[:extFindPos + len(ext)])
                            break

                    pythonPathFindPos = cacheLine.find(PYTHON_PATH)

            deps.extend(set(depFiles))

            cacheLines.clear()

        else:
            cacheLines.append(line)

    for libFile in REQUIRED_LIB_FILES:
        deps.append(os.path.join(PYTHON_LIB_PATH, libFile))

    for dllFile in REQUIRED_DLL_FILES:
        deps.append(os.path.join(PYTHON_DLLS_PATH, dllFile))

    return deps


def PackDeps(deps: List[str], outputDir: str):
    libFiles = []
    libFolders = []
    dllLibFiles = []

    for dep in sorted(set(deps)):
        if PYTHON_DLLS_PATH in dep:
            dllLibFiles.append(dep)

        elif PYTHON_SITE_PACKAGES_PATH in dep:
            dep, folder = os.path.split(dep)
            while dep != PYTHON_SITE_PACKAGES_PATH:
                dep, folder = os.path.split(dep)

            libFolders.append(os.path.join(PYTHON_SITE_PACKAGES_PATH, folder))

        elif PYTHON_LIB_PATH in dep:
            if os.path.split(dep)[0] == PYTHON_LIB_PATH:
                libFiles.append(dep)

            else:
                dep, folder = os.path.split(dep)
                while dep != PYTHON_LIB_PATH:
                    dep, folder = os.path.split(dep)

                libFolders.append(os.path.join(PYTHON_LIB_PATH, folder))

    with zipfile.ZipFile(os.path.join(outputDir, 'python.zip'), mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for file in libFiles:
            print("Pack lib module:", file)

            zf.write(file, file.replace(PYTHON_LIB_PATH, "").strip("\\/"))

        for folder in set(libFolders):
            print("Pack lib package:", folder)

            for dirPath, dirs, files in os.walk(folder):
                if dirPath.endswith("__pycache__"):
                    continue

                for file in files:
                    file = os.path.join(dirPath, file)
                    print("Pack lib package file:", file)

                    zf.write(file, file.replace(PYTHON_LIB_PATH, "").strip("\\/"))

    for dllFile in dllLibFiles:
        print("Copy dll file:", dllFile)

        dllFileName = os.path.split(dllFile)[1]
        with open(dllFile, "rb") as src:
            with open(os.path.join(outputDir, dllFileName), "wb") as dst:
                dst.write(src.read())


def MakeDeps(src: str, outputDir: str):
    if not os.path.exists(outputDir):
        os.makedirs(outputDir, exist_ok=True)

    PackDeps(AnalyzeDeps(src), outputDir)
