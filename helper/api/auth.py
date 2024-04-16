from requests.auth import HTTPBasicAuth
import requests


class Login:
    """
    Login to API and Get Bearer Token
    """

    def __init__(
        self,
        username: str,
        secret: str,
        tsg_id: int,
        url: str = "https://auth.apps.paloaltonetworks.com/auth/v1/oauth2/access_token",
    ) -> None:
        self.username = username
        self.secret = secret
        self.tsgId = tsg_id
        self.url = url
        self.data = {
            "grant_type": "client_credentials",
            "scope": f"tsg_id:{self.tsgId}",
        }

    def request(self) -> dict:
        try:
            res = requests.post(
                url=self.url,
                data=self.data,
                auth=HTTPBasicAuth(username=self.username, password=self.secret),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "NTTIndonesia-PANBA/0.1.0",
                },
            )
            res.raise_for_status()
            return {"status": res.status_code, "data": res.json()}
        except requests.exceptions.HTTPError as httpError:
            print(f"Http Error {httpError}")
            raise
        except requests.exceptions.RequestException as requestException:
            print(f"Something Went Wrong {requestException} {res}")
            raise


class Profile:
    def __init__(
        self,
        url: str = "https://api.sase.paloaltonetworks.com/sdwan/v2.1/api/profile",
        bearer_token: str = None,
    ) -> None:
        self.url = url
        self.bearerToken = bearer_token

    def request(self):
        try:
            res = requests.get(
                url=self.url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "NTTIndonesia-PANBA/0.1.0",
                    "Authorization": f"Bearer {self.bearerToken}",
                },
            )
            res.raise_for_status()
            return {"status": res.status_code, "data": res.json()}
        except requests.exceptions.HTTPError as httpError:
            print(f"Http Error {httpError}")
            raise
        except requests.exceptions.RequestException as requestException:
            print(f"Something Went Wrong {requestException} {res}")
            raise
