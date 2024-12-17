import requests
from json import dumps


class SiteOfTenant:
    def __init__(
        self, bearer_token: str, base_url: str = "https://api.sase.paloaltonetworks.com"
    ) -> None:
        self.baseUrl = base_url
        self.bearerToken = bearer_token

    def request(self) -> dict:
        try:
            res = requests.get(
                url=f"{self.baseUrl}/sdwan/v4.8/api/sites",
                headers={
                    "Accept": "application/json",
                    "User-Agent": "NTTIndonesia-PANBA/1.2.5",
                    "Authorization": f"Bearer {self.bearerToken}",
                },
            )
            res.raise_for_status()
            return {"status": res.status_code, "data": res.json()}
        except requests.exceptions.HTTPError as httpError:
            print(f"Http Error {httpError} {res.headers} {res.json()}")
            raise
        except requests.exceptions.RequestException as requestException:
            print(f"Something Went Wrong {requestException} {res}")
            raise


class ElementOfTenant:
    def __init__(
        self, bearer_token: str, base_url: str = "https://api.sase.paloaltonetworks.com"
    ) -> None:
        self.baseUrl = base_url
        self.bearerToken = bearer_token

    def request(self):
        try:
            res = requests.get(
                url=f"{self.baseUrl}/sdwan/v3.1/api/elements",
                headers={
                    "Accept": "application/json",
                    "User-Agent": "NTTIndonesia-PANBA/1.2.5",
                    "Authorization": f"Bearer {self.bearerToken}",
                },
            )
            res.raise_for_status()
            return {"status": res.status_code, "data": res.json()}
        except requests.exceptions.HTTPError as httpError:
            print(f"Http Error {httpError} {res.headers} {res.json()}")
            raise
        except requests.exceptions.RequestException as requestException:
            print(f"Something Went Wrong {requestException} {res}")
            raise


class RemoteNetworkBandwidth:
    def __init__(
        self,
        bearer_token: str,
        body: dict,
        base_url: str = "https://pa-id01.api.prismaaccess.com",
    ) -> None:
        self.body = body
        self.baseUrl = base_url
        self.bearerToken = bearer_token

    def request(self):
        try:
            res = requests.post(
                url=f"{self.baseUrl}/api/sase/v3.0/resource/query/sites/rn_list",
                data=dumps(self.body),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "NTTIndonesia-PANBA/1.2.5",
                    "Authorization": f"Bearer {self.bearerToken}",
                },
            )
            res.raise_for_status()
            return {"status": res.status_code, "data": res.json()}
        except requests.exceptions.HTTPError as httpError:
            print(f"Http Error {httpError} {res.headers} {res.json()}")
            raise
        except requests.exceptions.RequestException as requestException:
            print(f"Something Went Wrong {requestException} {res}")
            raise
