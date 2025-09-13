import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from threading import Thread

from helper.api.auth import Login, Profile
from assets.getfile import GetFile
from helper.config import decrypt_secret, encrypt_secret, save_config


class AccountNCredentials(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, fg_color="transparent", corner_radius=None)

        ### Root Frame ###
        self.root = ctk.CTkFrame(
            master=self, fg_color="transparent", corner_radius=None
        )
        self.root.pack(fill="both", expand=True)
        self.controller = controller
        self.getFile = GetFile
        # print(self.controller.env)

        # Typed tkinter variables
        self.username: ctk.StringVar = ctk.StringVar()
        self.secret: ctk.StringVar = ctk.StringVar()
        self.tsgId: ctk.StringVar = ctk.StringVar()
        self.status: ctk.StringVar = ctk.StringVar()
        self.rememberMe: ctk.BooleanVar = ctk.BooleanVar(
            value=bool(controller.config.get("ui", {}).get("remember_me", True))
        )

        ### Logo ###
        logo = ctk.CTkImage(
            dark_image=Image.open(
                self.getFile.getAssets(file_name="PANLogo(Dark).png")
            ),
            light_image=Image.open(self.getFile.getAssets(file_name="PANLogo.png")),
            size=(700, 128),
        )
        ctk.CTkLabel(
            master=self.root,
            image=logo,
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
            master=credentialsFrame,
            justify="left",
            textvariable=self.username,
            width=400,
        )
        self.nameField.grid(padx=5, pady=5, row=1, column=1, sticky="e", columnspan=3)
        self.secretField = ctk.CTkEntry(
            master=credentialsFrame,
            justify="left",
            textvariable=self.secret,
            width=400,
            show="*",
        )
        self.secretField.grid(padx=5, pady=5, row=2, column=1, sticky="e", columnspan=3)
        self.tsgIdField = ctk.CTkEntry(
            master=credentialsFrame, justify="left", textvariable=self.tsgId, width=400
        )
        self.tsgIdField.grid(padx=5, pady=5, row=3, column=1, sticky="e", columnspan=3)
        self.clearButton = ctk.CTkButton(
            master=credentialsFrame,
            text="Clear",
            fg_color="gray25",
            hover_color="grey22",
            command=self.clear_entry,
        )
        self.clearButton.grid(pady=5, column=2, row=4, sticky="e")
        ctk.CTkCheckBox(
            master=credentialsFrame, text="Remember me", variable=self.rememberMe
        ).grid(pady=5, column=0, row=4, sticky="w")
        self.logInButton = ctk.CTkButton(
            master=credentialsFrame, text="Log In", command=self.login
        )
        self.logInButton.grid(pady=5, column=3, row=4, sticky="e")
        self.workingLabel = ctk.CTkLabel(
            master=credentialsFrame, textvariable=self.status
        )
        self.workingLabel.grid(
            padx=5, pady=5, column=0, row=5, sticky="w", columnspan=4
        )

        ### Populate Entry ###
        # Populate fields shortly after render
        self.after(ms=10, func=self.__populate_entry)

    def __populate_entry(self) -> None:
        """Prefill credential fields from .env (fast) then config (robust)."""
        try:
            env = self.controller.env or {}
            # .env first (dev convenience)
            if env.get("userName"):
                self.nameField.delete(0, ctk.END)
                self.nameField.insert(0, env.get("userName"))
            if env.get("secret"):
                self.secretField.delete(0, ctk.END)
                self.secretField.insert(0, env.get("secret"))
            if env.get("tsgId"):
                self.tsgIdField.delete(0, ctk.END)
                self.tsgIdField.insert(0, env.get("tsgId"))
            # Config fallback (persisted between runs)
            self._prefill_from_config()
        except Exception:
            # Silently ignore prefill errors to avoid blocking UI
            pass

    def _prefill_from_config(self) -> None:
        """Fill fields from persisted config using DPAPI to decrypt secret."""
        cfg = self.controller.config
        auth = cfg.get("auth", {}) if isinstance(cfg.get("auth"), dict) else {}
        username = auth.get("username")
        tsg_id = auth.get("tsg_id")
        secret_enc = auth.get("secret_enc", "")
        if username:
            self.nameField.delete(0, ctk.END)
            self.nameField.insert(0, str(username))
        if tsg_id:
            self.tsgIdField.delete(0, ctk.END)
            self.tsgIdField.insert(0, str(tsg_id))
        if secret_enc:
            try:
                plain = decrypt_secret(secret_enc)
                if plain:
                    self.secretField.delete(0, ctk.END)
                    self.secretField.insert(0, plain)
            except Exception:
                # Ignore decryption errors; user can retype
                pass

    def clear_entry(self) -> None:
        self.username.set("")
        self.secret.set("")
        self.tsgId.set("")
        self.status.set("")
        self.workingLabel.configure(require_redraw=True)

    def lock_creds(self) -> None:
        self.nameField.configure(state=ctk.DISABLED)
        self.secretField.configure(state=ctk.DISABLED)
        self.tsgIdField.configure(state=ctk.DISABLED)
        self.clearButton.configure(state=ctk.DISABLED)
        self.logInButton.configure(state=ctk.DISABLED)

    def login(self) -> None:
        if not all([self.username.get(), self.secret.get(), self.tsgId.get()]):
            self.status.set("Please Fill All Credentials")
            return None
        self.status.set("Logging In...")
        try:
            auth = Login(
                username=self.username.get(),
                secret=self.secret.get(),
                tsg_id=self.tsgId.get(),
            )
            self.status.set("Getting Profile...")
            self.controller.authRes = auth.request()
            profile = Profile(
                bearer_token=self.controller.authRes["data"]["access_token"]
            )
            self.controller.resProfile = profile.request()
            self.status.set("Login Success")
            self.master.activate_menu()
            self.lock_creds()
            # Persist credentials and preference if enabled
            self._persist_credentials()
            Thread(
                target=self.after,
                args=(
                    (self.controller.authRes.get("data").get("expires_in", 60 * 15) - 1)
                    * 1000,
                    self.refresh_token,
                ),
                daemon=True,
            ).start()
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
            self.status.set("Logging In Failed")

    def refresh_token(self) -> None:
        expires_in = (
            self.controller.authRes.get("data").get("expires_in", 60 * 15) - 1
        ) * 1000
        if not all([self.username.get(), self.secret.get(), self.tsgId.get()]):
            return None
        try:
            auth = Login(
                username=self.username.get(),
                secret=self.secret.get(),
                tsg_id=self.tsgId.get(),
            )
            self.controller.authRes = auth.request()
            profile = Profile(
                bearer_token=self.controller.authRes["data"]["access_token"]
            )
            self.controller.resProfile = profile.request()
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
            return None
        self.after(expires_in, self.refresh_token)

    def _persist_credentials(self) -> None:
        """Persist current credentials to config if 'Remember me' is enabled.

        Uses DPAPI to encrypt the secret. Updates the app's in-memory config
        first, then saves to disk. Errors are ignored to avoid blocking UI.
        """
        try:
            # Update remember_me preference
            self.controller.config.setdefault("ui", {})["remember_me"] = bool(
                self.rememberMe.get()
            )
            if not self.rememberMe.get():
                return
            # Write auth fields
            auth = self.controller.config.setdefault("auth", {})
            auth["username"] = self.username.get()
            auth["tsg_id"] = self.tsgId.get()
            auth["secret_enc"] = encrypt_secret(self.secret.get())
            save_config(self.controller.config)
        except Exception:
            # Do not fail login if persistence fails
            pass
