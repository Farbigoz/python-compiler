from compiler import ExecResourceFile, Data, Package, Executable, ProcessAll


OBSBrawlhallaTournamentRes = ExecResourceFile(
    outputFile="main.rc",
    iconPath="Resources\\main.ico",
    fileVersion=(0, 0, 0),
    companyName="Cuofe Studio",
    productName="OBS Brawlhalla Tournament Manager",
    legalCopyright="(C) Cuofe Studio"
)


ProcessAll(
    Data("config.json"),
    Data("CustomStats.py"),
    Data("obs-plugins\\*.*"),
    Data([
        "Resources\\Country-flags\\*.*",
        "Resources\\Item-icons\\*.*"
    ]),

    Package([
        "utils\\*.py"
    ]),

    Package([
        "obs_websockets\\*.py"
    ]),

    Executable(
        main="main.py",
        name="OBS-Brawlhalla-tournament",
        resources=[
            "Brawlhalla.py",
            "OBS.py",
            "ScoreSystem.py",
            "StartGG.py",
            "StatsCommandsTree.py",
            "StatsProcessor.py",

            OBSBrawlhallaTournamentRes
        ]
    ),

    cleanCache=True
)
