"""Helper functions for processing raw data into structured formats."""

import ipaddress
import re
from pathlib import Path
from statistics import mean
from uuid import uuid4

import networkx
import pandas as pd


def average_per_site(tenant: pd.Series, rawData: dict) -> pd.Series:
    """Calculate average metrics per site and extract network interface configurations.

    This function processes raw data to compute average values for various metrics
    and extracts IPv4 addresses for specific network interfaces (port1 and port2).

    Args:
        tenant (pd.Series): A pandas Series containing tenant information that will be
            copied and extended with calculated metrics and interface data.
        rawData (dict): A dictionary containing raw data with the following structure:
            - "data": dict
                - "metrics": list of dicts, each containing:
                    - "series": list with at least one dict containing:
                        - "name": str, metric name
                        - "data": list with at least one dict containing:
                            - "datapoints": list of dicts with "value" keys
                - "interfaces": list of dicts, each containing:
                    - "name": str, interface identifier
                    - "ipv4_config": dict (optional) with:
                        - "type": str, configuration type
                        - "static_config": dict with "address" key
    Returns:
        pd.Series: A copy of the input tenant Series extended with:
            - Average values for each metric (keyed by metric name)
            - "ipv4_port1": IPv4 address of interface "1" with static config, or None
            - "ipv4_port2": IPv4 address of interface "2" with static config, or None
    Example:
        >>> tenant_data = pd.Series({"site_id": "123", "name": "Site A"})
        >>> raw_data = {
        ...     "data": {
        ...         "metrics": [{
        ...             "series": [{
        ...                 "name": "bandwidth",
        ...                 "data": [{"datapoints": [{"value": 100}, {"value": 200}]}]
        ...             }]
        ...         }],
        ...         "interfaces": [
        ...             {"name": "1", "ipv4_config": {"type": "static", "static_config": {"address": "192.168.1.1"}}},
        ...             {"name": "2", "ipv4_config": {"type": "static", "static_config": {"address": "192.168.1.2"}}}
        ...         ]
        ...     }
        ... }
        >>> result = average_per_site(tenant_data, raw_data)
    """
    res = tenant.copy()
    for metric in rawData["data"]["metrics"]:
        res[metric["series"][0]["name"]] = mean(
            point["value"] for point in metric["series"][0]["data"][0]["datapoints"]
        )
    res["ipv4_port1"] = next(
        (
            item.get("ipv4_config", {}).get("static_config", {}).get("address")
            for item in rawData["data"]["interfaces"]
            if item.get("name") == "1" and item.get("ipv4_config", {}).get("type", None) == "static"
        ),
        None,
    )
    res["ipv4_port2"] = next(
        (
            item.get("ipv4_config", {}).get("static_config", {}).get("address")
            for item in rawData["data"]["interfaces"]
            if item.get("name") == "2" and item.get("ipv4_config", {}).get("type", None) == "static"
        ),
        None,
    )

    return res


def filter_interfaces(interfaces: list[dict], site_name: str, *args, **kwargs) -> list[str]:
    """Filter network interfaces based on site name and interface name patterns.

    This function applies regex pattern matching to filter interfaces based on the site name
    and interface names. It uses a list of tuples containing name patterns and interface patterns
    to determine which interfaces to include.

    Args:
        interfaces (list[dict]): A list of interface dictionaries, where each dictionary
            should contain 'id' and 'name' keys.
        site_name (str): The name of the site to match against the filter patterns.
        *args: Variable length argument list (unused).
        **kwargs: Arbitrary keyword arguments. Supports:
            - filter (list, optional): A list of tuples where each tuple contains
                (name_pattern, interface_pattern). If not provided or not a list,
                defaults to [("^DC-|^DRC", "^13"), ("^DCI-", "^13$|^14")].

    Returns:
        list[str]: A list of interface IDs that match the filter criteria. If no filter
            matches the site name, returns interfaces matching the pattern "^1$".

    Example:
        >>> interfaces = [
        ...     {"id": "1", "name": "13"},
        ...     {"id": "2", "name": "14"},
        ...     {"id": "3", "name": "1"}
        ... ]
        >>> filter_interfaces(interfaces, "DC-Site1")
        ['1']
        >>> filter_interfaces(interfaces, "Unknown-Site")
        ['3']

    Note:
        - All regex patterns are pre-compiled for performance.
        - The function returns immediately after finding the first matching site pattern.
        - If no site pattern matches, a fallback pattern "^1$" is used.
    """
    filter = kwargs.get("filter", {})
    if not isinstance(filter, list):
        filter = [
            ("^DC-|^DRC", "^13"),
            ("^DCI-", "^13$|^14"),
        ]
    # Pre-compile all patterns in filter
    compiled_filter = [
        (re.compile(name_pattern), re.compile(interface_pattern)) for name_pattern, interface_pattern in filter
    ]
    for name_regex, interface_regex in compiled_filter:
        if name_regex.search(site_name):
            return [
                interface.get("id") for interface in interfaces if interface_regex.search(interface.get("name", ""))
            ]
    # Pre-compile fallback pattern
    fallback_regex = re.compile("^1$")
    return [interface.get("id") for interface in interfaces if fallback_regex.search(interface.get("name", ""))]


