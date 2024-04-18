import tkinter as tk
import customtkinter as ctk
from datetime import datetime as dt, timedelta

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
        self.bind("<ConfirmSetting>", self.on_confirm())

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
        self.settingButton = ctk.CTkButton(
            master=self.graphWindow, text="Open Setting", command=self.open_var_setting
        ).pack(anchor=ctk.CENTER)

    def open_var_setting(self, event=None):
        if self.varSetting is None or not self.varSetting.winfo_exists():
            self.varSetting = MetricVariableSetting(
                master=self,
                # bearer_token="asdasdasd",
                bearer_token=self.controller.authRes["data"]["access_token"],
                # data=self.bodyVars,
            )
            self.varSetting.focus_force()
            self.varSettingData = self.varSetting.var_setting
        else:
            self.varSetting.focus()

    def on_confirm(self):
        if self.varSetting is None or not self.varSetting.winfo_exists():
            self.bodyVars = {}
        else:
            self.bodyVars = self.varSetting.bodyVars
        print(self.bodyVars)
        # self.settingButton.destroy()
        # for child in self.graphWindow.winfo_children():
        #     child.destroy()
