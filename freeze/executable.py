import os

from typing import List, Optional


_EXECUTABLE_FREEZE_CODE_PATH = os.path.join(os.path.split(__file__)[0], "_executableFreezeCode.cpp")


def GetExecutableFreezeCode(executeModuleName: str,
                            modulesNames: Optional[List[str]] = None,
                            standalone: Optional[bool] = False,
                            pythonDepsDir: Optional[str] = None) -> str:
    if modulesNames is None:
        modulesNames = []

    with open(_EXECUTABLE_FREEZE_CODE_PATH, "r") as f:
        code = f.read()

    modInitDef = ""
    modInitMap = ""
    for moduleName in [executeModuleName] + modulesNames:
        moduleNameWithoutDots = moduleName.replace(".", "_")

        modInitDef += f'PyMODINIT_FUNC MODINIT({moduleNameWithoutDots}) (void);\n'
        modInitMap += f'    {{"{moduleName}", MODINIT({moduleNameWithoutDots})}},\n'

    code = code.replace("__pyx_module_is_main_X", f"__pyx_module_is_main_{executeModuleName}")
    code = code.replace("/* ModInit definitions */", modInitDef)
    code = code.replace("/* ModInit map */", modInitMap)

    if standalone:
        code = code.replace("/* Python init func */", "InitPythonStandalone(argc, argv);")
    else:
        code = code.replace("/* Python init func */", "InitPythonGlobal(argc, argv);")

    if pythonDepsDir is not None:
        code = code.replace("L\"\\\\bin", f"L\"\\\\{pythonDepsDir}")

    return code


def AddExecutableFreezeCode(code: str,
                            executeModuleName: str,
                            modulesNames: List[str],
                            standalone: Optional[bool] = False,
                            pythonDepsDir: Optional[str] = None) -> str:
    return code + "\n\n\n" + GetExecutableFreezeCode(executeModuleName, modulesNames, standalone=standalone, pythonDepsDir=pythonDepsDir)
