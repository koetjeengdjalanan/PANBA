from tkinter import ANCHOR, messagebox
import customtkinter as ctk

from datetime import datetime as dt
from tkcalendar import Calendar, DateEntry

from helper.api.getlist import ElementOfTenant


class MetricVariableSetting(ctk.CTkToplevel):
    def __init__(self, master, bearer_token: str, data: dict = {}):
        super().__init__(master=master)
        self.iconbitmap("./favicon.ico")
        self.title("Metric Variable Setting")
        self.geometry("600*800")
        self.data = data
        self.bearerToken = bearer_token

        ### Date Input ###
        # self.dateTimeFrom = ctk.StringVar()
        # self.hourTimeFrom = ctk.StringVar()
        # self.minuteTimeFrom = ctk.StringVar()
        # self.dateTimeTo = ctk.StringVar()
        # self.hourTimeTo = ctk.StringVar()
        # self.minuteTimeTo = ctk.StringVar()
        self.dateInputFrame = ctk.CTkFrame(master=self)
        self.dateInputFrame.pack(fill=ctk.X, expand=True, padx=10, pady=10)
        ctk.CTkLabel(
            master=self.dateInputFrame,
            anchor=ctk.CENTER,
            text="DateTime Config",
            font=("roboto", 18),
        ).pack()
        self.dateInputFrameFrom = ctk.CTkFrame(
            master=self.dateInputFrame, fg_color="transparent"
        )
        self.dateInputFrameFrom.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        self.dateInputFrameTo = ctk.CTkFrame(
            master=self.dateInputFrame, fg_color="transparent"
        )
        self.dateInputFrameTo.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)
        inputFrom = self.__date_input(parent=self.dateInputFrameFrom, type="from")
        inputTo = self.__date_input(parent=self.dateInputFrameTo, type="to")

        ### Choose Site ###
        self.siteListFrame = ctk.CTkScrollableFrame(master=self)
        self.siteListFrame.pack(fill=ctk.X, expand=True, padx=10, pady=(0, 10))
        ctk.CTkButton(
            master=self.siteListFrame, text="get", command=self.get_element_list
        ).pack()

        ### Confirm Deny ###
        confirmationFrame = ctk.CTkFrame(master=self, fg_color="transparent")
        confirmationFrame.pack(fill=ctk.X, expand=True, padx=10, pady=(0, 10))
        ctk.CTkButton(master=confirmationFrame, text="Confirm").pack(
            side=ctk.RIGHT, padx=10
        )
        ctk.CTkButton(master=confirmationFrame, text="Cancel").pack(
            side=ctk.RIGHT, padx=10
        )

    def __date_input(self, parent, type: str) -> None:
        ctk.CTkLabel(master=parent, text=type).grid(column=0, row=0, columnspan=3)
        ctk.CTkLabel(master=parent, text="Date: ").grid(column=0, row=1, sticky=ctk.W)
        dateTime = DateEntry(master=parent)
        dateTime.grid(column=1, row=1, sticky=ctk.EW, columnspan=2)
        ctk.CTkLabel(master=parent, text="Time: ").grid(column=0, row=2)
        hourInput = ctk.CTkComboBox(
            master=parent,
            values=[str(x) for x in range(0, 24)],
        )
        hourInput.grid(column=1, row=2)
        minuteInput = ctk.CTkComboBox(
            master=parent,
            values=[str(x) for x in range(0, 60)],
        )
        minuteInput.grid(column=2, row=2)

    def get_element_list(self):
        element = ElementOfTenant(bearer_token=self.bearerToken)
        try:
            res = element.request()
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
            return None
        for child in self.siteListFrame.winfo_children():
            child.destroy()
        self.siteListFrame.after(
            ms=10, func=lambda: self.populate_element_list(data=res)
        )
        return res

    def populate_element_list(self, data):
        for item in data["data"]["items"]:
            ctk.CTkCheckBox(
                master=self.siteListFrame,
                text=item["name"],
                command=lambda x=item: print([x["site_id"], x["id"]]),
            ).pack(padx=10, pady=(5, 0), anchor=ctk.W)

    def __define_time_range(self) -> list:
        return list(range(0, 24))

    def var_setting(self) -> dict:
        return {}
