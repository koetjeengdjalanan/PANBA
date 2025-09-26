"""Account and Credentials View Module."""

from threading import Thread
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from assets.getfile import GetFile
from helper.api.auth import Login, Profile
from helper.config import decrypt_secret, encrypt_secret, save_config
from models import AppController, AuthenticationProfile


class AccountNCredentials(ctk.CTkFrame):
    """A CustomTkinter frame for handling user authentication.

    This class creates the user interface for the login screen, including
    input fields for username, secret, and TSG ID. It manages user
    interactions such as entering credentials, initiating the login process,
    and opting to save credentials for future sessions. Upon successful
    login, it locks the input fields and schedules a periodic token refresh.

    Attributes:
        controller (AppController): The main application controller instance, used
            to manage application state and data.
        username (ctk.StringVar): The tkinter variable bound to the username entry field.
        secret (ctk.StringVar): The tkinter variable bound to the secret entry field.
        tsgId (ctk.StringVar): The tkinter variable bound to the TSG ID entry field.
        status (ctk.StringVar): The tkinter variable for displaying status messages
            (e.g., "Logging In...", "Login Success").
        rememberMe (ctk.BooleanVar): The tkinter variable bound to the "Remember me"
            checkbox.
    """

    def __init__(self, master: ctk.CTk, controller: AppController):
        super().__init__(
            master=master,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"],
            corner_radius=None,
        )

        ### Root Frame ###
        self.root = ctk.CTkFrame(master=self, fg_color="transparent", corner_radius=None)
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
            dark_image=Image.open(self.getFile.getAssets(file_name="PANLogo(Dark).png")),
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
        ctk.CTkLabel(master=credentialsFrame, text="User Credentials", font=("arial", 32)).grid(
            padx=5, pady=5, column=0, row=0, columnspan=4, sticky="nsew"
        )
        ctk.CTkLabel(master=credentialsFrame, text="User Name").grid(padx=5, pady=5, column=0, row=1, sticky="w")
        ctk.CTkLabel(master=credentialsFrame, text="Secret").grid(padx=5, pady=5, column=0, row=2, sticky="w")
        ctk.CTkLabel(master=credentialsFrame, text="TSG Id").grid(padx=5, pady=5, column=0, row=3, sticky="w")
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
        self.tsgIdField = ctk.CTkEntry(master=credentialsFrame, justify="left", textvariable=self.tsgId, width=400)
        self.tsgIdField.grid(padx=5, pady=5, row=3, column=1, sticky="e", columnspan=3)
        self.clearButton = ctk.CTkButton(
            master=credentialsFrame,
            text="Clear",
            fg_color="gray25",
            hover_color="grey22",
            command=self.__clear_entry,
        )
        self.clearButton.grid(pady=5, column=2, row=4, sticky="e")
        ctk.CTkCheckBox(master=credentialsFrame, text="Remember me", variable=self.rememberMe).grid(
            pady=5, column=0, row=4, sticky="w"
        )
        self.logInButton = ctk.CTkButton(master=credentialsFrame, text="Log In", command=self.login)
        self.logInButton.grid(pady=5, column=3, row=4, sticky="e")
        self.workingLabel = ctk.CTkLabel(master=credentialsFrame, textvariable=self.status)
        self.workingLabel.grid(padx=5, pady=5, column=0, row=5, sticky="w", columnspan=4)

        ### Populate Entry ###
        # Populate fields shortly after render
        self.after(ms=10, func=self.__populate_entry)

    def __populate_entry(self) -> None:
        """Prefill credential fields from .env (fast) then config (robust)."""
        try:
            self.nameField.delete(0, ctk.END)
            self.nameField.insert(0, self.controller.env.userName)
            self.tsgIdField.delete(0, ctk.END)
            self.tsgIdField.insert(0, self.controller.env.tsgId)
            self.secretField.delete(0, ctk.END)
            self.secretField.insert(0, self.controller.env.secret)
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

    def __clear_entry(self) -> None:
        self.username.set("")
        self.secret.set("")
        self.tsgId.set("")
        self.status.set("")
        self.workingLabel.configure(require_redraw=True)

    def __lock_creds(self) -> None:
        self.nameField.configure(state=ctk.DISABLED)
        self.secretField.configure(state=ctk.DISABLED)
        self.tsgIdField.configure(state=ctk.DISABLED)
        self.clearButton.configure(state=ctk.DISABLED)
        self.logInButton.configure(state=ctk.DISABLED)

    def login(self) -> None:
        """Handle user login and token refresh scheduling."""
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
            login_res = auth.request()["data"]
            profile = Profile(bearer_token=login_res["access_token"])
            profile_res = profile.request()["data"]
            self.controller.auth = AuthenticationProfile(
                access_token=login_res["access_token"],
                scope=login_res["scope"],
                expire_in=login_res["expires_in"] * 995,
                tenant_id=profile_res["tenant_id"],
                session_id=profile_res["session_id"],
            )
            self.status.set("Login Success")
            self.master.activate_menu()
            self.__lock_creds()
            # Persist credentials and preference if enabled
            self._persist_credentials()
            Thread(
                target=self.after,
                args=(
                    # (self.controller.authRes.get("data").get("expires_in", 60 * 15) - 1)
                    self.controller.auth.expire_in,
                    self.refresh_token,
                ),
                daemon=True,
            ).start()
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
            self.status.set("Logging In Failed")

    def refresh_token(self) -> None:
        """Refresh bearer token before expiry."""
        if not all([self.username.get(), self.secret.get(), self.tsgId.get()]):
            return None
        try:
            auth = Login(
                username=self.username.get(),
                secret=self.secret.get(),
                tsg_id=self.tsgId.get(),
            )
            login_res = auth.request()["data"]
            profile = Profile(bearer_token=self.controller.auth.access_token)
            profile_res = profile.request()["data"]
            self.controller.auth = AuthenticationProfile(
                access_token=login_res["access_token"],
                scope=login_res["scope"],
                expire_in=login_res["expires_in"] * 995,
                tenant_id=profile_res["tenant_id"],
                session_id=profile_res["session_id"],
            )
        except Exception as error:
            messagebox.showerror(title="Something Went Wrong!", message=error)
            return None
        self.after(self.controller.auth.expire_in, self.refresh_token)

    def _persist_credentials(self) -> None:
        """Persist current credentials to config if 'Remember me' is enabled.

        Uses DPAPI to encrypt the secret. Updates the app's in-memory config
        first, then saves to disk. Errors are ignored to avoid blocking UI.
        """
        try:
            # Update remember_me preference
            self.controller.config.setdefault("ui", {})["remember_me"] = bool(self.rememberMe.get())
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
