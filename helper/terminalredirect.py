import customtkinter as ctk


class StdOutTerminalRedirect:
    def __init__(self, widget):
        self.widget = widget

    def write(self, string: str):
        self.widget.insert(ctk.END, string)
        self.widget.see(ctk.END)


class StdErrTerminalRedirect:
    def __init__(self, widget):
        self.widget = widget

    def write(self, string: str):
        self.widget.insert(ctk.END, string, "Error")
        self.widget.see(ctk.END)
