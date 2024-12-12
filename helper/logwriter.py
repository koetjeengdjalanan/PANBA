import customtkinter
from pathlib import Path
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


def save_log_to_file(widget: customtkinter.CTkTextbox) -> None:
    logFile = open(Path("./PANBA.log"), "a")
    logFile.write(widget.get("0.0", "end"))
    logFile.write("\n--- Log saved at " + f"{dt.now():%d-%m-%Y %H:%M:%S}" + " ---\n\n")
    logFile.close()
