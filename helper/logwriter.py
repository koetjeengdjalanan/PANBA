import customtkinter
from datetime import datetime as dt


def text_view_render(widget: customtkinter.CTkTextbox, log: str) -> None:
    """Render log to the textbox

    Args:
        widget (customtkinter.CTkTextbox): CustomTKinter textbox widget
        log (str): Log message in string
    """
    widget.configure(state="normal")
    widget.insert(customtkinter.END, f"[ {dt.now():%d-%m-%Y %H:%M:%S} ] {log}\n")
    widget.configure(state="disabled")
    widget.see(customtkinter.END)
