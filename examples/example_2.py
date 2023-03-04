from compiler import Module, Package, Executable, Data
from compiler import ExecResourceFile


appCompiler = Executable(
    main="main.py",
    resources=[
        Module("baselib.py"),
        Package(["utils\\__init__.py", "utils\\utillib.py"]),
        Data("utils\\__init__.*"),
        ExecResourceFile(outputFile="main.rc",
                         iconPath="main.ico",
                         fileVersion=(1, 2, 3))
    ],
    name="test",
)

appCompiler.process()
appCompiler.clean()
