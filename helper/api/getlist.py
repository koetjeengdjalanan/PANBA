import requests


class Download:
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
