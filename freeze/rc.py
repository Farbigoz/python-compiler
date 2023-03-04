from typing import Optional, Tuple

_RC_CODE_TEMPLATE = """
#include <windows.h>
#include <winver.h>

{iconPath}

1 VERSIONINFO
FILEVERSION {verMajor},{verMinor},{verPath},0
BEGIN
  BLOCK "StringFileInfo"
  BEGIN
    BLOCK "040904B0"
    BEGIN
{fileInf}
    END
  END

  BLOCK "VarFileInfo"
  BEGIN
    VALUE "Translation", 0x419, 1200
  END
END
"""


def GetRcCode(iconPath: Optional[str] = None,
              fileVersion: Optional[Tuple[int, int, int]] = None,
              companyName: Optional[str] = None,
              fileDescription: Optional[str] = None,
              internalName: Optional[str] = None,
              originalFilename: Optional[str] = None,
              productName: Optional[str] = None,
              productVersion: Optional[Tuple[int, int, int]] = None,
              comments: Optional[str] = None,
              legalCopyright: Optional[str] = None):

    formatIconPath = ""
    if iconPath is not None:
        formatIconPath = f"IDI_ICON1 ICON \"{iconPath}\""

    if fileVersion is None:
        fileVersion = (0, 0, 0)

    verMajor, verMinor, verPath = fileVersion

    fileInf = f"      VALUE \"FileVersion\", \"{verMajor}.{verMinor}.{verPath}\"\n"

    if companyName is not None:
        fileInf += f"      VALUE \"CompanyName\", \"{companyName}\"\n"

    if fileDescription is not None:
        fileInf += f"      VALUE \"FileDescription\", \"{fileDescription}\"\n"

    if internalName is not None:
        fileInf += f"      VALUE \"InternalName\", \"{internalName}\"\n"

    if originalFilename is not None:
        fileInf += f"      VALUE \"OriginalFilename\", \"{originalFilename}\"\n"

    if productName is not None:
        fileInf += f"      VALUE \"ProductName\", \"{productName}\"\n"

    if productVersion is not None:
        fileInf += f"      VALUE \"ProductVersion\", \"{productVersion[0]}.{productVersion[1]}.{productVersion[2]}\"\n"

    if comments is not None:
        fileInf += f"      VALUE \"Comments\", \"{comments}\"\n"

    if legalCopyright is not None:
        fileInf += f"      VALUE \"LegalCopyright\", \"{legalCopyright}\"\n"

    return _RC_CODE_TEMPLATE.format(iconPath=formatIconPath,
                                    verMajor=verMajor,
                                    verMinor=verMinor,
                                    verPath=verPath,
                                    fileInf=fileInf)

