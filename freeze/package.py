import os

_PACKAGE_FINDER_SCRIPT_PATH = os.path.join(os.path.split(__file__)[0], "_packageFinderScript.py")

_PACKAGE_FINDER_CODE = """
  auto __pkgScript = {pkgFinderScript};

  PyRun_SimpleString(
    PyUnicode_AsUTF8(
      PyUnicode_FromFormat(
        __pkgScript,
        PyUnicode_AsUTF8(PyObject_GetAttrString(__pyx_m, (char*)"__package__")),
        PyUnicode_AsUTF8(PyObject_GetAttrString(__pyx_m, (char*)"__file__"))
      )
    )
  );
"""


def GetPackageFinderCode() -> str:
    with open(_PACKAGE_FINDER_SCRIPT_PATH, "r") as f:
        pkgFinderScript = f.read()

    pkgFinderScript = '""\n  "' + pkgFinderScript.replace("\n", '\\n"\n  "')[:-4]

    pkgFinderCode = _PACKAGE_FINDER_CODE.format(pkgFinderScript=pkgFinderScript)

    return pkgFinderCode


def AddPackageFinderCode(code: str) -> str:
    if 'if (unlikely(__Pyx_copy_spec_to_module(spec, moddict, "parent", "__package__", 1) < 0)) goto bad;' in code:
        raise Exception("Package not freezed.")

    execCodePos = code.find("/*--- Execution code ---*/")
    endifBeforeExecCodePos = code[execCodePos:].find("#endif")
    skipEndifPos = code[execCodePos + endifBeforeExecCodePos:].find("\n") + 1

    return (
            code[:execCodePos + endifBeforeExecCodePos + skipEndifPos] +
            GetPackageFinderCode() +
            code[execCodePos + endifBeforeExecCodePos + skipEndifPos:]
    )


def FreezePackage(code: str, packageName: str, packagePath: str) -> str:
    # Freeze '__package__'
    code = code.replace(
        'if (unlikely(__Pyx_copy_spec_to_module(spec, moddict, "parent", "__package__", 1) < 0)) goto bad;',
        f'if (PyDict_SetItemString(moddict, "__path__", PyUnicode_FromString("{packagePath}")) < 0) goto bad;'
    )

    # Freeze '__path__'
    code = code.replace(
        'if (unlikely(__Pyx_copy_spec_to_module(spec, moddict, "submodule_search_locations", "__path__", 0) < 0)) goto bad;',
        f'if (PyDict_SetItemString(moddict, "__package__", PyUnicode_FromString("{packageName}")) < 0) goto bad;'
    )

    return code
