import re
import pandas as pd
from statistics import mean


def average_per_site(tenant: pd.Series, rawData: dict) -> pd.Series:
    res = tenant.copy()
    for metric in rawData["data"]["metrics"]:
        res[metric["series"][0]["name"]] = mean(
            point["value"] for point in metric["series"][0]["data"][0]["datapoints"]
        )
    res["ipv4_port1"] = next(
        (
            item.get("ipv4_config", {}).get("static_config", {}).get("address")
            for item in rawData["data"]["interfaces"]
            if item.get("name") == "1"
            and item.get("ipv4_config", {}).get("type", None) == "static"
        ),
        None,
    )
    res["ipv4_port2"] = next(
        (
            item.get("ipv4_config", {}).get("static_config", {}).get("address")
            for item in rawData["data"]["interfaces"]
            if item.get("name") == "2"
            and item.get("ipv4_config", {}).get("type", None) == "static"
        ),
        None,
    )

    return res


def filter_interfaces(
    interfaces: list[dict], site_name: str, *args, **kwargs
) -> list[str]:

    filter = kwargs.get("filter", {})
    if not isinstance(filter, list):
        filter = [
            ("^DC-|^DRC", "^13"),
            ("^DCI-", "^13$|^14"),
        ]
    for name_pattern, interface_pattern in filter:
        if re.search(re.compile(name_pattern), site_name):
            return [
                interface.get("id")
                for interface in interfaces
                if re.search(re.compile(interface_pattern), interface.get("name", ""))
            ]
    return [
        interface.get("id")
        for interface in interfaces
        if re.search(re.compile("^1$"), interface.get("name", ""))
    ]
