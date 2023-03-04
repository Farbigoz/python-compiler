from compiler import Module, Package, Executable, ProcessAll
from compiler import ExecResourceFile

BUILD_DIR = "build"

modules = [
    Module(
        resources="baselib.py"
    ),
]

packages = [
    Package(
        resources=[
            "utils\\*.py",
        ]
    )
]

executables = [
    Executable(
        main="main.py",
        resources=[
            ExecResourceFile(outputFile="main.rc",
                             iconPath="main.ico",
                             fileVersion=(1, 2, 3),
                             companyName="None Studio",
                             productName="None APP")
        ]
    )
]

ProcessAll(modules + packages + executables, buildDir=BUILD_DIR, cleanCache=True)
