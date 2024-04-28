from tkinter import messagebox
import customtkinter as ctk

from datetime import datetime as dt, timedelta
from tkcalendar import DateEntry

from helper.api.getlist import ElementOfTenant


class MetricVariableSetting(ctk.CTkToplevel):
    def __init__(self, master, controller):
        super().__init__(master=master)
        self.iconbitmap("./favicon.ico")
        self.title("Metric Variable Setting")
        self.geometry("600*800")
        self.controller = controller

        ### Date Input ###
        self.now = dt.now()
        self.dateTimeFrom = ctk.StringVar(value=self.now - timedelta(days=30))
        self.hourTimeFrom = ctk.StringVar(value=self.now.hour)
        self.minuteTimeFrom = ctk.StringVar(value=self.now.minute)
        self.dateTimeTo = ctk.StringVar(value=self.now)
        self.hourTimeTo = ctk.StringVar(value=self.now.hour)
        self.minuteTimeTo = ctk.StringVar(value=self.now.minute)
        self.duration = ctk.StringVar(value="1day")
        self.dateInputFrame = ctk.CTkFrame(master=self)
        self.dateInputFrame.pack(fill=ctk.X, expand=True, padx=10, pady=10)
        self.cbxVars = []
        self.selected = []
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
        _ = self.__date_input(
            parent=self.dateInputFrameFrom,
            type="from",
            date=self.dateTimeFrom,
            hour=self.hourTimeFrom,
            minute=self.minuteTimeFrom,
        )
        _ = self.__date_input(
            parent=self.dateInputFrameTo,
            type="to",
            date=self.dateTimeTo,
            hour=self.hourTimeTo,
            minute=self.minuteTimeTo,
        )
        self.__duration_select()

        ### Choose Site ###
        self.siteListFrame = ctk.CTkScrollableFrame(master=self)
        self.siteListFrame.pack(fill=ctk.X, expand=True, padx=10, pady=(0, 10))
        ctk.CTkButton(
            master=self.siteListFrame, text="get", command=self.get_element_list
        ).pack()

        ### Confirm Deny ###
        confirmationFrame = ctk.CTkFrame(master=self, fg_color="transparent")
        confirmationFrame.pack(fill=ctk.X, expand=True, padx=10, pady=(0, 10))
        ctk.CTkButton(
            master=confirmationFrame, text="Confirm", command=self.confirm
        ).pack(side=ctk.RIGHT, padx=10)
        ctk.CTkButton(
            master=confirmationFrame, text="Cancel", command=self.__on_closed
        ).pack(side=ctk.RIGHT, padx=10)

    def __date_input(self, parent, type: str, date, hour, minute) -> None:
        ctk.CTkLabel(master=parent, text=type).grid(column=0, row=0, columnspan=3)
        ctk.CTkLabel(master=parent, text="Date: ").grid(
            column=0, row=1, pady=5, padx=5, sticky=ctk.W
        )
        dateTime = DateEntry(master=parent, textvariable=date)
        dateTime.grid(column=1, row=1, pady=5, padx=5, sticky=ctk.EW, columnspan=2)
        ctk.CTkLabel(master=parent, text="Time: ").grid(column=0, row=2, pady=5, padx=5)
        hourInput = ctk.CTkComboBox(
            master=parent,
            values=[str(x) for x in range(0, 24)],
            width=100,
            variable=hour,
        )
        hourInput.set(value=str(self.now.hour))
        hourInput.grid(column=1, row=2, pady=5, padx=5)
        minuteInput = ctk.CTkComboBox(
            master=parent,
            values=[str(x) for x in range(0, 60)],
            width=100,
            variable=minute,
        )
        minuteInput.set(value=str(self.now.minute))
        minuteInput.grid(column=2, row=2, pady=5, padx=5)

    def __duration_select(self):
        durationList = (
            ("10 Sec", "10sec"),
            ("1 Min", "1min"),
            ("5 Min", "5min"),
            ("1 Hour", "1hour"),
            ("1 Day", "1day"),
        )
        durationFrame = ctk.CTkFrame(master=self)
        durationFrame.pack(padx=10, pady=(0, 10))
        col = 0
        ctk.CTkLabel(master=durationFrame, text="Duration: ").grid(
            row=0, column=col, pady=(5, 0), padx=(10, 0)
        )
        # ctk.CTkEntry(master=durationFrame, width=5, )
        for duration in durationList:
            col = col + 1
            ctk.CTkRadioButton(
                master=durationFrame,
                text=duration[0],
                variable=self.duration,
                value=duration[1],
            ).grid(
                row=0,
                column=col,
                padx=5,
                pady=5,
            )

    def get_element_list(self):
        element = ElementOfTenant(
            bearer_token=self.controller.controller.authRes["data"]["access_token"]
        )
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
        self.selectAllVars = ctk.BooleanVar()
        selectAll = ctk.CTkCheckBox(
            master=self.siteListFrame, text="Select All", variable=self.selectAllVars
        )
        selectAll.configure(command=self.handle_select_all)
        selectAll.pack(padx=10, pady=(5, 0), anchor=ctk.W)
        for item in data["data"]["items"]:
            cbState = ctk.BooleanVar()
            self.cbxVars.append(cbState)
            cbState.item = item
            cb = ctk.CTkCheckBox(
                master=self.siteListFrame, text=item["name"], variable=cbState
            )
            cb.configure(
                command=lambda x=item, cbx=cb: self.handle_selection(
                    checkbox=cbx, item=x
                )
            )
            cb.pack(padx=10, pady=(5, 0), anchor=ctk.W)

    def handle_select_all(self) -> None:
        for cbx in self.cbxVars:
            cbx.set(self.selectAllVars.get())
            self.handle_selection(cbx, cbx.item)

    def handle_selection(self, checkbox, item) -> None:
        if checkbox.get():
            self.selected.append([item["site_id"], item["id"], item["name"]])
        else:
            self.selected.remove([item["site_id"], item["id"], item["name"]])

    def __define_time_range(self) -> list:
        return list(range(0, 24))

    def var_setting(self) -> dict:
        return {}

    def confirm(self) -> dict:
        self.controller.bodyVars = {
            "globalVars": {
                "start_time": dt.strptime(
                    f"{self.dateTimeFrom.get()} {self.hourTimeFrom.get()} {self.minuteTimeFrom.get()}",
                    "%m/%d/%y %H %M",
                ).isoformat()
                + ".000Z",
                "end_time": dt.strptime(
                    f"{self.dateTimeTo.get()} {self.hourTimeTo.get()} {self.minuteTimeTo.get()}",
                    "%m/%d/%y %H %M",
                ).isoformat()
                + ".000Z",
                "interval": self.duration.get(),
            },
            "selected": self.selected,
        }
        self.event_generate("<<ConfirmSetting>>")
        self.__on_closed()
        return self.controller.bodyVars

    def __on_closed(self):
        self.destroy()
