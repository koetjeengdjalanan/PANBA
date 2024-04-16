import tkinter as tk
import customtkinter as ctk
from datetime import datetime as dt, timedelta


class DeviceMetric(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, fg_color="transparent")
        self.controller = controller
        self.today = dt.now()
        self.weekAgo = self.today - timedelta(days=7)

        ### data gather setting ###
        self.settingFrame = ctk.CTkFrame(master=self)
        self.settingFrame.pack(fill="x", anchor="n", padx=10, pady=10)
        ctk.CTkLabel(
            master=self.settingFrame,
            text=f"{self.weekAgo.isoformat()} - {self.today.isoformat()}",
        ).pack()

        ### # Date Range # ###
        # dateRangeFrame = ctk.CTkFrame(master=self.settingFrame)
        # dateRangeFrame.grid(sticky="w", row=0, column=0)
        # date_var = tk.IntVar(value=0)
        # hourlyRang =
