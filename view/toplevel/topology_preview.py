"""Topology preview toplevel window.

Renders a given NetworkX graph using pyvis and embeds the HTML output
inside a Tkinter window via tkinterweb's HtmlFrame.
"""

import tempfile
import webbrowser
from pathlib import Path

import networkx
from pyvis.network import Network


def create_graph_preview(graph: networkx.Graph) -> tuple[int, Path]:
    """Create an interactive graph preview visualization and open it in a web browser.

    This function takes a NetworkX graph and generates an interactive HTML visualization
    using the pyvis Network library. The visualization is saved to a temporary HTML file
    and automatically opened in the user's default web browser.

    Args:
        graph (networkx.Graph): A NetworkX graph object to be visualized.

    Returns:
        tuple[int, Path]: A tuple containing:
            - temp_id (int): The file descriptor of the temporary file created.
            - html_path (Path): Path object pointing to the generated HTML file.

    Notes:
        - The visualization uses pyvis with embedded CDN resources for portability.
        - The graph is displayed with interactive features including filter and select menus.
        - Physics simulation is enabled with a minimum velocity of 0.75.
        - Manipulation mode is enabled, allowing user interaction with the graph.
        - Edge colors inherit from node colors.
        - The HTML file is created in the system's temporary directory with prefix "panba_".

    Side Effects:
        - Creates a temporary HTML file in the system's temp directory.
        - Opens the generated HTML file in a new browser tab.

    Example:
        >>> import networkx as nx
        >>> G = nx.karate_club_graph()
        >>> temp_id, path = create_graph_preview(G)
        >>> # Browser opens with interactive graph visualization
    """
    temp_id, html_path = tempfile.mkstemp(suffix=".html", prefix="panba_")
    nets = Network(
        height="75vh", width="100%", notebook=False, cdn_resources="in_line", filter_menu=True, select_menu=True
    )
    nets.from_nx(nx_graph=graph, edge_scaling=True)
    nets.set_options(
        """
    const options = {
        "nodes": {
            "borderWidth": null,
            "borderWidthSelected": null,
            "opacity": null,
            "size": null
        },
        "edges": {
            "color": {
                "inherit": true
            },
            "selfReferenceSize": null,
            "selfReference": {
                "angle": 0.7853981633974483
            },
            "smooth": {
                "forceDirection": "none"
            }
        },
        "manipulation": {
            "enabled": true
        },
        "physics": {
            "minVelocity": 0.75
        }
    }
    """
    )
    with Path(html_path).open("w", encoding="utf-8") as f:
        f.write(nets.generate_html(notebook=False))
    webbrowser.open_new_tab(url=html_path)

    return temp_id, Path(html_path)
