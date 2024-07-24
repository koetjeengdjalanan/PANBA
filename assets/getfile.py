import os
import sys


class GetFile:
    """
    Get path of assets properly
    """

    def getAssets(file_name: str):
        if hasattr(sys, "__MEIPASS"):
            return os.path.join(sys._MEIPASS, "assets", file_name)
        else:
            return os.path.join("assets", file_name)
