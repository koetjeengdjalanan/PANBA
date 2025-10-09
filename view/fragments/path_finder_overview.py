"""PathFinderOverview: A CustomTkinter tabbed view for network path finding operations."""

from tkinter.ttk import Treeview

import customtkinter as ctk
import numpy
import pandas
from networkx import Graph

from helper.processing import find_slice, splice_ip


class PathFinderOverview(ctk.CTkTabview):
    """A CustomTkinter tabbed view widget for managing network path finding operations.

    This class provides a graphical interface for:
    - Viewing and editing input data (source, destination, port information)
    - Validating IP address ranges with visual feedback (normal/warning/critical states)
    - Processing network paths through a topology graph
    - Displaying output results in a tabular format

    The widget contains two tabs:
    1. "Memo Input": An editable table for input data with real-time validation
    2. "Config Output": A read-only table displaying processed path-finding results

    Attributes:
        input_data (pandas.DataFrame): The input data containing source, destination, and port information.
        segment_db (pandas.DataFrame): Database of network segments for zone mapping.
        topology_graph (Graph): Network topology graph used for path finding.
        widget_settings (dict[str, dict[str, str]]): Color schemes for different validation states.
        spliced_ip_cols (list[str]): Column names for spliced IP address ranges.
        tables_data (numpy.ndarray): Array of StringVar objects representing table cell data.
        widgets_data (numpy.ndarray): Array of CTkEntry widgets for the input table.
        problematic_rows (dict[str, ctk.StringVar]): Counters for warning and critical validation issues.
        output_data (pandas.DataFrame): Processed path-finding results.

    Args:
        master: Parent widget.
        input_data (pandas.DataFrame): Initial input data with network connection information.
        segment_db (pandas.DataFrame): Segment database for zone resolution.
        topology_graph (Graph): Network topology graph for path computation.
        **kwargs: Additional keyword arguments passed to CTkTabview.

    Methods:
        _count_problematic_rows: Counts rows with validation warnings and errors.
        _on_entry_edit: Callback handler for table cell edits with validation.
        _create_tables: Creates the input table interface with validation styling.
        _draw_output_table: Renders the output results table.
        process_finding_path: Main processing method that computes network paths.
    """

    input_data: pandas.DataFrame

    def __init__(
        self, master, input_data: pandas.DataFrame, segment_db: pandas.DataFrame, topology_graph: Graph, **kwargs
    ):
        super().__init__(master, border_width=1, **kwargs)
        self.master = master
        self.input_data = input_data
        self.segment_db = segment_db
        self.topology_graph = topology_graph
        self.widget_settings: dict[str, dict[str, str]] = {
            "normal": {
                "fg_color": ctk.ThemeManager.theme["CTkEntry"]["fg_color"],
                "border_color": ctk.ThemeManager.theme["CTkEntry"]["border_color"],
                "text_color": ctk.ThemeManager.theme["CTkEntry"]["text_color"],
            },
            "warn": {
                "fg_color": "orange",
                "border_color": "darkorange",
                "text_color": "white",
            },
            "crit": {
                "fg_color": "red",
                "border_color": "darkred",
                "text_color": "white",
            },
        }
        self.spliced_ip_cols: list[str] = ["src_start_ip", "src_end_ip", "dst_start_ip", "dst_end_ip"]

        self.add("Memo Input")
        self.add("Config Output")
        self.tables_data, self.widgets_data = self._create_tables()
        problem_count = self._count_problematic_rows()
        self.problematic_rows: dict[str, ctk.StringVar] = {
            "warn": ctk.StringVar(master=self, name="Warning Line", value=f"Warning: {problem_count[0]}"),
            "crit": ctk.StringVar(master=self, name="Critical Line", value=f"Critical: {problem_count[1]}"),
        }

    def _count_problematic_rows(self) -> tuple[int, int]:
        return (
            max(
                0,
                *[self.input_data.loc[self.input_data[col] == 0].__len__() for col in self.spliced_ip_cols],
            ),
            max(
                0,
                *[self.input_data.loc[self.input_data[col] < 0].__len__() for col in self.spliced_ip_cols],
            ),
        )

    def _on_entry_edit(self, var, index, mode):
        col_name: str = var.split("_")[0]
        col, row = map(int, var.split("_")[1:])
        vals = self.tables_data[row, col].get()
        self.input_data.iat[row, col] = vals
        if col_name.lower() != "port" and vals != "":
            split_cols = "src" if col_name.lower() == "source" else "dst"
            result = splice_ip(self.input_data.iloc[row], column=col_name).tolist()
            self.input_data.loc[row, [f"{split_cols}_start_ip", f"{split_cols}_end_ip"]] = result
            is_problematic: str = (
                "crit"
                if (self.input_data.iloc[row][self.spliced_ip_cols] < 0).any()
                else ("warn" if (self.input_data.iloc[row][self.spliced_ip_cols] == 0).any() else "normal")
            )
            for cols_idx in range(3):
                self.widgets_data[row, cols_idx].configure(**self.widget_settings[is_problematic])
        problem_count = self._count_problematic_rows()
        self.problematic_rows["warn"].set(f"Warning: {problem_count[0]}")
        self.problematic_rows["crit"].set(f"Critical: {problem_count[1]}")

    def _create_tables(self) -> tuple[numpy.ndarray, numpy.ndarray]:
        col_list = self.input_data.columns[:3].tolist()
        table_address = numpy.empty(shape=(len(self.input_data), len(col_list)), dtype=object)
        widget_address = numpy.empty(shape=(len(self.input_data), len(col_list)), dtype=object)
        table_headers = ctk.CTkFrame(master=self.tab("Memo Input"))
        table_headers.pack(fill="x", padx=5, pady=(5, 0))
        self.input_table_frame = ctk.CTkScrollableFrame(master=self.tab("Memo Input"))
        self.input_table_frame.pack(fill="both", expand=True, padx=5, pady=(2, 5))
        [
            [frame.grid_columnconfigure(i, weight=1) for i in range(len(col_list))]
            for frame in (table_headers, self.input_table_frame)
        ]
        for col_idx, value in enumerate(col_list):
            ctk.CTkLabel(master=table_headers, text=value).grid(row=0, column=col_idx, padx=0, pady=0)
        for idx, data in self.input_data.iterrows():
            is_problematic: str = (
                "crit"
                if (data[self.spliced_ip_cols] < 0).any()
                else ("warn" if (data[self.spliced_ip_cols] == 0).any() else "normal")
            )
            for col_idx, value in enumerate(col_list):
                table_address[idx, col_idx] = ctk.StringVar(
                    master=self,
                    value=str(data[value]),
                    name=f"{value}_{col_idx}_{idx}",
                )
                table_address[idx, col_idx].trace_add("write", lambda *args: self._on_entry_edit(*args))
                widget_address[idx, col_idx] = ctk.CTkEntry(
                    master=self.input_table_frame,
                    textvariable=table_address[idx, col_idx],
                    corner_radius=0,
                    border_width=0,
                    **self.widget_settings[is_problematic],
                )
                widget_address[idx, col_idx].grid(row=idx, column=col_idx, padx=1, pady=1, sticky=ctk.EW)
        return table_address, widget_address

    def _draw_output_table(self):
        if self.output_data.empty:
            return
        self._output_table = Treeview(
            master=self.tab("Config Output"),
            columns=list(self.output_data.columns),
            show="headings",
            selectmode="browse",
            name="path_finder_output_table",
        )
        self._output_table.pack(fill=ctk.BOTH, expand=True, side=ctk.LEFT, padx=(5, 0), pady=5)
        for col in self.output_data.columns:
            self._output_table.heading(col, text=col)
            self._output_table.column(col, width=100, anchor=ctk.W)
        for _, row in self.output_data.iterrows():
            self._output_table.insert("", "end", values=tuple(row))
        self._output_table.update_idletasks()
        v_scroll = ctk.CTkScrollbar(
            master=self.tab("Config Output"), orientation="vertical", command=self._output_table.yview
        )
        v_scroll.pack(side=ctk.RIGHT, fill=ctk.Y)
        self._output_table.configure(yscrollcommand=v_scroll.set)

    def process_finding_path(self):
        """
        Process and find network paths between source and destination zones using a topology graph.

        This method performs the following operations:
        1. Applies the find_slice function to extract memo_id, src_zone_str, and dst_zone_str from input data
        2. Iterates through each row of input data to find the shortest path between source and destination zones
        3. Uses NetworkX to compute shortest paths in the topology graph
        4. Constructs a list of network path dictionaries containing device, vsys, and zone information
        5. Yields progress updates during processing (current index, total length)
        6. Stores the results in output_data as a pandas DataFrame
        7. Draws the output table upon completion

        The method handles:
        - Rows with null source or destination zones (skips processing)
        - Removal of 'other.unconfigured.Core' from paths if present
        - NetworkX path-finding exceptions (NetworkXNoPath)
        - Zone string parsing and reconstruction

        Yields:
            tuple[int, int]: A tuple containing (current_index, total_length) to track progress

        Side Effects:
            - Modifies self.input_data by adding columns: memo_id, src_zone_str, dst_zone_str
            - Sets self.output_data with the processed results as a DataFrame
            - Calls self._draw_output_table() to render the results

        Output DataFrame Columns:
            - memo_id: Identifier from the input data
            - device: Network device name
            - vsys: Virtual system identifier
            - source_zone: Source zone name
            - source_IP(s): Source IP addresses
            - destination_zone: Destination zone name
            - destination_IP(s): Destination IP addresses
            - port(s): Port information
        """
        import networkx as nx

        self.input_data[["memo_id", "src_zone_str", "dst_zone_str"]] = self.input_data.apply(
            find_slice, axis=1, db=self.segment_db
        )
        res: list[dict] = []
        length = self.input_data.__len__()
        yield 0, length
        for idx, row in self.input_data.iterrows():
            nodes_path = {}
            if row[["src_zone_str", "dst_zone_str"]].isnull().any():
                yield idx, length
                continue
            try:
                paths = nx.shortest_path(
                    self.topology_graph,
                    source=row["src_zone_str"].rsplit(".", 1)[0] + ".zones",
                    target=row["dst_zone_str"].rsplit(".", 1)[0] + ".zones",
                )
                if "other.unconfigured.Core" in paths:
                    paths.remove("other.unconfigured.Core")
                for path in paths:
                    device, vsys, zone = path.split(".")
                    nodes_path.setdefault(vsys, [])
                    nodes_path[vsys].append({"device": device, "vsys": vsys, "zone": zone})
                nodes_path[next(iter(nodes_path))][0]["zone"] = row["src_zone_str"].split(".")[-1]
                nodes_path[next(reversed(nodes_path))][-1]["zone"] = row["dst_zone_str"].split(".")[-1]
                res.extend(
                    [
                        {
                            "memo_id": row["memo_id"],
                            "device": node[0].get("device", ""),
                            "vsys": node[0].get("vsys", ""),
                            "source_zone": node[0].get("zone", "") if len(node) > 0 else "",
                            "source_IP(s)": row["source"],
                            "destination_zone": node[-1].get("zone", "") if len(node) > 0 else "",
                            "destination_IP(s)": row["destination"],
                            "port(s)": row["port"],
                        }
                        for node in nodes_path.values()
                    ]
                )
            except nx.NetworkXNoPath as no_path:
                print(f"No path found for row {idx}: {no_path}")
            finally:
                yield idx, length
                continue
        self.output_data = pandas.DataFrame(res)
        yield length, length
        self._draw_output_table()
