from datetime import datetime
import pathlib
import chardet
import pandas as pd
from tkinter import filedialog as fd
from tkinter.messagebox import askokcancel, showerror, showinfo


class FileHandler:
    def __init__(self) -> None:
        self.sourcefile: str = None
        self.sourcedata: pd.DataFrame = None
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
            "euc_jp",
            "euc_jis_2004",
            "euc_jisx0213",
            "euc_kr",
            "gb2312",
            "gbk",
            "gb18030",
            "hz",
            "iso2022_jp",
            "iso2022_jp_1",
            "iso2022_jp_2",
            "iso2022_jp_2004",
            "iso2022_jp_3",
            "iso2022_jp_ext",
            "iso2022_kr",
            "latin_1",
            "iso8859_2",
            "iso8859_3",
            "iso8859_4",
            "iso8859_5",
            "iso8859_6",
            "iso8859_7",
            "iso8859_8",
            "iso8859_9",
            "iso8859_10",
            "iso8859_11",
            "iso8859_13",
            "iso8859_14",
            "iso8859_15",
            "iso8859_16",
            "johab",
            "koi8_r",
            "koi8_t",
            "koi8_u",
            "kz1048",
            "mac_cyrillic",
            "mac_greek",
            "mac_iceland",
            "mac_latin2",
            "mac_roman",
            "mac_turkish",
            "ptcp154",
            "shift_jis",
            "shift_jis_2004",
            "shift_jisx0213",
            "utf_32",
            "utf_32_be",
            "utf_32_le",
            "utf_16",
            "utf_16_be",
            "utf_16_le",
            "utf_7",
            "utf_8",
            "utf_8_sig",
        ]

    def select_file(self) -> str:
        filetype = (
            ("Excel Files", "*.xls *.xlsx *.xlsm *.xlsb"),
            ("CSV Files", "*.csv"),
            ("All Files", "*.*"),
        )

        self.sourcefile = fd.askopenfilename(
            title="Open Source File", initialdir="/", filetypes=filetype
        )

        handlefile = self.handling_file()

        if not handlefile.empty or self.sourcefile != "":
            return self.sourcefile
        return ""

    def encoder_detect(self) -> dict:
        with open(self.sourcefile, "rb") as file:
            data = file.read()
            res = chardet.detect(data)
            file.close()
            if res in self.encodingList:
                return res
            else:
                return None

    def handling_file(self) -> pd.DataFrame:
        match pathlib.Path(self.sourcefile).suffix:
            case ".csv":
                if askokcancel(
                    title="Confirm Source File?",
                    message="Make sure you choose CSV file separated by ',' or ';'!",
                ):
                    encoding = self.encoder_detect()
                    if encoding:
                        self.sourcedata = pd.read_csv(
                            filepath_or_buffer=self.sourcefile,
                            encoding=encoding["encoding"],
                        )
                        return self.sourcedata
                    else:
                        pass
                else:
                    return {}
            case ".xlsx" | ".xls" | ".xlsm" | ".xlsb":
                if askokcancel(
                    title="Confirm Source File?",
                    message="Make sure you choose Correct Excel Files",
                ):
                    # print(
                    #     pd.read_excel(self.sourcefile).apply(
                    #         lambda x: x.pd.value_counts().get("-", 0), axis=1
                    #     )
                    # )
                    self.sourcedata = pd.read_excel(io=self.sourcefile)
                    return self.sourcedata
                else:
                    return {}
        showerror(
            title="Your File is not Recognized",
            message="Please Choose available extension",
        )
        return {}

    def save_as_excel(self, data: list, flatten: bool = False) -> None:
        # print(type(data), data, sep="\n")
        fileLoc = fd.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=(
                ("Excel Files", "*.xls *.xlsx *.xlsm *.xlsb"),
                ("All Files", "*.*"),
            ),
            initialdir="~",
            initialfile=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_Tenant_List",
            title="Export as Excel File",
        )
        if fileLoc is not None or "":
            # pd.read_json(data).to_excel(fileLoc)
            if flatten:
                pd.DataFrame(
                    data=[self.flatten_dict(data=row, level=1) for row in data]
                ).to_excel(excel_writer=fileLoc, index=False, header=True)
            else:
                pd.DataFrame(data=data).to_excel(
                    excel_writer=fileLoc, index=False, header=True
                )
            showinfo(title="File Saved", message=f"File Saved to {fileLoc}")

    def flatten_dict(
        self, data: dict, parent_key: str = "", sep: str = "_", level: int = 1
    ) -> dict:
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
