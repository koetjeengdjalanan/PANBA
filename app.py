import os
import customtkinter as ctk
from pathlib import Path
from dotenv import load_dotenv
from helper.config import load_config

from layout.sidebar import SideBar
from view.accountncredentials import AccountNCredentials
from view.bandwidthconsumption import BandwidthConsumption
from view.bulkmetricreporting import BulkMetricReporting
from view.devicemetric import DeviceMetric
from view.siteconfiguration import SiteConfiguration
from assets.getfile import GetFile


class App(ctk.CTk):
    def __init__(self, start_size: tuple[int], env: dict = None):
        super().__init__()
        self.iconbitmap(GetFile.getAssets(file_name="favicon.ico"))
        self.title("Palo Alto Network Bulk Automation")
        self.geometry(f"{start_size[0]}x{start_size[1]}")
        self.resizable(False, False)

        # Preserve existing env behavior (from .env) and load persisted config
        # for defaults and user preferences.
        self.env = env if env is not None else None
        self.config = load_config()
        self.frames = {}
        self.authRes = None

        # Side Bar
        # FIXME: Other menu still accessible even in not a dev environment
        self.sideBar = SideBar(master=self, start_pos=0, end_pos=0.2)
        self.menuList = [
            ["Account & Credentials", AccountNCredentials, True],
            ["Site Configuration", SiteConfiguration, False],
            ["Device's Metric", DeviceMetric, False],
            ["Bulk Metric Reporting", BulkMetricReporting, False],
            ["Bandwidth Consumption", BandwidthConsumption, False],
        ]
        self.__draw_menu()

    def activate_menu(self) -> None:
        for child in self.sideBar.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(state=ctk.NORMAL)

    def __draw_menu(self):
        for menu in self.menuList:
            ctk.CTkButton(
                master=self.sideBar,
                text=menu[0],
                state=ctk.NORMAL if menu[2] else ctk.DISABLED,
                corner_radius=0,
                fg_color="transparent",
                text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"],
                command=lambda x=menu[1]: self.show_page(container=x),
            ).pack(fill=ctk.X, pady=1)
            frame = menu[1](master=self, controller=self)
            self.frames[menu[1]] = frame
            frame.place(relx=0.2, rely=0, relwidth=0.8, relheight=1)
        self.show_page(container=AccountNCredentials)

    def show_page(self, container):
        frame = self.frames[container]
        frame.tkraise()


def environment() -> dict | None:
    load_dotenv(dotenv_path="./.env")
    if Path("./.env").is_file():
        return {
            "dev": os.getenv("DEV"),
            "userName": os.getenv("USER_NAME"),
            "secret": os.getenv("SECRET_STRING"),
            "tsgId": os.getenv("TSG_ID"),
        }
    return None


app = App(start_size=(1190, 620), env=environment())
app.mainloop()
