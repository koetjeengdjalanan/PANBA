import requests
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(
    stop=stop_after_attempt(7),
    wait=wait_exponential(multiplier=1, min=5, max=30),
    reraise=True,
)
def get_all_interfaces(
    bearer_token: str,
    site_id: str,
    element_id: str,
    base_url: str = "https://api.sase.paloaltonetworks.com",
) -> dict:
    res = requests.get(
        url=f"{base_url}/sdwan/v4.21/api/sites/{site_id}/elements/{element_id}/interfaces",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "NTTIndonesia-PANBA/1.2.5",
            "Authorization": f"Bearer {bearer_token}",
        },
    )
    res.raise_for_status()
    return {"status": res.status_code, "data": res.json()}


@retry(
    stop=stop_after_attempt(7),
    wait=wait_exponential(multiplier=1, min=5, max=30),
    reraise=True,
)
def system_metric(
    bearer_token: str,
    body: dict,
    base_url: str = "https://api.sase.paloaltonetworks.com",
) -> dict:
    res = requests.post(
        url=f"{base_url}/sdwan/monitor/v2.3/api/monitor/sys_metrics",
        json=body,
        headers={
            "X-PANW-Region": "sg",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "NTTIndonesia-PANBA/1.2.5",
            "Authorization": f"Bearer {bearer_token}",
        },
    )
    res.raise_for_status()
    return {"status": res.status_code, "data": res.json()}
