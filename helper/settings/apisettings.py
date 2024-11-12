class BWConsSetting:
    rules: list[dict[str, any]] = [
        {
            "property": "event_time",
            "values": int,
        }
    ]
    propState: dict[str, bool] = {
        "site_name": True,
        "edge_location_display_name": True,
        "source_ip": True,
        "site_type": True,
        "destination_ip": True,
        "instance_state": True,
        "compute_location": True,
        "site_all_tunnels": True,
        "bgp_all_tunnels": True,
        "site_aggregate_capacity": True,
        "site_capacity": True,
        "site_state": True,
        "site_state_name": True,
        "site_up_tunnels": True,
        "instance_state_name": True,
        "source_ip_string": True,
        "destination_ip_string": True,
        "site_city": True,
        "site_country": True,
        "bgp_up_tunnels": True,
        "bgp_site_state": True,
        "bgp_site_state_name": True,
        "site_disconnection": True,
        "site_connection_duration": True,
        "peak_throughput": True,
        "avg_throughput": True,
        "median_throughput": True,
    }

    def __init__(self, rules: list[dict[str, any]], properties: list[str]) -> None:
        self.rules = rules
        self.properties = properties
