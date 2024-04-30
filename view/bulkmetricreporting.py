import os
import sys
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from numpy import array_split
import pandas as pd

from tkinter import messagebox
from tkcalendar import DateEntry
from threading import Thread
from datetime import datetime as dt, timedelta
from dateutil.relativedelta import relativedelta as rdt

from helper.api.getlist import ElementOfTenant
from helper.api.monitor import SysMetric
from helper.filehandler import FileHandler
from helper.terminalredirect import StdErrTerminalRedirect, StdOutTerminalRedirect


class BulkMetricReporting(ctk.CTkFrame):
    def __init__(self, master, controller) -> None:
        super().__init__(master=master, fg_color="transparent", corner_radius=None)
        self.controller = controller
        self.FH = FileHandler()
        self.siteList = None
        self.now = dt.now()
        self.agoDate = self.now - rdt(months=3)
        self.dateInput = ctk.StringVar(value=self.now.strftime(format="%m/%d/%Y"))
        self.dateAgo = ctk.StringVar(value=self.agoDate.strftime(format="%m/%d/%Y"))
        self.dateDuration = ctk.IntVar(value=3)
        self.metrics = [
            {
                "name": "InterfaceBandwidthUsage",
                "statistics": ["average"],
                "unit": "Mbps",
            },
            {"name": "CPUUsage", "statistics": ["average"], "unit": "percentage"},
            {"name": "MemoryUsage", "statistics": ["average"], "unit": "percentage"},
            {"name": "DiskUsage", "statistics": ["average"], "unit": "percentage"},
        ]

        ### Output Dir ###
        outputDirFrame = ctk.CTkFrame(master=self)
        outputDirFrame.pack(fill="x", anchor="n", padx=10, pady=10, expand=True)
        self.outputDirEntry = ctk.CTkEntry(
            master=outputDirFrame,
            placeholder_text="Output Directory ...",
        )
        self.outputDirEntry.pack(pady=10, padx=10, side="left", fill="x", expand=True)
        ctk.CTkButton(
            master=outputDirFrame,
            text="Set Directory ",
            command=self.pick_dest_dir,
            # command=lambda: threading.Thread(target=self.pick_source_file).start(),
        ).pack(padx=10, pady=10, side="right", fill="none", expand=False)

        ### Setting Frame ###
        settingFrame = ctk.CTkFrame(master=self)
        settingFrame.pack(fill="x", padx=10, pady=(0, 10), expand=True)
        settingFrame.grid_rowconfigure(index=0, weight=1)
        settingFrame.grid_columnconfigure(index=0, weight=1)

        ### # DatePicker # ###
        datePickerFrame = ctk.CTkFrame(master=settingFrame, fg_color="transparent")
        datePickerFrame.grid(padx=10, pady=10, column=0, row=0, sticky="nsew")
        datePickerFrame.grid_columnconfigure(index=0, weight=1)
        ctk.CTkLabel(
            master=datePickerFrame, text="Date Setting", font=("roboto", 20)
        ).grid(column=0, row=0)
        self.date_picker(parent=datePickerFrame)

        ### # Site List # ###
        siteListFrame = ctk.CTkFrame(master=settingFrame, fg_color="transparent")
        siteListFrame.grid(padx=10, pady=10, column=1, row=0, sticky="nsew")
        siteListFrame.grid_columnconfigure(index=0, weight=1)
        ctk.CTkLabel(master=siteListFrame, text="Site list", font=("roboto", 20)).grid(
            column=0, row=0, sticky=ctk.E
        )
        ctk.CTkButton(
            master=siteListFrame, text="Get Data", command=self.get_site_list
        ).grid(column=1, row=0, padx=5, pady=5, columnspan=2, sticky=ctk.W)
        self.safeDataButton = ctk.CTkButton(
            master=siteListFrame,
            text="Save as Excel",
            state=ctk.DISABLED,
            command=self.save_data,
        )
        self.safeDataButton.grid(column=1, row=1, padx=5, pady=5)
        self.automateReport = ctk.CTkButton(
            master=siteListFrame,
            text="Automate",
            state=ctk.DISABLED,
            command=self.automate,
        )
        self.automateReport.grid(column=2, row=1, padx=5, pady=5)

        ### Log Frame ###
        logFrame = ctk.CTkFrame(master=self)
        logFrame.pack(fill=ctk.BOTH, padx=10, pady=(0, 10), expand=True)
        self.logTerminal = ctk.CTkTextbox(master=logFrame, wrap="none")
        self.logTerminal.pack(fill=ctk.BOTH, padx=10, pady=10, expand=True)
        sys.stdout = StdOutTerminalRedirect(widget=self.logTerminal)
        sys.stderr = StdErrTerminalRedirect(widget=self.logTerminal)

    def pick_dest_dir(self) -> None:
        self.destDirectory = self.FH.select_directory()
        if self.destDirectory != "":
            self.outputDirEntry.delete(0, ctk.END)
            self.outputDirEntry.insert(0, self.destDirectory)

    def date_picker(self, parent) -> None:
        ctk.CTkLabel(master=parent, text="Choose Date:").grid(
            column=0, row=1, padx=5, pady=5, sticky=ctk.W
        )
        dateInput = DateEntry(master=parent, textvariable=self.dateInput)
        dateInput.grid(column=1, row=1, padx=5, pady=5, columnspan=2, sticky=ctk.E)
        ctk.CTkLabel(master=parent, text="Duration:").grid(
            column=0, row=2, padx=5, pady=5, sticky=ctk.W
        )
        self.durationLabel = ctk.CTkLabel(master=parent, text="3 Month(s)")
        self.durationLabel.grid(column=2, row=2, padx=5, pady=5, sticky=ctk.E)
        self.dateSlider = ctk.CTkSlider(
            master=parent,
            from_=1,
            to=6,
            number_of_steps=5,
            variable=self.dateDuration,
            command=self.date_ago_pick,
        )
        self.dateSlider.grid(column=1, row=2, padx=5, pady=5, sticky=ctk.EW)

    def date_ago_pick(self, event=None) -> None:
        self.agoDate = self.now - rdt(months=self.dateSlider.get())
        self.dateAgo = ctk.StringVar(value=self.agoDate.strftime(format="%m/%d/%Y"))
        self.durationLabel.configure(text=f"{int(self.dateSlider.get())} Month(s)")

    def get_site_list(self) -> None:
        element = ElementOfTenant(
            bearer_token=self.controller.authRes["data"]["access_token"]
        )
        try:
            res = element.request()
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
            pass
        get = Thread(target=self.process_site_list, args=(res,))
        get.start()

    def process_site_list(self, data) -> None:
        id = []
        siteId = []
        name = []
        softwareVersion = []
        serialNumber = []
        for item in data["data"]["items"]:
            id.append(item["id"])
            siteId.append(item["site_id"])
            name.append(item["name"])
            softwareVersion.append(item["software_version"])
            serialNumber.append(item["serial_number"])
        self.siteList = pd.DataFrame(
            data={
                "id": id,
                "site_id": siteId,
                "name": name,
                "software_version": softwareVersion,
                "serial_number": serialNumber,
            }
        )
        self.safeDataButton.configure(state=ctk.ACTIVE)
        self.automateReport.configure(state=ctk.ACTIVE)

    def save_data(self) -> None:
        self.FH.save_as_excel(data=self.siteList, directory=self.destDirectory)

    def automate(self) -> None:
        data = array_split(ary=self.siteList, indices_or_sections=4)
        proc0 = Thread(target=self.iterate_site, args=(data[0],))
        proc1 = Thread(target=self.iterate_site, args=(data[1],))
        proc2 = Thread(target=self.iterate_site, args=(data[2],))
        proc3 = Thread(target=self.iterate_site, args=(data[3],))
        proc0.start()
        proc1.start()
        proc2.start()
        proc3.start()

    def iterate_site(self, siteList: pd.DataFrame) -> None:
        for index, row in siteList.iterrows():
            print(f"Working for: {index} - {row['name']}\n")
            self.render_canvas(site=row["name"], tenant=row.to_dict())

    def generate_data(self, tenant: dict) -> dict:
        payload = {
            "start_time": dt.strptime(
                f"{self.dateAgo.get()} 00 00",
                "%m/%d/%Y %H %M",
            ).isoformat()
            + ".000Z",
            "end_time": dt.strptime(
                f"{self.dateInput.get()} 00 00",
                "%m/%d/%y %H %M",
            ).isoformat()
            + ".000Z",
            "interval": "1day",
            "metrics": self.metrics,
            "filter": {"site": [tenant["site_id"]], "element": [tenant["id"]]},
        }
        SM = SysMetric(
            bearer_token=self.controller.authRes["data"]["access_token"], body=payload
        )
        res = SM.request()
        return res

    def render_canvas(self, site: str, tenant) -> None:
        rawData = self.generate_data(tenant=tenant)
        if not os.path.exists(f"{self.destDirectory}/{site}"):
            os.makedirs(f"{self.destDirectory}/{site}")
        for metric in rawData["data"]["metrics"]:
            try:
                data = pd.DataFrame(
                    data=metric["series"][0]["data"][0]["datapoints"]
                ).set_index("time")
                data.index = pd.to_datetime(data.index)
                maxPercentage = data["value"].idxmax()
                minPercentage = data["value"].idxmin()
                fig, ax = plt.subplots(figsize=(15, 6))
                fig.subplots_adjust(bottom=0.15)
                ax.text(
                    x=0.5,
                    y=0.5,
                    s="PANBA V0.2.0 by NTT Indonesia",
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    alpha=0.2,
                    zorder=-1,
                    rotation=30,
                    fontsize=30,
                    fontweight=10,
                )
                ax.set_title(site)
                ax.plot(
                    data.index,
                    data["value"],
                    linestyle="solid",
                    label=metric["series"][0]["name"],
                )
                for percent in maxPercentage, minPercentage:
                    ax.plot(
                        percent,
                        data.loc[percent]["value"],
                        "r^",
                        label="Max Percentile",
                    )
                    ax.annotate(
                        f"{percent.strftime('%d %b')}, {data.loc[percent]['value']:.2f}",
                        (percent, data.loc[percent]["value"]),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha="left",
                    )
                ax.grid(visible=True, which="both", linestyle=":")
                ax.set_xlabel("Dates")
                ax.xaxis.set_minor_locator(mdates.DayLocator())
                locator = mdates.DayLocator(bymonthday=(1, 10, 20))
                formatter = mdates.ConciseDateFormatter(locator)
                ax.xaxis.set_major_locator(locator)
                ax.xaxis.set_major_formatter(formatter)
                ax.set_ylabel(metric["series"][0]["unit"])
                ax.legend()
                plt.savefig(
                    fname=f"{self.destDirectory}/{site}/{metric['series'][0]['name']}.png",
                    metadata={
                        "Title": f"{site}-{metric['series'][0]['name']}",
                        "Copyright": "Reserved By: NTT Indonesia",
                        "Software": "PANBA V0.2.0 by NTT Indonesia",
                    },
                )
            except Exception as error:
                print(error, file=sys.stderr)
            plt.close()