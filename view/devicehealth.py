import customtkinter as ctk


class DeviceHealth(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, fg_color="transparent")

        ctk.CTkLabel(master=self, text="DeviceHealth").pack()
