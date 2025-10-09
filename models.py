"""Pydantic models for application configuration and state management."""

from pathlib import Path
from typing import Literal, Optional

from customtkinter import CTkFrame
from pydantic import BaseModel, StrictBool


class EnvironmentVariables(BaseModel):
    """
    Model for environment variables used by the application.

    Attributes:
        userName (Optional[str]): The username provided as an environment variable.
        secret (Optional[str]): The secret key or token provided as an environment variable.
        tsgId (Optional[str]): The TSg ID provided as an environment variable.
        first_view (Optional[str]): The default view to display on application start.
        dev (StrictBool): Flag indicating if the current environment is for development.
    """

    userName: Optional[str] = None
    secret: Optional[str] = None
    tsgId: Optional[str] = None
    first_view: Optional[str] = None
    dev: StrictBool = False


class ViewsMenuItem(BaseModel):
    """
    Represents an entry in the application’s views menu.

    Attributes:
        name (str): The display name of the menu item.
        view_class (type[CTkFrame]): The frame class to instantiate when this menu item is selected.
        is_active (StrictBool): Flag indicating if this menu item is currently active. Defaults to False.
        is_deprecated (StrictBool): Flag indicating if this menu item is deprecated and should not be used.
                                    Defaults to False.
    """

    name: str
    view_class: type[CTkFrame]
    is_active: StrictBool = False
    is_deprecated: StrictBool = False


class AuthenticationProfile(BaseModel):
    """
    AuthenticationProfile represents the authentication context for a user session.

    Attributes:
        access_token (str): The OAuth2 access token used for API calls.
        scope (str): Space-separated list of permissions granted to the token.
        expire_in (int): The duration in milliseconds when the access token will expire.
        tenant_id (str): Identifier of the tenant or organization.
        session_id (str): Unique identifier for the authentication session.
    """

    access_token: str
    scope: str
    expire_in: int = 60 * 15 * 995  # Default to 15 minutes in milliseconds
    tenant_id: str
    session_id: str


class LastOpenPath(BaseModel):
    """Model for tracking the last opened file paths.

    Attributes:
        last_open_dir (Optional[Path]): Last directory used for opening files.
        last_export_dir (Optional[Path]): Last directory used for exports.
        last_import_dir (Optional[Path]): Last directory used for importing files.
        last_import_file (Optional[Path]): Last file path selected for import.
        last_import_topology_file (Optional[Path]): Last topology file path selected for import.
        last_import_segment_db_file (Optional[Path]): Last segment database file path selected for import.
    """

    last_open_dir: Optional[Path]
    last_export_dir: Optional[Path]
    last_import_dir: Optional[Path]
    last_import_file: Optional[Path]
    last_import_topology_file: Optional[Path]
    last_import_segment_db_file: Optional[Path]


class UIDefaults(BaseModel):
    """Model for UI configuration overrides.

    Attributes:
        remember_me (StrictBool): Flag to remember user preferences across sessions.
        default_theme (Literal["dark", "light"]): Default theme for the UI, either 'dark' or 'light'.
    """

    remember_me: StrictBool = False
    default_theme: Literal["dark", "light"] = "dark"


class Creds(BaseModel):
    """Authentication profile (username, tenant, secret).

    Attributes:
        username (Optional[str]): Last used username (non-sensitive).
        tsg_id (Optional[str | int]): Tenant/TSG identifier.
        secret_enc (Optional[str]): Base64-encoded DPAPI-protected secret.
    """

    username: Optional[str]
    tsg_id: Optional[str | int]
    secret_enc: Optional[str]


class Config(BaseModel):
    """Top-level configuration shape.

    Attributes:
        version (Optional[str]): Semantic version of the config schema, for future migrations.
        ui (UIDefaults): UI defaults and remember-me flag.
        paths (LastOpenPath): Last used directories.
        auth (Creds): Authentication profile.
    """

    version: Optional[str]
    ui: UIDefaults
    paths: LastOpenPath
    auth: Optional[Creds]


class AppController(BaseModel):
    """
    AppController orchestrates the core components of the application.

    Attributes:
        env (EnvironmentVariables): Holds environment-specific variables and settings.
        config (Config): Contains application configuration parameters.
        auth (Creds): Manages authentication credentials and behavior.
    """

    env: EnvironmentVariables
    config: Config
    auth: Optional[AuthenticationProfile]
