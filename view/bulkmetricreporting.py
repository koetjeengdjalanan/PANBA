import os
import queue
import sys
import threading
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import helper.logwriter as lw

from numpy import array_split
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta as rdt

from helper.api.getlist import ElementOfTenant
from helper.api.monitor import SysMetric
from helper.filehandler import FileHandler


class BulkMetricReporting(ctk.CTkFrame):
    def __init__(self, master, controller) -> None:
        super().__init__(master=master, fg_color="transparent", corner_radius=None)
        self.controller = controller
        self.FH = FileHandler()
        self.queuedRes = queue.Queue()
        self.siteList = None
        self.now = dt.now()
        defaultDiff: int = 90
        self.agoDate = self.now - rdt(days=defaultDiff - 1)
        self.dateInput = ctk.StringVar(value=self.now.strftime(format="%m/%d/%Y"))
        self.dateAgo = ctk.StringVar(value=self.agoDate.strftime(format="%m/%d/%Y"))
        self.dateDuration = ctk.IntVar(value=defaultDiff)
        self.pendingRes = []
        self.threadLock = threading.Lock()
        self.metrics = [
            {"name": "CPUUsage", "statistics": ["average"], "unit": "percentage"},
            {"name": "MemoryUsage", "statistics": ["average"], "unit": "percentage"},
            {"name": "DiskUsage", "statistics": ["average"], "unit": "percentage"},
            {
                "name": "InterfaceBandwidthUsage",
                "statistics": ["average"],
                "unit": "Mbps",
            },
        ]

        ### Output Dir ###
        outputDirFrame = ctk.CTkFrame(master=self)
        outputDirFrame.pack(fill="x", anchor="n", padx=10, pady=10, expand=True)
        self.outputDirEntry = ctk.CTkEntry(
            master=outputDirFrame,
            placeholder_text="Output Directory ...",
            state=ctk.DISABLED,
        )  # TODO: Make Text Entry change value on Input
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
        self.logTerminal = ctk.CTkTextbox(
            master=logFrame, wrap="none", state="disabled"
        )
        self.logTerminal.pack(fill=ctk.BOTH, padx=10, pady=10, expand=True)

    def pick_dest_dir(self) -> None:
        self.destDirectory = self.FH.select_directory().initDir
        self.outputDirEntry.configure(state=ctk.NORMAL)
        if self.destDirectory != "":
            self.FH.destDir = self.destDirectory
            self.outputDirEntry.delete(0, ctk.END)
            self.outputDirEntry.insert(0, self.destDirectory)
        self.outputDirEntry.configure(state=ctk.DISABLED)

    def date_picker(self, parent) -> None:
        ctk.CTkLabel(master=parent, text="Choose Date:").grid(
            column=0, row=1, padx=5, pady=5, sticky=ctk.W
        )
        dateInput = DateEntry(master=parent, textvariable=self.dateInput)
        dateInput.grid(column=1, row=1, padx=5, pady=5, columnspan=2, sticky=ctk.E)
        ctk.CTkLabel(master=parent, text="Duration:").grid(
            column=0, row=2, padx=5, pady=5, sticky=ctk.W
        )
        self.durationLabel = ctk.CTkLabel(master=parent, text="90 Day(s)")
        self.durationLabel.grid(column=2, row=2, padx=5, pady=5, sticky=ctk.E)
        self.dateSlider = ctk.CTkSlider(
            master=parent,
            from_=1,
            to=90,
            number_of_steps=89,
            variable=self.dateDuration,
            command=self.date_ago_pick,
        )
        self.dateSlider.grid(column=1, row=2, padx=5, pady=5, sticky=ctk.EW)

    def date_ago_pick(self, event=None) -> None:
        self.agoDate = self.now - rdt(days=(self.dateSlider.get() - 1))
        self.dateAgo = ctk.StringVar(value=self.agoDate.strftime(format="%m/%d/%Y"))
        self.durationLabel.configure(text=f"{int(self.dateSlider.get())} Day(s)")

    def get_site_list(self) -> None:
        element = ElementOfTenant(
            bearer_token=self.controller.authRes["data"]["access_token"]
        )
        try:
            res = element.request()
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
            pass
        get = threading.Thread(target=self.process_site_list, args=(res,))
        get.start()

    def process_site_list(self, data) -> None:
        id = []
        siteId = []
        name = []
        modelName = []
        hwId = []
        softwareVersion = []
        serialNumber = []
        for item in data["data"]["items"]:
            id.append(item["id"])
            siteId.append(item["site_id"])
            name.append(item["name"])
            modelName.append(item["model_name"])
            hwId.append(item["hw_id"])
            softwareVersion.append(item["software_version"])
            serialNumber.append(item["serial_number"])
        self.siteList = pd.DataFrame(
            data={
                "id": id,
                "site_id": siteId,
                "serial_number": serialNumber,
                "name": name,
                "model_name": modelName,
                "software_version": softwareVersion,
                "hw_id": hwId,
            }
        )
        self.safeDataButton.configure(state=ctk.ACTIVE)
        self.automateReport.configure(state=ctk.ACTIVE)

    def save_data(self) -> None:
        self.FH.save_file_loc(dirStr=self.destDirectory).export_excel(
            data=self.siteList
        )
        lw.text_view_render(
            widget=self.logTerminal, log="file saved: " + str(self.FH.savedFile)
        )

    def automate(self) -> None:
        threadCount: int = 4
        data: list = array_split(
            ary=self.siteList[:16],
            # ary=self.siteList,
            indices_or_sections=threadCount,
        )  # HACK: Get Only first 16 for dev purposes
        self.queuedRes = queue.Queue()
        workingThreads = []
        for _ in range(threadCount):
            worker = threading.Thread(target=self.iterate_site, args=(data[_],))
            worker.start()
            workingThreads.append(worker)
        self.controller.after(
            100, lambda: self.automate_thread_is_done(workers=workingThreads)
        )

    def automate_thread_is_done(self, workers: list) -> None:
        isAllDone: bool = all(not worker.is_alive() for worker in workers)
        while not self.queuedRes.empty():
            tempRes = self.queuedRes.get()
            with self.threadLock:
                self.pendingRes.append(tempRes)
        if not isAllDone:
            self.controller.after(
                100, lambda: self.automate_thread_is_done(workers=workers)
            )
        else:
            self.FH.save_file_loc(
                fileName="site_list_with_resource_metric.xlsx",
                promptDialog=False,
                dirStr=self.destDirectory,
            ).export_excel(data=pd.DataFrame(self.pendingRes)).open_explorer()
            lw.text_view_render(
                widget=self.logTerminal, log="All Done!, Excel File exported"
            )

    def iterate_site(self, siteList: pd.DataFrame) -> None:
        for index, row in siteList.iterrows():
            lw.text_view_render(
                widget=self.logTerminal, log=f"Working for  : {index} - {row['name']}"
            )
            res: dict = self.render_canvas(site=row["name"], tenant=row.to_dict())
            self.queuedRes.put(res)
            lw.text_view_render(
                widget=self.logTerminal, log=f"Generated for: {index} - {row['name']}"
            )

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

    def render_canvas(self, site: str, tenant: dict) -> dict:
        try:
            rawData = self.generate_data(tenant=tenant)
        except Exception as error:
            lw.text_view_render(widget=self.logTerminal, log=error, file=sys.stderr)
            raise ValueError(error)
        if not os.path.exists(f"{self.destDirectory}/{site}"):
            os.makedirs(f"{self.destDirectory}/{site}")
        res = tenant
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
                    s="PANBA V1.1.0 by NTT Data Indonesia",
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    alpha=0.1,
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
                ax.plot(
                    maxPercentage,
                    data.loc[maxPercentage]["value"],
                    "r^",
                    label="Max Percentile",
                )
                ax.annotate(
                    f"{maxPercentage.strftime('%d %b')}, {data.loc[maxPercentage]['value']:.2f}",
                    (maxPercentage, data.loc[maxPercentage]["value"]),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha="left",
                )
                ax.plot(
                    minPercentage,
                    data.loc[minPercentage]["value"],
                    "gv",
                    label="Min Percentile",
                )
                ax.annotate(
                    f"{minPercentage.strftime('%d %b')}, {data.loc[minPercentage]['value']:.2f}",
                    (minPercentage, data.loc[minPercentage]["value"]),
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
                        "Software": "PANBA V1.1.0 by NTT Indonesia",
                    },
                )
            except Exception as error:
                lw.text_view_render(widget=self.logTerminal, log=error, file=sys.stderr)
            plt.close()
            res[metric["series"][0]["name"]] = data["value"].mean()
        return res
