import os
import customtkinter as ctk
from dotenv import load_dotenv
from helper.config import load_config

from layout.sidebar import SideBar
from models import AppController, EnvironmentVariables, ViewsMenuItem
from view.accountncredentials import AccountNCredentials
from view.bandwidthconsumption import BandwidthConsumption
from view.bulkmetricreporting import BulkMetricReporting
from view.devicemetric import DeviceMetric
from view.siteconfiguration import SiteConfiguration
from assets.getfile import GetFile


class App(ctk.CTk):
    """
    App(ctk.CTk) – Main application window for Palo Alto Network Bulk Automation.
    Initializes the custom Tkinter window, loads environment and persisted configuration,
    and constructs a sidebar navigation menu with corresponding view frames.
        start_size (tuple[int, int]): Initial window dimensions as (width, height).
        env (EnvironmentVariables): Environment flags and variables (e.g., dev mode).
    Attributes:
        controller (AppController):
            Coordinates application logic, holds environment settings, configuration and auth.
        frames (dict[str, ctk.CTkFrame]):
            Maps view names to their frame instances for dynamic page display.
        sideBar (SideBar):
            The container widget holding sidebar navigation buttons.
        menuList (list[ViewsMenuItem]):
            Definitions of available views, including name, view class, activity and deprecation flags.
    Methods:
        activate_menu():
            Enable or disable sidebar buttons based on deprecation status and dev mode.
        __draw_menu():
            Create sidebar buttons for each menu item, instantiate corresponding frames,
            and place them within the main window.
        show_page(container: str, active: int):
            Raise the specified frame to the front and highlight the active sidebar button.
    """

    def __init__(self, start_size: tuple[int], env: EnvironmentVariables):
        super().__init__()
        self.iconbitmap(GetFile.getAssets(file_name="favicon.ico"))
        self.title("Palo Alto Network Bulk Automation")
        self.geometry(f"{start_size[0]}x{start_size[1]}")
        self.resizable(False, False)

        # for defaults and user preferences.
        self.controller: AppController = AppController(
            env=env,
            config=load_config(),
            auth=None,
        )
        self.frames: dict[str, ctk.CTkFrame] = {}

        # Side Bar
        self.sideBar = SideBar(master=self, start_pos=0, end_pos=0.2)
        self.menuList: list[ViewsMenuItem] = [
            ViewsMenuItem(
                name="Account & Credentials",
                view_class=AccountNCredentials,
                is_active=True,
            ),
            ViewsMenuItem(
                name="Site Configuration",
                view_class=SiteConfiguration,
                is_deprecated=True,
            ),
            ViewsMenuItem(
                name="Device's Metric",
                view_class=DeviceMetric,
                is_deprecated=True,
            ),
            ViewsMenuItem(
                name="Bulk Metric Reporting",
                view_class=BulkMetricReporting,
            ),
            ViewsMenuItem(
                name="Bandwidth Consumption",
                view_class=BandwidthConsumption,
            ),
        ]
        self.__draw_menu()

    def activate_menu(self) -> None:
        """
        Activate sidebar menu buttons based on deprecation status.

        This method iterates through all CTkButton children of the `self.sideBar`
        container and updates each button's state:
        - Sets to NORMAL if the corresponding entry in `self.menuList` is not deprecated.
        - Sets to DISABLED if the corresponding entry in `self.menuList` is deprecated.

        No return value.
        """
        side_bar_child: list[ctk.CTkButton] = [
            child
            for child in self.sideBar.winfo_children()
            if isinstance(child, ctk.CTkButton)
        ]
        for index, child in enumerate(side_bar_child):
            child.configure(
                state=(
                    ctk.NORMAL
                    if not self.menuList[index].is_deprecated
                    else ctk.DISABLED
                )
            )

    def __draw_menu(self) -> None:
        """
        Draws the application side menu by creating menu buttons and corresponding frames.

        Iterates over self.menuList to:
        - Create a CTkButton for each menu item in the sidebar.
            - Enables the button only if menu.is_active and self.controller.env.dev are True.
            - Sets the command to call self.show_page with the menu's name and index.
        - Instantiate the menu's view_class, store it in self.frames under the menu's name,
            and place it in the main area (80% width, starting at 20%).
        After building all buttons and frames, displays the first frame by invoking
        self.show_page with the first key in self.frames and index 0.

        Returns:
            None
        """
        for idx, menu in enumerate(self.menuList):
            ctk.CTkButton(
                master=self.sideBar,
                text=menu.name,
                state=(
                    ctk.NORMAL
                    if menu.is_active or self.controller.env.dev
                    else ctk.DISABLED
                ),
                corner_radius=0,
                fg_color="transparent",
                text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"],
                command=lambda x=(menu.name, idx): self.show_page(
                    container=x[0], active=x[1]
                ),
            ).pack(fill=ctk.X, pady=1)
            frame = menu.view_class(master=self, controller=self.controller)
            self.frames[menu.name] = frame
            frame.place(relx=0.2, rely=0, relwidth=0.8, relheight=1)
        self.show_page(container=next(iter(self.frames)), active=0)

    def show_page(self, container: str, active: int) -> None:
        """
        Display the specified page frame and highlight the corresponding sidebar button.

        Args:
            container (str): Key identifying which frame in self.frames to show.
            active (int): Index of the sidebar button to mark as active.

        Returns:
            None
        """
        frame = self.frames[container]
        frame.tkraise()
        for idx, child in enumerate(
            [i for i in self.sideBar.winfo_children() if isinstance(i, ctk.CTkButton)]
        ):
            child.configure(
                fg_color=(
                    ctk.ThemeManager.theme["CTk"]["fg_color"]
                    if idx == active
                    else "transparent"
                )
            )


def environment() -> EnvironmentVariables:
    """
    Load environment variables from a .env file and return them as an EnvironmentVariables instance.

    This function reads a .env file in the project root (./.env), loads its contents into the
    environment, and constructs an EnvironmentVariables object with the following fields:
        dev (bool): True if the DEV environment variable equals "true", False otherwise.
        userName (str | None): The value of the USER_NAME environment variable.
        secret (str | None): The value of the SECRET_STRING environment variable.
        tsgId (str | None): The value of the TSG_ID environment variable.

    Returns:
        EnvironmentVariables: A dataclass populated with the loaded environment values.
    """
    load_dotenv(dotenv_path="./.env")
    data = {
        "dev": True if os.getenv("DEV") == "true" else False,
        "userName": os.getenv("USER_NAME"),
        "secret": os.getenv("SECRET_STRING"),
        "tsgId": os.getenv("TSG_ID"),
    }
    return EnvironmentVariables(**data)


app = App(start_size=(1190, 620), env=environment())
app.mainloop()
