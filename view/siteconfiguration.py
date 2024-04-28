import threading
import customtkinter as ctk
import pandas as pd

from tkinter import messagebox
from tksheet import Sheet
from helper.api.getlist import SiteOfTenant
from helper.filehandler import FileHandler


class SiteConfiguration(ctk.CTkFrame):
    def __init__(self, master, controller) -> None:
        super().__init__(master=master, fg_color="transparent", corner_radius=None)
        self.dataPreview = None
        self.controller = controller
        self.FH = FileHandler()

        ### Source File ###
        self.filePickerFrame = ctk.CTkFrame(self)
        self.filePickerFrame.pack(fill="x", anchor="n", padx=10, pady=10)
        dataPickerTab = ctk.CTkTabview(master=self.filePickerFrame, height=50)
        dataPickerTab.add("Online")
        dataPickerTab.add("From File")
        dataPickerTab.set("Online")
        dataPickerTab.pack(fill="x", anchor="center")

        ### # From File # ###
        ctk.CTkButton(
            master=dataPickerTab.tab("Online"),
            text="Get Data",
            command=lambda: self.download_list(),
        ).pack()

        ### # From File # ###
        self.filePickerEntry = ctk.CTkEntry(
            master=dataPickerTab.tab("From File"),
            placeholder_text="Source File Directory ...",
        )
        self.filePickerEntry.pack(pady=10, padx=10, side="left", fill="x", expand=True)
        ctk.CTkButton(
            master=dataPickerTab.tab("From File"),
            text="Choose File",
            command=lambda: threading.Thread(target=self.pick_source_file).start(),
        ).pack(padx=10, pady=10, side="right", fill="none", expand=False)

        ### File Manipulation ###
        self.fileManipulationFrame = ctk.CTkFrame(master=self, fg_color="transparent")
        self.fileManipulationFrame.pack(pady=(0, 10), padx=10, fill="both", expand=True)

        ### File Viewer ###
        self.fileViewerFrame = ctk.CTkFrame(master=self.fileManipulationFrame)
        self.fileViewerFrame.pack(pady=(0, 10), fill=ctk.BOTH, expand=True)

        ### Automation Execute ###
        self.automationExecuteFrame = ctk.CTkFrame(
            master=self.fileManipulationFrame, fg_color="transparent"
        )
        self.automationExecuteFrame.pack(fill="x", expand=False)
        ctk.CTkButton(
            master=self.automationExecuteFrame,
            text="Save",
            anchor="center",
            command=lambda: self.save_to_file(),
        ).pack(side="left")

    def pick_source_file(self):
        file = self.FH.select_file()
        self.dataPreview = self.FH.sourcedata
        # print(self.dataPreview.columns.values.tolist())
        self.__show_data()
        if file != "":
            self.filePickerEntry.delete(0, ctk.END)
            self.filePickerEntry.insert(0, file)

    def download_list(self) -> None:
        download = SiteOfTenant(
            bearer_token=self.controller.authRes["data"]["access_token"]
        )
        try:
            res = download.request()
            # print(res["data"]["items"])
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
        self.dataPreview = pd.DataFrame(
            data=[
                self.FH.flatten_dict(data=row, level=1) for row in res["data"]["items"]
            ]
        )
        self.__show_data()

    def __show_data(self) -> None:
        table = Sheet(
            parent=self.fileViewerFrame,
            data=self.dataPreview.values.tolist(),
            show_default_index_for_empty=False,
        )
        table.enable_bindings()
        table.set_header_data(value=self.dataPreview.columns.values.tolist())
        table.pack(anchor="center", expand=True, fill="both")

    def save_to_file(self) -> None:
        if self.dataPreview is not None or "":
            self.FH.save_as_excel(data=self.dataPreview)
        else:
            messagebox.showerror(
                title="Something Went Wrong!", message="No Data Selected!"
            )