def load_topology(file_path: Path) -> networkx.Graph:
    """Load network topology from a JSON file and construct a NetworkX graph.

    This function parses a JSON file containing network topology information and creates
    a graph representation where nodes represent network gates and zones, and edges
    represent connections between them.

    Args:
        file_path (Path): Path to the JSON file containing the topology data.
            The JSON file should have the following structure:
            - "physicals": A dict mapping device names to their virtual systems (vsys)
            - "connections": A list of tuples representing external connections between nodes
    Returns:
        networkx.Graph: A graph object with the following node types:
            - "gate" nodes: Representing network gates with attributes:
                - type: "gate"
                - device: The device name
                - vsys: The virtual system name
                - common_name: The gate's short name
            - "zones" nodes: Representing zone collections with attributes:
                - type: "zones"
                - device: The device name
                - vsys: The virtual system name
                - common_name: "zones"
                - value_list: List of zone names
            And the following edge types:
            - "internal": Edges connecting all gates and zones within the same vsys
            - "external": Edges defined in the connections list
    Note:
        - Devices named "other" or vsys without zones are not connected to zone nodes
        - Internal edges are created between all pairs of gates and the zones node
        within each vsys using combinations
    """
    import json
    from itertools import combinations

    raw_data: dict = json.loads(open(file_path).read())
    G = networkx.Graph()

    physical: dict = raw_data.get("physicals", {})
    for device_name, devices in physical.items():
        for vsys_name, vsys in devices.items():
            gates = [f"{device_name}.{vsys_name}.{gate}" for gate in vsys.get("gates", [])]
            for gate in gates:
                G.add_node(
                    gate,
                    type="gate",
                    device=device_name,
                    vsys=vsys_name,
                    common_name=gate.split(".")[-1],
                )
            if device_name == "other" or len(vsys.get("zones", [])) == 0:
                continue
            G.add_node(
                f"{device_name}.{vsys_name}.zones",
                type="zones",
                device=device_name,
                vsys=vsys_name,
                common_name="zones",
                value_list=vsys.get("zones", []),
            )
            G.add_edges_from(combinations(gates + [f"{device_name}.{vsys_name}.zones"], 2), type="internal")

    connections: list = raw_data.get("connections", [])
    for conn in connections:
        G.add_edge(*conn, type="external")

    return G


