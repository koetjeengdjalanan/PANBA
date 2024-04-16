import customtkinter as ctk
from tkinter import PhotoImage, messagebox

from helper.api.auth import Login, Profile


class AccountNCredentials(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, fg_color="transparent", corner_radius=None)

        ### Root Frame ###
        self.root = ctk.CTkFrame(
            master=self, fg_color="transparent", corner_radius=None
        )
        self.root.pack(fill="both", expand=True)
        self.controller = controller
        # print(self.controller.env)

        username = ctk.StringVar()
        secret = ctk.StringVar()
        tsgId = ctk.StringVar()

        ### Logo ###
        ctk.CTkLabel(
            master=self.root,
            image=PhotoImage(
                name="PAN Logo", file="./assets/PANLogo(Dark).png"
            ).subsample(3, 3),
            text=None,
        ).pack(anchor="center", fill="x", expand=True)

        ### Credentials Input ###
        credentialsFrame = ctk.CTkFrame(master=self, fg_color="transparent")
        credentialsFrame.pack(anchor="n", fill="y", expand=True)
        ctk.CTkLabel(
            master=credentialsFrame, text="User Credentials", font=("arial", 32)
        ).grid(padx=5, pady=5, column=0, row=0, columnspan=4, sticky="nsew")
        ctk.CTkLabel(master=credentialsFrame, text="User Name").grid(
            padx=5, pady=5, column=0, row=1, sticky="w"
        )
        ctk.CTkLabel(master=credentialsFrame, text="Secret").grid(
            padx=5, pady=5, column=0, row=2, sticky="w"
        )
        ctk.CTkLabel(master=credentialsFrame, text="TSG Id").grid(
            padx=5, pady=5, column=0, row=3, sticky="w"
        )
        self.nameField = ctk.CTkEntry(
            master=credentialsFrame, justify="left", textvariable=username, width=400
        )
        self.nameField.grid(padx=5, pady=5, row=1, column=1, sticky="e", columnspan=3)
        self.secretField = ctk.CTkEntry(
            master=credentialsFrame,
            justify="left",
            textvariable=secret,
            width=400,
            show="*",
        )
        self.secretField.grid(padx=5, pady=5, row=2, column=1, sticky="e", columnspan=3)
        self.tsgIdField = ctk.CTkEntry(
            master=credentialsFrame, justify="left", textvariable=tsgId, width=400
        )
        self.tsgIdField.grid(padx=5, pady=5, row=3, column=1, sticky="e", columnspan=3)
        ctk.CTkButton(
            master=credentialsFrame,
            text="Clear",
            fg_color="gray25",
            hover_color="grey22",
        ).grid(pady=5, column=2, row=4, sticky="e")
        ctk.CTkButton(
            master=credentialsFrame, text="Log In", command=lambda: self.login()
        ).grid(pady=5, column=3, row=4, sticky="e")
        self.workingLabel = ctk.CTkLabel(master=credentialsFrame, text=None)
        self.workingLabel.grid(padx=5, pady=5, column=0, row=5, sticky="w")

        ### Populate Entry ###
        self.after(ms=10, func=self.__populate_entry)

    def __populate_entry(self) -> None:
        if self.controller.env["userName"] is not None or "":
            self.nameField.delete(first_index=0, last_index=ctk.END)
            self.nameField.insert(index=0, string=self.controller.env["userName"])
        if self.controller.env["secret"] is not None or "":
            self.secretField.delete(first_index=0, last_index=ctk.END)
            self.secretField.insert(index=0, string=self.controller.env["secret"])
        if self.controller.env["tsgId"] is not None or "":
            self.tsgIdField.delete(first_index=0, last_index=ctk.END)
            self.tsgIdField.insert(index=0, string=self.controller.env["tsgId"])

    def login(self) -> None:
        self.workingLabel.configure(require_redraw=True, text="Logging In...")
        try:
            auth = Login(
                username=self.nameField.get(),
                secret=self.secretField.get(),
                tsg_id=self.tsgIdField.get(),
            )
            self.workingLabel.configure(
                require_redraw=True, text="Login Success", text_color="lightgreen"
            )
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
        self.controller.authRes = auth.request()
        # print(self.controller.authRes)
        try:
            profile = Profile(
                bearer_token=self.controller.authRes["data"]["access_token"]
            )
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
        print(profile.request())
