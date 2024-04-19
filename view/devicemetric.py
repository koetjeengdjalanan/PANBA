import functools
import customtkinter as ctk
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
            {"name": "MemoryUsage", "statistics": ["average"], "unit": "percentage"},
            {"name": "CPUUsage", "statistics": ["average"], "unit": "percentage"},
            {"name": "DiskUsage", "statistics": ["average"], "unit": "percentage"},
        ]
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
        ctk.CTkButton(
            master=self.graphWindow, text="Render", command=self.on_confirm
        ).grid(padx=10, pady=10, sticky=ctk.E, row=0)

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
            res = SysMetric(
                bearer_token=self.controller.authRes["data"]["access_token"],
                body=bodyJson,
            )
            print(res.request())
        # self.settingButton.destroy()
        # for child in self.graphWindow.winfo_children():
        #     child.destroy()
