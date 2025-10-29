"""Shortest Path Finder for Network Graph."""

import threading
from pathlib import Path
from tkinter import Event, Menu, filedialog, messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk
import networkx
import pandas

from helper.processing import load_topology, splice_ip
from view.fragments.loading_overlay import load_overlay
from view.fragments.path_finder_overview import PathFinderOverview
from view.toplevel.topology_preview import create_graph_preview

if TYPE_CHECKING:
    from dotenv.main import StrPath

    from main import App


class PathFinder(ctk.CTkFrame):
    """
    A GUI frame for pathfinding operations in network topology analysis.

    This class provides a user interface for loading network topology data, segment databases,
    and processing network path analysis from memo files. It handles file selection, data loading,
    visualization, and path computation operations.

    Attributes:
        topology (networkx.Graph): The network topology graph representing firewall and network relationships.
        segment_db (pandas.DataFrame): Database containing segment information including firewall, VSys, zone, and IP ranges.
        _raw_memo_data (pandas.DataFrame): Raw data loaded from memo files containing path requests.
        _padding (dict[str, tuple[int, int]]): Padding configuration for UI elements.
        master (App): Reference to the parent application instance.
        setting_container (ctk.CTkFrame): Container frame for source file configuration widgets.
        topology_source_file (ctk.StringVar): Path to the topology JSON file.
        segment_db_source_file (ctk.StringVar): Path to the segment database CSV/Excel file.
        finder_overview (PathFinderOverview): Widget displaying the overview of pathfinding results.
        submit_button (ctk.CTkButton): Button to trigger path finding operations.

    The PathFinder interface is divided into three main sections:
        1. Source Files Configuration - For loading topology and segment database files
        2. Memo Input - For loading memo files containing path analysis requests
        3. Instructions Table - Displays results and status of path analysis operations

    Methods handle file loading, data validation, topology visualization, and asynchronous
    path computation with progress tracking.
    """  # noqa: E501

    topology: networkx.Graph = networkx.Graph()
    segment_db: pandas.DataFrame = pandas.DataFrame()
    _raw_memo_data: pandas.DataFrame = pandas.DataFrame()
    _padding: dict[str, tuple[int, int]] = {
        "pad_x": (10, 10),
        "pad_y": (10, 0),
    }

    def __init__(self, master: "App"):  # type: ignore[name-defined]
        super().__init__(master=master, fg_color="transparent")
        self.master: "App" = master  # type: ignore[name-defined]
        self._preview_topology_frame: ctk.CTkToplevel | None = None
        self.is_concurrent: bool = False

        self._source_file_frame()
        self._command_frame()

    def _source_file_frame(self) -> None:
        self.setting_container = ctk.CTkFrame(master=self)
        self.setting_container.pack(fill=ctk.X, anchor=ctk.NE, padx=self._padding["pad_x"], pady=self._padding["pad_y"])
        self.setting_container.columnconfigure(index=0, weight=1)
        self.setting_container.columnconfigure(index=1, weight=4)
        ctk.CTkLabel(
            master=self.setting_container,
            text="Source Files Configuration",
            font=("Arial", 12, "bold"),
            anchor="center",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=self._padding["pad_x"], pady=self._padding["pad_y"])

        ## Topology Source File
        self.topology_source_file = ctk.StringVar(
            master=self,
            name="topology_source_file",
            value=str(self.master.controller.config.paths.last_import_topology_file),
        )
        ctk.CTkLabel(master=self.setting_container, text="Topology Source File:").grid(
            row=1, column=0, sticky="w", padx=self._padding["pad_x"], pady=self._padding["pad_y"]
        )
        self._topology_entry = ctk.CTkEntry(
            master=self.setting_container,
            textvariable=self.topology_source_file,
            state="readonly",
        )
        self._topology_entry.xview_moveto(1)
        self._topology_entry.grid(
            row=1, column=1, sticky="ew", padx=self._padding["pad_x"], pady=self._padding["pad_y"]
        )
        self._topology_entry.bind(
            "<Button-1>",
            lambda e: self._file_select(
                widget=self._topology_entry,
                str_var=self.topology_source_file,
                expected=[("JSON files", "*.json")],
            ),
        )
        self.debug_mode = ctk.BooleanVar(
            master=self, name="path_finder_debug_mode", value=bool(self.master.controller.env.dev)
        )

        ## Segment DB Source File
        self.segment_db_source_file = ctk.StringVar(
            master=self,
            name="segment_db_source_file",
            value=str(self.master.controller.config.paths.last_import_segment_db_file),
        )
        ctk.CTkLabel(master=self.setting_container, text="Segment DB Source File:").grid(
            row=2, column=0, sticky="w", padx=self._padding["pad_x"], pady=self._padding["pad_y"]
        )
        self._segment_entry = ctk.CTkEntry(
            master=self.setting_container,
            textvariable=self.segment_db_source_file,
            state="readonly",
        )
        self._segment_entry.xview_moveto(1)
        self._segment_entry.grid(row=2, column=1, sticky="ew", padx=self._padding["pad_x"], pady=self._padding["pad_y"])
        self._segment_entry.bind(
            "<Button-1>",
            lambda e: self._file_select(
                widget=self._segment_entry,
                str_var=self.segment_db_source_file,
                expected=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
            ),
        )

        ## Action Button
        self._action_popup = Menu(
            master=self,
            tearoff=False,
            bg=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1],
            fg=ctk.ThemeManager.theme["CTkLabel"]["text_color"][1],
            bd=0,
            borderwidth=0,
        )
        self._action_popup.add_command(
            label="PreView Topology",
            command=lambda: setattr(self, "_temporary_topology_file", create_graph_preview(graph=self.topology)[1]),
        )
        self._action_popup.add_command(label="Save Topology as...", command=self._save_topology_as)
        self._preview_button = ctk.CTkButton(master=self.setting_container, text="Load Topology", command=lambda: None)
        self._preview_button.grid(row=3, column=0, columnspan=2, pady=(10, 10))
        self._preview_button.bind("<Button-1>", self._preview_topology)
        self._preview_button.bind("<Button-3>", self._preview_topology)

    def _preview_topology(self, event: Event) -> None:
        match event.num:
            case 1:
                self._reload_sources()
            case 3:
                try:
                    self._action_popup.tk_popup(x=event.x_root, y=event.y_root)
                finally:
                    self._action_popup.grab_release()

    def _load_source_files(self, file_path: "StrPath") -> bool:
        from time import sleep

        def load_segment_db(csv_source: Path) -> None:
            df = pandas.read_csv(csv_source)
            expected_columns = {"Firewall1", "VSys", "Zone", "Segment"}
            if not expected_columns.issubset(set(df.columns)):
                raise ValueError(f"CSV file must contain columns: {expected_columns}")
            df[["start_ip", "end_ip"]] = df.apply(splice_ip, axis=1)
            self.segment_db = df

        def make_graph(file_path: Path) -> None:
            self.topology = load_topology(file_path=file_path)
            self.topology.name = f"PANBA_{file_path.stem}".replace(" ", "_")

        self.master.controller.config.paths.last_import_dir = str(Path(file_path).parent)
        with load_overlay(master=self.setting_container) as ov:
            source = Path(file_path)
            match source.suffix.lower():
                case ".json":
                    self.master.controller.config.paths.last_import_topology_file = source
                    ov.update_text(text="Reading Topology Rules...")
                    ov.pulse()
                    calls = make_graph
                case ".csv" | ".xlsx":
                    self.master.controller.config.paths.last_import_segment_db_file = source
                    ov.update_text(text="Reading Segment DB...")
                    ov.pulse()
                    calls = load_segment_db
                case _:
                    ov.text_value = "Unsupported file type!"
                    return False

            if not self.is_concurrent:
                thread = threading.Thread(target=calls, args=(source,), name="load_data_thread")
                thread.start()
                while thread.is_alive():
                    self.master.update()
                    ov.pulse()
                    sleep(0.1)
                thread.join()
                self.is_concurrent = False
            else:
                calls(source)
        return True

    def _file_select(
        self, widget: ctk.CTkEntry, str_var: ctk.StringVar, expected: list[tuple[str, str]], skip_ui: bool = False
    ) -> str | None:
        file_path = (
            str_var.get()
            if skip_ui
            else filedialog.askopenfilename(
                title="Select file!",
                filetypes=expected + [("All files", "*.*")],
                parent=self.master,
                initialdir=self.master.controller.config.paths.last_import_dir,
            )
        )
        if file_path:
            if self._load_source_files(file_path=file_path):
                str_var.set(file_path)
                widget.configure(state="normal")
                widget.xview_moveto(1)
            else:
                if messagebox.askretrycancel(
                    title="Error",
                    message="Failed to load the selected file. Do you want to retry?",
                    parent=self.master,
                ):
                    self._file_select(widget, str_var, expected)
        return file_path

    def _reload_sources(self) -> None:
        files: list[str] = []
        if self.segment_db.empty:
            sgmt_file = self._file_select(
                widget=self._segment_entry,
                str_var=self.segment_db_source_file,
                expected=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
                skip_ui=True,
            )
            if sgmt_file:
                files.append(sgmt_file)
        if self.topology.number_of_nodes() == 0:
            topo_file = self._file_select(
                widget=self._topology_entry,
                str_var=self.topology_source_file,
                expected=[("JSON files", "*.json")],
                skip_ui=True,
            )
            if topo_file:
                files.append(topo_file)
        if len(files) >= 2:
            self._memo_entry.bind("<Button-1>", lambda e: self._read_memo_entry(e))
            self._reload_memo_button.configure(state=ctk.NORMAL)

    def _save_topology_as(self) -> None:
        from shutil import copyfile

        with load_overlay(master=self) as ov:
            ov.update_text(text="Saving Topology Preview File...")
            ov.pulse()
            self.master.update()
            ov.pulse()
            if getattr(self, "_temporary_topology_file", None) is None:
                messagebox.showwarning(
                    title="No Topology",
                    message="No topology preview available to save. Please preview a topology first.",
                    parent=self.master,
                )
                return
            target_file = Path(
                filedialog.asksaveasfilename(
                    title="Save Topology As...",
                    defaultextension=".json",
                    filetypes=[("HTML File", "*.html")],
                    confirmoverwrite=True,
                    parent=self.master,
                    initialdir=self.master.controller.config.paths.last_export_dir,
                    initialfile=f"rendered_{self.topology.name.replace(' ', '_')}.html",
                )
            )
            if target_file:
                try:
                    copyfile(src=self._temporary_topology_file, dst=target_file)
                except Exception as e:
                    messagebox.showerror(
                        title="Error",
                        message="Failed to save the topology file:!",
                        detail=str(e),
                        parent=self.master,
                    )

    def _command_frame(self) -> None:
        self._command_frame_container = ctk.CTkFrame(master=self)
        self._command_frame_container.pack(
            fill=ctk.BOTH, expand=True, anchor=ctk.SE, padx=self._padding["pad_x"], pady=(10, 10)
        )
        self._command_frame_container.rowconfigure(index=0, weight=1)
        self._command_frame_container.rowconfigure(index=1, weight=4)
        self._command_frame_container.rowconfigure(index=2, weight=1)
        self._command_frame_container.columnconfigure(index=0, weight=1)

        ## Commands Table Input Frame
        commands_table_input_frame = ctk.CTkFrame(master=self._command_frame_container, fg_color="transparent")
        commands_table_input_frame.grid(row=0, column=0, sticky=ctk.EW)
        commands_table_input_frame.columnconfigure(index=0, weight=1)
        commands_table_input_frame.columnconfigure(index=1, weight=4)
        commands_table_input_frame.columnconfigure(index=2, weight=1)
        ctk.CTkLabel(
            master=commands_table_input_frame,
            text="Memo Input:",
        ).grid(row=0, column=0, padx=self._padding["pad_x"])
        self._memo_path = ctk.StringVar(master=self, name="memo_path", value="")
        self._memo_entry = ctk.CTkEntry(
            master=commands_table_input_frame,
            textvariable=self._memo_path,
            state="readonly",
        )
        self._memo_entry.xview_moveto(1)
        self._memo_entry.grid(row=0, column=1, sticky="ew", padx=self._padding["pad_x"])
        self._reload_memo_button = ctk.CTkButton(
            master=commands_table_input_frame,
            text="ReLoad Memo",
            command=lambda e: self._read_memo_entry(skip_ui=True),
            state=ctk.DISABLED,
        )
        self._reload_memo_button.grid(row=0, column=2, padx=self._padding["pad_x"])

        ## Instructions Table Input-Output Frame
        self._instructions_table_frame = ctk.CTkFrame(master=self._command_frame_container, fg_color="transparent")
        self._instructions_table_frame.grid(row=1, column=0, sticky=ctk.NSEW)
        ctk.CTkLabel(master=self._instructions_table_frame, text="Instructions Table").pack(
            anchor=ctk.CENTER, fill=ctk.BOTH, expand=True
        )

        ## Action Button Cluster
        self._action_button_cluster_frame = ctk.CTkFrame(master=self._command_frame_container, fg_color="transparent")
        self._action_button_cluster_frame.grid(row=2, column=0, sticky=ctk.EW)
        self._action_button_cluster_frame.columnconfigure(index=0, weight=1)
        self._action_button_cluster_frame.columnconfigure(index=1, weight=1)
        self._action_button_cluster_frame.columnconfigure(index=2, weight=1)
        self._step_button_var = ctk.StringVar(master=self, name="step_button_var", value="Next...")
        self._command_popup = Menu(
            master=self,
            tearoff=False,
            bg=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1],
            fg=ctk.ThemeManager.theme["CTkLabel"]["text_color"][1],
            bd=0,
            borderwidth=0,
        )
        self._submit_button = ctk.CTkButton(
            master=self._action_button_cluster_frame,
            textvariable=self._step_button_var,
            command=self._do_a_breakpoint,
        )
        self._submit_button.grid(row=0, column=2, padx=self._padding["pad_x"], sticky=ctk.EW)
        self._submit_button.bind("<Button-3>", self._memo_right_click_menu)

    def _memo_right_click_menu(self, event: Event) -> None:
        if event.num != 3:
            return
        if len(self._command_popup.entryconfigure(0)) == 0:
            self._command_popup.add_command(label="Re-Find Path", command=self._find_path)
            return
        else:
            try:
                self._command_popup.tk_popup(x=event.x_root, y=event.y_root)
            finally:
                self._command_popup.grab_release()

    def _read_memo_entry(self, *args, **kwargs) -> None:
        def process_memo_entry():
            match Path(self._memo_path.get()).suffix.lower():
                case ".xlsx":
                    self._raw_memo_data = pandas.read_excel(self._memo_path.get())
                case ".csv":
                    self._raw_memo_data = pandas.read_csv(self._memo_path.get())
            ov.pulse()
            self._raw_memo_data[["src_start_ip", "src_end_ip"]] = self._raw_memo_data.apply(
                splice_ip, axis=1, column="source"
            )
            self._raw_memo_data[["dst_start_ip", "dst_end_ip"]] = self._raw_memo_data.apply(
                splice_ip, axis=1, column="destination"
            )
            for child in self._instructions_table_frame.winfo_children():
                child.destroy()
            ov.pulse()
            self.finder_overview = PathFinderOverview(
                master=self._instructions_table_frame,
                input_data=self._raw_memo_data,
                segment_db=self.segment_db,
                topology_graph=self.topology,
            )
            self.finder_overview.pack(fill="both", expand=True, padx=10, pady=5)
            self._step_button_var.set("Find Path")
            self._submit_button.configure(command=self._find_path)
            self._submit_button.bind("<Button-3>", self._memo_right_click_menu)
            for idx, val in enumerate(self.finder_overview.problematic_rows.items()):
                _ = ctk.CTkFrame(
                    master=self._action_button_cluster_frame,
                    border_width=2,
                    border_color=self.finder_overview.widget_settings[val[0]]["border_color"],
                )
                _.grid(row=0, column=idx, padx=self._padding["pad_x"], sticky=ctk.EW)
                ctk.CTkLabel(
                    master=_,
                    textvariable=val[1],
                    text_color=self.finder_overview.widget_settings[val[0]]["fg_color"],
                ).pack(anchor=ctk.CENTER, fill=ctk.BOTH, expand=True)

        if not kwargs.get("skip_ui", False):
            self._memo_path.set(
                filedialog.askopenfilename(
                    title="Select Memo File",
                    filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
                    parent=self.master,
                    initialdir=self.master.controller.config.paths.last_import_dir,
                )
            )

        if self._memo_path.get() is None or self._memo_path.get() == "":
            return

        self.master.controller.config.paths.last_import_dir = str(Path(self._memo_path.get()).parent)
        with load_overlay(master=self._command_frame_container) as ov:
            ov.update_text("Loading Memo...")
            thread = threading.Thread(target=process_memo_entry, name="load_memo_thread")
            thread.start()
            while thread.is_alive():
                self.master.update()
                ov.pulse()
            else:
                thread.join()

    def _find_path(self) -> None:
        from queue import Queue

        self.is_concurrent = True
        self._submit_button.configure(state=ctk.DISABLED)
        self._reload_sources()
        progress_queue = Queue()

        def process_with_progress():
            for current, total in self.finder_overview.process_finding_path():
                progress_queue.put((current, total))
            progress_queue.put(None)  # Signal completion

        # Manually manage the overlay context for async operation
        ov = load_overlay(master=self._command_frame_container).__enter__()
        ov.update_text("Finding Paths...")

        def check_progress():
            try:
                progress = progress_queue.get_nowait()
                if progress is None:
                    # Thread completed
                    ov.__exit__(None, None, None)
                    self.is_concurrent = False
                    self._step_button_var.set("Export Results")
                    self._submit_button.configure(command=self._export_results, state=ctk.NORMAL)
                    return
                current, total = progress
                ov.update_text(f"Finding Paths... ({current}/{total})")
                ov.pulse()
            except Exception:
                pass

            # Schedule next check (non-blocking)
            self.master.after(50, check_progress)

        thread = threading.Thread(target=process_with_progress, name="find_path_thread", daemon=True)
        thread.start()

        # Start polling the queue asynchronously
        self.master.after(50, check_progress)

    def _export_results(self) -> None:
        from helper.ext_filehandler import status_coloring_fmt
        from helper.filehandler import FileHandler as FH

        if any(
            [
                not hasattr(self.finder_overview, "output_data"),
                any([df.empty for df in self.finder_overview.output_data.values()]),
            ]
        ):
            messagebox.showwarning(
                title="No Results",
                message="No results available to export. Please perform a pathfinding operation first.",
                parent=self.master,
            )
            return
        if self.master.controller.env.dev:
            self.finder_overview.output_data["debug_output"] = self.finder_overview.input_data
        fh = (
            FH(destDir=self.master.controller.config.paths.last_export_dir)
            .save_file_loc(fileName="Path_Results.xlsx", dirStr=self.master.controller.config.paths.last_export_dir)
            .export_excel(data=self.finder_overview.output_data, additional_fmt=status_coloring_fmt)
            .open_explorer()
        )
        self.master.controller.config.paths.last_export_dir = fh.destDir
        self._do_a_breakpoint()

    def _do_a_breakpoint(self) -> None:
        print("Breakpoint reached!")