def splice_ip(row_input: pd.Series, column: str = "Segment") -> pd.Series:
    """
    Convert IP address, CIDR notation, or IP range to integer start and end values.

    This function processes different IP address formats and converts them to their
    integer representations for comparison and analysis purposes.

    Args:
        row_input (pd.Series): A pandas Series containing the IP address information.
        column (str, optional): The name of the column containing the IP data.
            Defaults to "Segment".

    Returns:
        pd.Series: A Series with two elements:
            - First element: Integer representation of the start IP address
            - Second element: Integer representation of the end IP address
            Returns [-1, -1] if the input is invalid.

    Supported Formats:
        - CIDR notation (e.g., "192.168.1.0/24"): Returns network and broadcast addresses
        - IP range (e.g., "192.168.1.1-192.168.1.255"): Returns start and end IPs
        - Single IP (e.g., "192.168.1.1"): Returns the same IP for both start and end

    Examples:
        >>> row = pd.Series({"Segment": "192.168.1.0/24"})
        >>> splice_ip(row)
        0    3232235776
        1    3232236031
        dtype: int64

        >>> row = pd.Series({"Segment": "192.168.1.1-192.168.1.10"})
        >>> splice_ip(row)
        0    3232235777
        1    3232235786
        dtype: int64

        >>> row = pd.Series({"Segment": "192.168.1.1"})
        >>> splice_ip(row)
        0    3232235777
        1    3232235777
        dtype: int64

    Raises:
        ValueError: Caught internally and returns [-1, -1] for invalid IP formats.
    """
    import re

    subnet = row_input.get(column, "").replace(" ", "")
    regex_string = re.compile(r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\.)")
    find_domains = re.compile(r"(^\w+\.|https?:\/\/)")
    try:
        if not regex_string.match(subnet) and find_domains.match(subnet):
            return pd.Series([0, 0])
        if "/" in subnet:
            net = ipaddress.ip_network(subnet, strict=False)
            return pd.Series([int(net.network_address), int(net.broadcast_address)])
        if "-" in subnet:
            start, end = subnet.split("-")
            if start > end:
                raise ValueError("Start IP is greater than End IP in range.")
            return pd.Series([int(ipaddress.ip_address(start)), int(ipaddress.ip_address(end))])
        ip = int(ipaddress.ip_address(subnet))
        return pd.Series([ip, ip])
    except ValueError:
        return pd.Series([-1, -1])


def find_slice(row_input: pd.Series, db: pd.DataFrame) -> pd.Series:
    """Find firewall zones for source and destination IP ranges.

    Matches source and destination IP ranges from the input row against IP ranges
    in the database to determine the corresponding firewall and virtual system zones.

    Args:
        row_input (pd.Series): A Series containing IP range information with keys:
            - "src_start_ip": Start IP address (as integer) for source
            - "src_end_ip": End IP address (as integer) for source
            - "dst_start_ip": Start IP address (as integer) for destination
            - "dst_end_ip": End IP address (as integer) for destination
        db (pd.DataFrame): Database containing IP range mappings with columns:
            - "start_ip": Start of IP range (as integer)
            - "end_ip": End of IP range (as integer)
            - "Firewall1": Firewall identifier
            - "VSys": Virtual system identifier

    Returns:
        pd.Series: A Series containing:
            - First element: UUID (uuid.UUID)
            - Second element: Zone path for source (str, e.g., "firewall.vsys.zones") or ""
            - Third element: Zone path for destination (str, e.g., "firewall.vsys.zones") or ""

    Example:
        >>> row = pd.Series({"src_start_ip": 3232235776, "src_end_ip": 3232235776,
        ...                  "dst_start_ip": 3232236032, "dst_end_ip": 3232236032})
        >>> db = pd.DataFrame({"start_ip": [3232235776], "end_ip": [3232236031],
        ...                    "Firewall1": ["FW1"], "VSys": ["vsys1"]})
        >>> find_slice(row, db)
        0    <UUID>
        1    FW1.vsys1.zones
        2
        dtype: object
    """
    masks = {
        "source": (db["start_ip"] <= row_input["src_start_ip"]) & (db["end_ip"] >= row_input["src_end_ip"]),
        "destination": (db["start_ip"] <= row_input["dst_start_ip"]) & (db["end_ip"] >= row_input["dst_end_ip"]),
    }
    results = []
    results.insert(0, str(uuid4()))
    if row_input[["src_start_ip", "src_end_ip", "dst_start_ip", "dst_end_ip"]].isin([0, -1]).any():
        results.extend([None, None])
        return pd.Series(results)
    for direction, mask in masks.items():
        matched_rows = db.loc[mask]
        if not matched_rows.empty:
            # Construct the zone path string in the format "Firewall1.VSys.zones"
            # This format can be changed here if the structure changes in the future.
            first_match = matched_rows.iloc[0]
            zone_path = f"{first_match['Firewall1']}.{first_match['VSys']}.{first_match['Zone']}"
            results.append(zone_path)
        else:
            results.append(None)

    return pd.Series(results)
