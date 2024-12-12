import pandas as pd
from statistics import mean


def average_per_site(tenant: pd.Series, rawData: dict) -> pd.Series:
    res = tenant.copy()
    for metric in rawData["data"]["metrics"]:
        res[metric["series"][0]["name"]] = mean(
            point["value"] for point in metric["series"][0]["data"][0]["datapoints"]
        )
    return res
