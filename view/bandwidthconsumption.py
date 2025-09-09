import traceback
from pathlib import Path
import customtkinter as ctk
import pandas as pd
from helper.api.getlist import RemoteNetworkBandwidth
from helper.filehandler import FileHandler
import helper.logwriter as lw
from helper.settings.apisettings import BWConsSetting
from helper.config import save_config


class BandwidthConsumption(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, fg_color="transparent", corner_radius=None)
        self.controller = controller
        self.FH = FileHandler()
        # Prefill output path from config if available
        try:
            paths_cfg = (
                self.controller.config.get("paths")
                if isinstance(self.controller.config.get("paths"), dict)
                else None
            )
            if paths_cfg and paths_cfg.get("last_export_dir"):
                self.FH.destDir = Path(paths_cfg.get("last_export_dir"))
                self.FH.initDir = Path(paths_cfg.get("last_export_dir"))
        except Exception:
            pass
        self.outputPath: ctk.StringVar = ctk.StringVar(value=str(self.FH.savedFile))
        self.daysAgo: ctk.IntVar = ctk.IntVar(value=90)
        self.leftSetupFrame, self.rightSetupFrame = self.__setup_frame()
        self.__output_config()
        self.__prop_select()
        self.__log_frame()

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
        def set_output_path():
            # Use last_export_dir if present
            dir_hint = None
            try:
                paths_cfg = (
                    self.controller.config.get("paths")
                    if isinstance(self.controller.config.get("paths"), dict)
                    else None
                )
                dir_hint = paths_cfg.get("last_export_dir") if paths_cfg else None
            except Exception:
                dir_hint = None
            val = self.FH.save_file_loc(dirStr=dir_hint or self.FH.destDir).savedFile
            self.outputPath.set(value=str(val))
            lw.text_view_render(widget=self.logBox, log=f"File path set to {val}")
            outputEntry.xview_moveto(1)

        def date_picker():
            datePickerFrame = ctk.CTkFrame(master=outputFrame, fg_color="transparent")
            datePickerFrame.pack(fill=ctk.X, expand=True, pady=5)
            datePickerFrame.grid_columnconfigure(index=1, weight=3)
            ctk.CTkLabel(master=datePickerFrame, text="Duration").grid(
                row=0, column=0, sticky=ctk.W, pady=5, padx=5
            )
            ctk.CTkSlider(
                master=datePickerFrame,
                variable=self.daysAgo,
                from_=1,
                to=90,
                number_of_steps=89,
            ).grid(row=0, column=1, sticky=ctk.EW, pady=5)
            ctk.CTkLabel(master=datePickerFrame, text="Day(s)").grid(
                row=0, column=2, sticky=ctk.E, pady=5, padx=(5, 0)
            )
            ctk.CTkLabel(master=datePickerFrame, textvariable=self.daysAgo).grid(
                row=0, column=3, sticky=ctk.E, pady=5, padx=5
            )

        outputFrame = ctk.CTkFrame(master=self.rightSetupFrame, fg_color="transparent")
        outputFrame.pack(fill=ctk.X, expand=True, anchor=ctk.N, padx=10, pady=10)
        ctk.CTkLabel(master=outputFrame, text="Output File Path").pack(
            fill=ctk.X, expand=True, pady=5
        )
        outputEntry = ctk.CTkEntry(
            master=outputFrame, textvariable=self.outputPath, state=ctk.DISABLED
        )
        outputEntry.pack(fill=ctk.X, expand=True, pady=5)
        outputEntry.xview_moveto(1)
        outputEntry.bind(sequence="<Button-1>", command=lambda x: set_output_path())
        ctk.CTkLabel(master=outputFrame, text="Duration").pack(
            fill=ctk.X, expand=True, pady=5
        )
        date_picker()
        ctk.CTkButton(
            master=outputFrame,
            text="Export",
            command=self.export_data,
        ).pack(fill=ctk.X, expand=True, pady=5)

    def __prop_select(self):
        def toggle_state(prop: str):
            bWConsSetting.propState[prop] = not bWConsSetting.propState[prop]

        bWConsSetting = BWConsSetting
        propertiesSelectFrame = ctk.CTkScrollableFrame(
            master=self.leftSetupFrame, label_text="Properties Select", border_width=1
        )
        propertiesSelectFrame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        halfPoint = len(bWConsSetting.propState) // 2 + 1
        for id, prop in enumerate(bWConsSetting.propState):
            _ = ctk.CTkCheckBox(
                master=propertiesSelectFrame,
                text=prop,
                command=lambda x=prop: toggle_state(x),
            )
            _.select()
            _.grid(
                row=id if id < halfPoint else id - halfPoint,
                column=0 if id < halfPoint else 1,
                sticky="w",
                pady=(0, 5),
                padx=5,
            )

    def export_data(self):
        propList = [
            {"property": prop}
            for prop in BWConsSetting.propState
            if BWConsSetting.propState[prop]
        ]
        lw.text_view_render(
            widget=self.logBox,
            log=f"Count of properties selected: {len(propList)} & Days ago: {self.daysAgo.get()}",
        )
        body: dict = {
            "properties": propList,
            "filter": {
                "rules": [
                    {
                        "property": "event_time",
                        "operator": "last_n_days",
                        "values": [int(self.daysAgo.get())],
                    }
                ]
            },
        }
        lw.text_view_render(widget=self.logBox, log="Requesting Data")
        try:
            rm = RemoteNetworkBandwidth(
                bearer_token=self.controller.authRes["data"]["access_token"], body=body
            )
            res = rm.request()["data"]["data"]
            data = pd.DataFrame(res)
            lw.text_view_render(
                widget=self.logBox, log=f"Data Received\nCount: {len(data)}"
            )
            self.FH.export_excel(data=data)
            lw.text_view_render(
                widget=self.logBox,
                log=f"SUCCESS! Data Exported to {self.FH.savedFile}",
            )
            # Persist last export directory
            try:
                self.controller.config.setdefault("paths", {})["last_export_dir"] = str(
                    Path(self.FH.savedFile).parent
                )
                save_config(self.controller.config)
            except Exception:
                pass
        except Exception as e:
            lw.text_view_render(
                widget=self.logBox, log=f"ERROR! {e}\n{traceback.format_exc()}"
            )
