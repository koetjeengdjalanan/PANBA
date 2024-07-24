import functools
import customtkinter as ctk
import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime as dt, timedelta

from helper.api.monitor import SysMetric
from view.toplevel.metricvariablesetting import MetricVariableSetting


class DeviceMetric(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, fg_color="transparent")
        self.controller = controller
        self.varSetting = None
        self.toDate = dt.now()
        self.fromDate = self.toDate - timedelta(days=7)
        self.intervalList = [
            "hour",
            "day",
            "week",
        ]
        self.varSettingData = None
        self.bodyVars = {}
        self.metrics = [
            {"name": "CPUUsage", "statistics": ["average"], "unit": "percentage"},
            {"name": "MemoryUsage", "statistics": ["average"], "unit": "percentage"},
            {"name": "DiskUsage", "statistics": ["average"], "unit": "percentage"},
            {
                "name": "InterfaceBandwidthUsage",
                "statistics": ["average"],
                "unit": "Mbps",
            },
        ]
        self.plot = []
        # self.bind("<<ConfirmSetting>>", lambda: self.on_confirm())

        ### Interval Overview ###
        self.settingFrame = ctk.CTkFrame(master=self)
        self.settingFrame.pack(fill="x", anchor="n", padx=10, pady=10)
        overview = ctk.CTkLabel(
            master=self.settingFrame,
            text=f"{self.fromDate.isoformat()} - {self.toDate.isoformat()} | Daily",
        )
        overview.pack()
        overview.bind(sequence="<Button-1>", command=self.open_var_setting)

        ### Graph Window ###
        self.graphWindow = ctk.CTkScrollableFrame(master=self)
        self.graphWindow.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # self.settingButton = ctk.CTkButton(
        #     master=self.graphWindow, text="Open Setting", command=self.open_var_setting
        # ).pack(anchor=ctk.CENTER)
        self.graphWindow.columnconfigure(0, weight=1)
        ctk.CTkButton(
            master=self.graphWindow, text="Render", command=self.on_confirm
        ).grid(padx=10, pady=(10, 15), sticky=ctk.E, row=0)

    def open_var_setting(self, event=None):
        if self.varSetting is None or not self.varSetting.winfo_exists():
            self.varSetting = MetricVariableSetting(
                master=self,
                controller=self,
                # bearer_token=self.controller.authRes["data"]["access_token"],
                # data=self.bodyVars,
            )
            self.varSetting.grab_set()
            # self.varSettingData = self.varSetting.bodyVars
            # print("Binding on_confirm to WM_DELETE_WINDOW")
            self.varSetting.protocol(
                "WM_DELETE_WINDOW", functools.partial(self.on_confirm)
            )
        else:
            self.varSetting.focus()

    def on_confirm(self):
        for element in self.bodyVars["selected"]:
            bodyJson = self.bodyVars["globalVars"]
            bodyJson["metrics"] = self.metrics
            bodyJson["filter"] = {"site": [element[0]], "element": [element[1]]}
            SM = SysMetric(
                bearer_token=self.controller.authRes["data"]["access_token"],
                body=bodyJson,
            )
            res = SM.request()
            self.render_canvas(data=res["data"]["metrics"], title=element[2])

    def render_canvas(
        self,
        data: list,
        title: str = "Uname Plot",
    ) -> None:
        # FIXME: Render Canvas is still on previous iteration
        fig, axs = plt.subplots(
            nrows=len(data),
            ncols=1,
            sharex=True,
            figsize=(10, 6),
        )
        fig.suptitle(title)
        plt.tight_layout()
        plt.figure(figsize=(9, 6))
        # plt.style.use("bmh")
        graphIterate: int = 0
        for graph in data:
            _ = graph["series"][0]
            df = pd.DataFrame(data=_["data"][0]["datapoints"])
            df["time"] = pd.to_datetime(df["time"])
            axs[graphIterate].set_title(_["name"])
            axs[graphIterate].set_ylabel(_["unit"])
            axs[graphIterate].plot_date(df["time"], df["value"], linestyle="solid")
            axs[graphIterate].xaxis.set_minor_locator(AutoMinorLocator())
            axs[graphIterate].tick_params(axis="x", rotation=270)
            # x_left, x_right = axs[graphIterate].get_xlim()
            # y_low, y_high = axs[graphIterate].get_ylim()
            # axs[graphIterate].set_aspect(
            #     abs((x_right - x_left) / (y_low - y_high)) * 0.5
            # )
            graphIterate += 1
        # axs[-1].xaxis.set_major_locator(plt.MaxNLocator(2))
        # plt.subplots_adjust(hspace=0.35)
        canvas = FigureCanvasTkAgg(figure=fig, master=self.graphWindow)
        widget = canvas.get_tk_widget()
        widget.grid(column=0, padx=10, pady=5, sticky=ctk.EW)
        canvas.draw()

    # def to_dataframe (data: dict) -> pd.DataFrame:
