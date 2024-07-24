import os
import customtkinter as ctk
from pathlib import Path
from dotenv import load_dotenv

from layout.sidebar import SideBar
from view.accountncredentials import AccountNCredentials
from view.bulkmetricreporting import BulkMetricReporting
from view.devicehealth import DeviceHealth
from view.devicemetric import DeviceMetric
from view.siteconfiguration import SiteConfiguration
from assets.getfile import GetFile


class App(ctk.CTk):
    def __init__(self, start_size: tuple[int], env: dict = None):
        super().__init__()
        favicon = GetFile.getAssets(file_name="favicon.ico")
        self.iconbitmap(favicon)
        self.title("Palo Alto Network Bulk Automation")
        self.geometry(f"{start_size[0]}x{start_size[1]}")
        self.resizable(False, False)
        self.env = env if not None else None
        self.frames = {}
        self.authRes = None

        ### Side Bar ###
        # FIXME: Other menu still accessible even in not a dev environment
        sideBar = SideBar(master=self, start_pos=0, end_pos=0.2)
        menu_list = [
            ["Account & Credentials", AccountNCredentials],
            ["Site Configuration", SiteConfiguration],
            ["Device's Metric", DeviceMetric],
            ["Bulk Metric Reporting", BulkMetricReporting],
            ["Device's Health", DeviceHealth],
        ]
        for menu in menu_list:
            ctk.CTkButton(
                master=sideBar,
                text=menu[0],
                corner_radius=0,
                bg_color="transparent",
                fg_color="transparent",
                command=lambda x=menu[1]: self.show_page(container=x),
            ).pack(fill="x", pady=1)
            frame = menu[1](master=self, controller=self)
            self.frames[menu[1]] = frame
            frame.place(relx=0.2, rely=0, relwidth=0.8, relheight=1)

        self.show_page(container=AccountNCredentials)
        # self.show_page(container=DeviceMetric)

    def show_page(self, container):
        frame = self.frames[container]
        frame.tkraise()


def environment() -> dict | None:
    load_dotenv(dotenv_path="./.env")
    if Path("./.env").is_file():
        return {
            "userName": os.getenv("USER_NAME"),
            "secret": os.getenv("SECRET_STRING"),
            "tsgId": os.getenv("TSG_ID"),
        }
    return None


app = App(start_size=(1190, 620), env=environment())
app.mainloop()
