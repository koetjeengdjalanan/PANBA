"""Site Configuration View."""

import threading
from pathlib import Path
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk
import pandas as pd
from tksheet import Sheet

from helper.api.getlist import SiteOfTenant
from helper.config import save_config
from helper.filehandler import FileHandler

if TYPE_CHECKING:
    from main import App


class SiteConfiguration(ctk.CTkFrame):
    """A customtkinter frame for configuring site data.

    This class provides a user interface for loading site information either from a
    local file (e.g., CSV, Excel) or by downloading it from an online API. It
    displays the loaded data in a spreadsheet-like view and allows the user to
    save the data back to a file.
    The UI is composed of several frames:
    - A tabbed view to select the data source ('Online' or 'From File').
    - A file picker for selecting a local source file.
    - A data viewer to display the contents of the loaded data.
    - A save button to export the displayed data.
    It interacts with a `FileHandler` for file operations and the main application
    controller to access configuration and authentication details.

    Attributes:
        master (App): The root Tkinter application window.
        dataPreview (pd.DataFrame | None): Holds the loaded data for preview and saving.
        FH (FileHandler): An instance of the FileHandler for file-related operations.
        filePickerFrame (ctk.CTkFrame): Frame containing the data source selection UI.
        filePickerEntry (ctk.CTkEntry): Entry widget to display the selected file path.
        fileManipulationFrame (ctk.CTkFrame): Container for the viewer and action buttons.
        fileViewerFrame (ctk.CTkFrame): Frame to display the data table.
        automationExecuteFrame (ctk.CTkFrame): Frame containing the 'Save' button.
    """

    def __init__(self, master) -> None:
        super().__init__(
            master=master,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"],
            corner_radius=None,
        )
        self.master: "App" = master
        self.dataPreview = None
        self.FH = FileHandler()
        # Prefill initial directory from config if available
        try:
            self.FH.initDir = self.master.controller.config.paths.last_import_dir
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
            command=lambda: self._download_list(),
        ).pack()

        ### # From File # ###
        self.filePickerEntry = ctk.CTkEntry(
            master=dataPickerTab.tab("From File"),
            placeholder_text="Source File Directory ...",
        )
        self.filePickerEntry.pack(pady=10, padx=10, side="left", fill="x", expand=True)
        # Prefill last selected file path if available
        try:
            self.filePickerEntry.delete(0, ctk.END)
            self.filePickerEntry.insert(0, self.master.controller.config.paths.last_import_file)
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
        self.automationExecuteFrame = ctk.CTkFrame(master=self.fileManipulationFrame, fg_color="transparent")
        self.automationExecuteFrame.pack(fill="x", expand=False)
        ctk.CTkButton(
            master=self.automationExecuteFrame,
            text="Save",
            anchor="center",
            command=lambda: self._save_to_file(),
        ).pack(side="left")

    def pick_source_file(self):
        """Open a file picker, load preview data, and persist last path.

        Uses FileHandler to open a file dialog starting from the last used
        directory when available, reads the selected file into a DataFrame,
        updates the UI entry, and saves last_import_dir/file in config.
        """
        selected_file = self.FH.select_file()
        # If select_file returns the selected file, use it; otherwise, check sourceFile
        if selected_file is None or not Path(selected_file).exists():
            self.FH.sourceFile = None
            return
        self.FH.sourceFile = Path(selected_file)
        # Persist last import dir and file
        try:
            self.master.controller.config.setdefault("paths", {})["last_import_dir"] = str(self.FH.sourceFile.parent)
            self.master.controller.config.setdefault("paths", {})["last_import_file"] = str(self.FH.sourceFile)
            save_config(self.master.controller.config)
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

    def _download_list(self) -> None:
        download = SiteOfTenant(bearer_token=self.master.controller.auth.access_token)
        try:
            res = download.request()
            # print(res["data"]["items"])
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
        self.dataPreview = pd.DataFrame(data=[self.FH.flatten_dict(data=row, level=1) for row in res["data"]["items"]])
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

    def _save_to_file(self) -> None:
        if self.dataPreview is not None and not self.dataPreview.empty:
            # Start in last export dir if available
            dir_hint = None
            try:
                paths_cfg = (
                    self.master.controller.config.get("paths")
                    if isinstance(self.master.controller.config.get("paths"), dict)
                    else None
                )
                dir_hint = paths_cfg.get("last_export_dir") if paths_cfg else None
            except Exception:
                dir_hint = None
            self.FH.save_file_loc(dirStr=dir_hint or self.FH.destDir).export_excel(data=self.dataPreview)
            # Persist last export directory
            try:
                self.master.controller.config.setdefault("paths", {})["last_export_dir"] = str(self.FH.savedFile.parent)
                save_config(self.master.controller.config)
            except Exception:
                pass
        else:
            messagebox.showerror(title="Something Went Wrong!", message="No Data Selected!")
