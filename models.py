from typing import Optional
from pydantic import BaseModel, StrictBool
from customtkinter import CTkFrame
from helper.config import Config


class EnvironmentVariables(BaseModel):
    """
    Model for environment variables used by the application.

    Attributes:
        userName (Optional[str]): The username provided as an environment variable.
        secret (Optional[str]): The secret key or token provided as an environment variable.
        tsgId (Optional[str]): The TSg ID provided as an environment variable.
        dev (StrictBool): Flag indicating if the current environment is for development.
    """

    userName: Optional[str] = None
    secret: Optional[str] = None
    tsgId: Optional[str] = None
    dev: StrictBool = False


class ViewsMenuItem(BaseModel):
    """
    Represents an entry in the application’s views menu.

    Attributes:
        name (str): The display name of the menu item.
        view_class (type[CTkFrame]): The frame class to instantiate when this menu item is selected.
        is_active (StrictBool): Flag indicating if this menu item is currently active. Defaults to False.
        is_deprecated (StrictBool): Flag indicating if this menu item is deprecated and should not be used. Defaults to False.
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


class AppController(BaseModel):
    """
    AppController orchestrates the core components of the application.

    Attributes:
        env (EnvironmentVariables): Holds environment-specific variables and settings.
        config (Config): Contains application configuration parameters.
        auth (AuthenticationProfile): Manages authentication credentials and behavior.
    """

    env: EnvironmentVariables
    config: Config
    auth: Optional[AuthenticationProfile]
