"""Extended File Handler Module."""

from typing import Dict, List, Union

import pandas as pd
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet


def status_coloring_fmt(
    workbook: Workbook, worksheet: Worksheet, data: Union[pd.DataFrame, Dict, List]
) -> tuple[Workbook, Worksheet]:
    """Apply status coloring format to the worksheet based on 'status' column."""
    if isinstance(data, pd.DataFrame) and "status" in data.columns:
        status_formatting: Dict[str, Dict[str, str]] = {
            "success": {"bg_color": "#C6EFCE", "font_color": "#006100"},
            "failed": {"bg_color": "#FFC7CE", "font_color": "#9C0006"},
        }
        for key, fmt in status_formatting.items():
            format_obj = workbook.add_format(fmt)
            worksheet.conditional_format(
                1,
                0,
                len(data),
                len(data.columns) - 1,
                {
                    "type": "cell",
                    "criteria": "equal to",
                    "value": f'"{key}"',
                    "format": format_obj,
                },
            )
    return workbook, worksheet
