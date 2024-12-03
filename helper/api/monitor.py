import json
import requests


class SysMetric:
    def __init__(
        self,
        bearer_token: str,
        body: dict,
        base_url: str = "https://api.sase.paloaltonetworks.com",
    ) -> None:
        self.baseUrl = base_url
        self.body = body
        self.bearerToken = bearer_token

    def request(self) -> dict:
        try:
            res = requests.post(
                url=f"{self.baseUrl}/sdwan/monitor/v2.3/api/monitor/sys_metrics",
                data=json.dumps(self.body),
                # data='{"start_time":"2024-04-19T06:05:00.000Z","end_time":"2024-04-19T06:34:00.000Z","interval":"1min","metrics":[{"name":"MemoryUsage","statistics":["average"],"unit":"percentage"},{"name":"CPUUsage","statistics":["average"],"unit":"percentage"},{"name":"DiskUsage","statistics":["average"],"unit":"percentage"}],"filter":{"site":["1696663173285010327"],"element":["1696666533144019927"]}}',
                headers={
                    "X-PANW-Region": "sg",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "NTTIndonesia-PANBA/1.1.0",
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
