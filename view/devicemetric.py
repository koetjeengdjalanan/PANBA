import tkinter as tk
import customtkinter as ctk
from datetime import datetime as dt, timedelta

from view.toplevel.metricvariablesetting import MetricVariableSetting


class DeviceMetric(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, fg_color="transparent")
        self.controller = controller
        self.varSetting = None
        self.today = dt.now()
        self.weekAgo = self.today - timedelta(days=7)
        self.intervalList = [
            "hour",
            "day",
            "week",
        ]
        self.varSettingData = None

        ### Interval Overview ###
        self.settingFrame = ctk.CTkFrame(master=self)
        self.settingFrame.pack(fill="x", anchor="n", padx=10, pady=10)
        overview = ctk.CTkLabel(
            master=self.settingFrame,
            text=f"{self.weekAgo.isoformat()} - {self.today.isoformat()} | Daily",
        )
        overview.pack()
        overview.bind(sequence="<Button-1>", command=self.open_var_setting)

        ### Graph Window ###
        graphWindow = ctk.CTkFrame(master=self)
        graphWindow.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        ctk.CTkButton(
            master=graphWindow, text="Open Setting", command=self.open_var_setting
        ).pack(anchor=ctk.CENTER)

    def open_var_setting(self, event=None):
        if self.varSetting is None or not self.varSetting.winfo_exists():
            self.varSetting = MetricVariableSetting(
                master=self,
                bearer_token=self.controller.authRes["data"]["access_token"],
            )
            self.varSetting.focus_force()
            self.varSettingData = self.varSetting.var_setting
        else:
            self.varSetting.focus()
