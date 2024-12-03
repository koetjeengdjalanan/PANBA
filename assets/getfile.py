import os
import sys


class GetFile:
    """
    Get path of assets properly
    """

    @staticmethod
    def getAssets(file_name: str) -> str:
        if hasattr(sys, "_MEIPASS"):
            path = os.path.join(sys._MEIPASS, "assets", file_name)
        else:
            path = os.path.join(os.path.dirname(__file__), "..", "assets", file_name)

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"The asset file '{file_name}' does not exist at path '{path}'"
            )

        return path
