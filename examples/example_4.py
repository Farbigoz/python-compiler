from compiler import Package, ProcessAll


UtilsPackage = Package([
    "utils\\*.py",
])

ApiPackage = Package([
    "api\\*.py"
    "api\\defs\\calls.py"
])


ProcessAll(UtilsPackage, ApiPackage, cleanCache=True, buildDir="BUILD")
