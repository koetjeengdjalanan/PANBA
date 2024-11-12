from datetime import datetime as dt
import customtkinter as ctk
import operator
from helper.settings.apisettings import BWConsSetting


class BandwidthConsumption(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, fg_color="transparent", corner_radius=None)
        self.controller = controller
        self.leftSetupFrame, self.rightSetupFrame = self.__setup_frame()
        self.__log_frame()
        self.__output_config()
        self.__prop_select()

    def __setup_frame(self) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
        setupFrame = ctk.CTkFrame(master=self)
        setupFrame.pack(fill=ctk.X, anchor=ctk.N, padx=10, pady=10)
        setupFrame.columnconfigure(0, weight=1)
        setupFrame.columnconfigure(1, weight=1)
        leftSetupFrame = ctk.CTkFrame(master=setupFrame, fg_color="transparent")
        leftSetupFrame.grid(row=0, column=0, sticky=ctk.EW)
        rightSetupFrame = ctk.CTkFrame(master=setupFrame, fg_color="transparent")
        rightSetupFrame.grid(row=0, column=1, sticky=ctk.EW)
        return leftSetupFrame, rightSetupFrame

    def __log_frame(self):
        logFrame = ctk.CTkFrame(master=self)
        logFrame.pack(fill=ctk.BOTH, expand=True, anchor=ctk.S, padx=10, pady=10)
        ctk.CTkLabel(
            master=logFrame, text="Log Configuration", font=("Arial", 12, "bold")
        ).pack(fill=ctk.X, expand=True, pady=5, anchor=ctk.W)
        self.logBox = ctk.CTkTextbox(master=logFrame, state="disabled")
        self.logBox.pack(fill=ctk.BOTH, expand=True, pady=(0, 5), padx=5)

    def __output_config(self):
        outputFrame = ctk.CTkFrame(master=self.leftSetupFrame, fg_color="transparent")
        outputFrame.pack(fill=ctk.X, expand=True, anchor=ctk.N, padx=10, pady=10)
        ctk.CTkLabel(
            master=outputFrame, text="Output Configuration", font=("Arial", 12, "bold")
        ).pack(fill=ctk.X, expand=True, pady=5)
        ctk.CTkLabel(master=outputFrame, text="Output File").pack(
            fill=ctk.X, expand=True, pady=5
        )
        ctk.CTkEntry(master=outputFrame).pack(fill=ctk.X, expand=True, pady=5)
        ctk.CTkButton(
            master=outputFrame, text="Browse", command=lambda: self.writeLog("Browse")
        ).pack(fill=ctk.X, expand=True, pady=5)
        ctk.CTkLabel(master=outputFrame, text="Output Format").pack(
            fill=ctk.X, expand=True, pady=5
        )
        ctk.CTkButton(
            master=outputFrame, text="Export", command=lambda: self.writeLog("Export")
        ).pack(fill=ctk.X, expand=True, pady=5)

    def __prop_select(self):
        bWConsSetting = BWConsSetting
        propertiesFrame = ctk.CTkFrame(
            master=self.rightSetupFrame, fg_color="transparent"
        )
        propertiesFrame.pack(fill=ctk.X, expand=True, anchor=ctk.N, padx=10, pady=10)
        ctk.CTkLabel(
            master=propertiesFrame, text="Properties Select", font=("Arial", 12, "bold")
        ).pack(fill=ctk.X, expand=True, pady=5)
        propertiesSelectFrame = ctk.CTkScrollableFrame(
            master=propertiesFrame, border_width=1
        )
        propertiesSelectFrame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 10))
        halfPoint = int((len(bWConsSetting.propState) / 2))
        for id, prop in enumerate(bWConsSetting.propState):
            _ = ctk.CTkCheckBox(
                master=propertiesSelectFrame,
                text=prop,
                command=lambda x=prop: operator.setitem(
                    bWConsSetting.propState, x, not bWConsSetting.propState[x]
                ),
            )
            _.select()
            _.grid(
                row=id if id < halfPoint else id - halfPoint,
                column=0 if id < halfPoint else 1,
                sticky="w",
                pady=(0, 5),
                padx=5,
            )

    def writeLog(self, log: str):
        self.logBox.configure(state="normal")
        self.logBox.insert(ctk.END, f"[ {dt.now():%d-%m-%Y %H:%M:%S} ] {log} \n\n")
        self.logBox.configure(state="disabled")
        self.logBox.see(ctk.END)
