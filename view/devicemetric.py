import customtkinter as ctk


class DeviceMetric(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, fg_color="transparent")

        ctk.CTkLabel(master=self, text="DeviceMetric").pack(expand=True, fill="both")
