from datetime import datetime
from pathlib import Path
from typing import Union, Dict, Any, List
import chardet
import pandas as pd
from tkinter import filedialog as fd


class FileHandler:
    def __init__(
        self,
        sourceFile: Path = None,
        sourceData: pd.DataFrame = None,
        initDir: Path = Path().home().absolute(),
        destDir: Path = Path().cwd(),
        savedFile: Path = Path("./saved.xlsx").absolute(),
    ) -> None:
        """Handling File Dialogs and File Operations"""
        self.sourceFile = sourceFile
        self.sourceData = sourceData
        self.initDir = initDir
        self.destDir = destDir
        self.savedFile = savedFile
        self.encodingList: list = [
            "ascii",
            "big5",
            "big5hkscs",
            "cp037",
            "cp273",
            "cp424",
            "cp437",
            "cp500",
            "cp720",
            "cp737",
            "cp775",
            "cp850",
            "cp852",
            "cp855",
            "cp856",
            "cp857",
            "cp858",
            "cp860",
            "cp861",
            "cp862",
            "cp863",
            "cp864",
            "cp865",
            "cp866",
            "cp869",
            "cp874",
            "cp875",
            "cp932",
            "cp949",
            "cp950",
            "cp1006",
            "cp1026",
            "cp1125",
            "cp1140",
            "cp1250",
            "cp1251",
            "cp1252",
            "cp1253",
            "cp1254",
            "cp1255",
            "cp1256",
            "cp1257",
            "cp1258",
            "euc-jp",
            "euc-jis-2004",
            "euc-jisx0213",
            "euc-kr",
            "gb2312",
            "gbk",
            "gb18030",
            "hz",
            "iso2022-jp",
            "iso2022-jp-1",
            "iso2022-jp-2",
            "iso2022-jp-2004",
            "iso2022-jp-3",
            "iso2022-jp-ext",
            "iso2022-kr",
            "latin-1",
            "iso8859-2",
            "iso8859-3",
            "iso8859-4",
            "iso8859-5",
            "iso8859-6",
            "iso8859-7",
            "iso8859-8",
            "iso8859-9",
            "iso8859-10",
            "iso8859-11",
            "iso8859-13",
            "iso8859-14",
            "iso8859-15",
            "iso8859-16",
            "johab",
            "koi8-r",
            "koi8-t",
            "koi8-u",
            "kz1048",
            "mac-cyrillic",
            "mac-greek",
            "mac-iceland",
            "mac-latin2",
            "mac-roman",
            "mac-turkish",
            "ptcp154",
            "shift-jis",
            "shift-jis-2004",
            "shift-jisx0213",
            "utf-32",
            "utf-32-be",
            "utf-32-le",
            "utf-16",
            "utf-16-be",
            "utf-16-le",
            "utf-7",
            "utf-8",
            "utf-8-sig",
        ]

    def select_directory(
        self, dirStr: str | Path = Path().home().absolute()
    ) -> "FileHandler":
        """Select Directory / Folder Dialog

        Args:
            dirStr (Path, optional): Defined where the directory or folder should start. Defaults to Path().home().absolute().

        Returns:
            FileHandler: FileHandler Class Object
        """
        destDirectory = fd.askdirectory(
            initialdir=dirStr,
            mustexist=True,
            title="Select Directory / Folder",
        )
        self.initDir = (
            Path(destDirectory).absolute() if destDirectory != "" else self.initDir
        )
        return self

    def save_file_loc(
        self,
        fileName="EXPORT.xlsx",
        dirStr: str | Path = Path().home().absolute(),
        timeStamp: bool = True,
        promptDialog: bool = True,
    ) -> "FileHandler":
        """Select File Location Dialog

        Args:
            fileName (str, optional): Defined the file output name. Defaults to "EXPORT.xlsx".
            dirStr (str | Path, optional): Defined where the dialog should start. Defaults to Path().home().absolute().
            timeStamp (bool, optional): With timestamp?. Defaults to True.
            promptDialog (bool, optional): Prompt the dialog?. Defaults to True.

        Returns:
            FileHandler: FileHandler Class Object
        """
        if timeStamp:
            fileName = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-{fileName}"
        filetype = (
            ("Excel Files", "*.xls *.xlsx *.xlsm *.xlsb"),
            ("CSV Files", "*.csv"),
            ("All Files", "*.*"),
        )
        res = (
            fd.asksaveasfilename(
                title="Save File As ...",
                initialdir=dirStr if dirStr != "" else self.destDir,
                filetypes=filetype,
                defaultextension=".xlsx",
                initialfile=fileName,
                confirmoverwrite=True,
            )
            if promptDialog
            else f"{dirStr}/{fileName}"
        )
        self.savedFile = Path(res).absolute() if res != "" else self.savedFile
        return self

    def select_file(self, title: str = "Open Source File") -> "FileHandler":
        """Select File Dialog

        Returns:
            FileHandler: FileHandler Class Object
        """
        filetype = (
            ("CSV Files", "*.csv"),
            ("Excel Files", "*.xls *.xlsx *.xlsm *.xlsb"),
            ("All Files", "*.*"),
        )
        res = fd.askopenfilename(
            title=title, initialdir=self.initDir, filetypes=filetype
        )
        self.sourceFile = Path(res).absolute() if res != "" else self.sourceFile
        return self

    def encoder_detect(self) -> dict | None:
        """Detect File Encoding

        Returns:
            FileHandler: FileHandler Class Object
        """
        with open(self.sourceFile, "rb") as file:
            data = file.read()
            res = chardet.detect(data)
            file.close()
            if res["encoding"].lower() in self.encodingList:
                return res
            else:
                return None

    def read_file(self, skipRows: int = 0) -> "FileHandler":
        """Read Source File as DataFrame

        Args:
            skipRows (int, optional): How many line should be skipped. Defaults to 0.

        Raises:
            ValueError: None Value in `FileHandler.sourcefile`
            ValueError: Invalid Encoding
            ValueError: Invalid File Type or No File Selected!

        Returns:
            FileHandler: FileHandler Class Object
        """
        if not self.sourceFile.is_file():
            raise FileNotFoundError(f"{self.sourceFile} is not a file!")
        match self.sourceFile.suffix:
            case ".csv":
                if self.encoder_detect() is None:
                    raise ValueError("Invalid Encoding", self.encoder_detect())
                self.sourceData = pd.read_csv(
                    filepath_or_buffer=self.sourceFile, skiprows=skipRows
                )
            case ".xlsx" | ".xls" | ".xlsm" | ".xlsb":
                self.sourceData = pd.read_excel(io=self.sourceFile, skiprows=skipRows)
            case _:
                raise TypeError("Invalid File Type", self.sourceFile.suffix)
        return self

    def export_excel(
        self,
        data: Union[
            pd.DataFrame, Dict[str, Union[List, pd.DataFrame, Dict[str, Any]]]
        ] = None,
    ) -> "FileHandler":
        """Export DataFrame to Excel

        Args:
            data (dict[str, pd.DataFrame  |  dict  |  list] | pd.DataFrame, optional): data to be exported. Defaults to None.

        Raises:
            ValueError: Invalid Data Type

        Returns:
            FileHandler: FileHandler Class Object
        """
        data = data if data is not None else self.sourceData
        writer = pd.ExcelWriter(path=self.savedFile, engine="xlsxwriter")
        match data:
            case pd.DataFrame():
                data.to_excel(excel_writer=writer, sheet_name="Sheet1")
                writer.close()
            case dict():
                for key in data.keys():
                    pd.DataFrame(data=data[key]).to_excel(
                        excel_writer=writer, sheet_name=key
                    )
                writer.close()
            case _:
                raise ValueError("Invalid Data Type", type(data))
        return self

    def flatten_dict(
        self, data: dict, parent_key: str = "", sep: str = "_", level: int = 1
    ) -> dict:
        """Flatten a nested dictionary

        Args:
            data (dict): Data with nested dictionary
            parent_key (str, optional): Which key is to parented. Defaults to "".
            sep (str, optional): New key separators. Defaults to "_".
            level (int, optional): How many nested shall there be. Defaults to 1.

        Returns:
            FileHandler: FileHandler Class Object
        """
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key != "" else key
            if isinstance(value, dict) and level > 0:
                items.extend(
                    self.flatten_dict(
                        data=value, parent_key=new_key, level=level - 1
                    ).items()
                )
            else:
                items.append((new_key, value))
        return dict(items)

    def open_explorer(self) -> "FileHandler":
        """Open File Explorer

        Returns:
            FileHandler: FileHandler Class Object
        """
        from subprocess import run
        from platform import system

        match system():
            case "Windows":
                run(args=["explorer", "/select,", self.savedFile])
            case "Darwin":
                run(args=["open", "-R", self.savedFile])
            case "Linux":
                run(args=["xdg-open", self.savedFile.parent])

        return self
