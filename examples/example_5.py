from compiler import Module, ProcessAll


FastArray = Module(
    resources=[
        "fastArr\\fastArr.pyx",
        "fastArr\\fastArr.h",
        "fastArr\\fastArr.cpp"
    ],
    includeDirs=["fastArr\\inc\\"]
)


ProcessAll(FastArray, cleanCache=True, buildDir="BUILD")
