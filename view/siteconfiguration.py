import threading
from pathlib import Path
import customtkinter as ctk
import pandas as pd

from tkinter import messagebox
from tksheet import Sheet
from helper.api.getlist import SiteOfTenant
from helper.filehandler import FileHandler
from helper.config import save_config


class SiteConfiguration(ctk.CTkFrame):
    def __init__(self, master, controller) -> None:
        super().__init__(master=master, fg_color="transparent", corner_radius=None)
        self.dataPreview = None
        self.controller = controller
        self.FH = FileHandler()
        # Prefill initial directory from config if available
        try:
            paths_cfg = (
                self.controller.config.get("paths")
                if isinstance(self.controller.config.get("paths"), dict)
                else None
            )
            if paths_cfg and paths_cfg.get("last_import_dir"):
                self.FH.initDir = Path(paths_cfg.get("last_import_dir"))
        except Exception:
            pass

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
        # Prefill last selected file path if available
        try:
            paths_cfg = (
                self.controller.config.get("paths")
                if isinstance(self.controller.config.get("paths"), dict)
                else None
            )
            if paths_cfg and paths_cfg.get("last_import_file"):
                self.filePickerEntry.delete(0, ctk.END)
                self.filePickerEntry.insert(0, paths_cfg.get("last_import_file"))
        except Exception:
            pass
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
        """Open a file picker, load preview data, and persist last path.

        Uses FileHandler to open a file dialog starting from the last used
        directory when available, reads the selected file into a DataFrame,
        updates the UI entry, and saves last_import_dir/file in config.
        """

        self.FH.select_file()
        if not self.FH.sourceFile or not self.FH.sourceFile.exists():
            return
        # Persist last import dir and file
        try:
            self.controller.config.setdefault("paths", {})["last_import_dir"] = str(
                self.FH.sourceFile.parent
            )
            self.controller.config.setdefault("paths", {})["last_import_file"] = str(
                self.FH.sourceFile
            )
            save_config(self.controller.config)
        except Exception:
            pass
        # Update entry text
        self.filePickerEntry.delete(0, ctk.END)
        self.filePickerEntry.insert(0, str(self.FH.sourceFile))
        # Load and preview data
        try:
            self.FH.read_file()
            self.dataPreview = self.FH.sourceData
            self.__show_data()
        except Exception as e:
            messagebox.showerror(
                title="Something Went Wrong!",
                message=f"Failed to read file: {e}",
            )

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
        if self.dataPreview is not None and not self.dataPreview.empty:
            # Start in last export dir if available
            dir_hint = None
            try:
                paths_cfg = (
                    self.controller.config.get("paths")
                    if isinstance(self.controller.config.get("paths"), dict)
                    else None
                )
                dir_hint = paths_cfg.get("last_export_dir") if paths_cfg else None
            except Exception:
                dir_hint = None
            self.FH.save_file_loc(dirStr=dir_hint or self.FH.destDir).export_excel(
                data=self.dataPreview
            )
            # Persist last export directory
            try:
                self.controller.config.setdefault("paths", {})["last_export_dir"] = str(
                    self.FH.savedFile.parent
                )
                save_config(self.controller.config)
            except Exception:
                pass
        else:
            messagebox.showerror(
                title="Something Went Wrong!", message="No Data Selected!"
            )
