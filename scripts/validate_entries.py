"""Validate entries in the public-apis README.md file.

This script checks that all API entries in the README follow the expected
format and contain required fields (API name, description, Auth, HTTPS, CORS).
"""

import re
import sys
from pathlib import Path

# Expected table header format
TABLE_HEADER = "| API | Description | Auth | HTTPS | CORS |"
TABLE_SEPARATOR = "|---|---|---|---|---|"

# Valid values for structured columns
VALID_AUTH = {"apiKey", "OAuth", "X-Mashape-Key", "User-Agent", "No", ""}
VALID_HTTPS = {"Yes", "No"}
VALID_CORS = {"Yes", "No", "Unknown"}

# Regex pattern for a table row
ROW_PATTERN = re.compile(
    r"^\|\s*\[?(.+?)\]?(?:\(.*?\))?\s*"
    r"\|\s*(.+?)\s*"
    r"\|\s*(`[^`]*`|No|)\s*"
    r"\|\s*(Yes|No)\s*"
    r"\|\s*(Yes|No|Unknown)\s*\|$"
)


def parse_table_rows(lines: list[str]) -> list[tuple[int, list[str]]]:
    """Extract table data rows (excluding headers and separators).

    Args:
        lines: All lines from the README file.

    Returns:
        List of (line_number, columns) tuples for each data row.
    """
    rows = []
    in_table = False

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if TABLE_HEADER in stripped:
            in_table = True
            continue

        if in_table and stripped.startswith("|---"):
            continue

        if in_table and stripped.startswith("|") and stripped.endswith("|"):
            # Split columns and strip whitespace
            cols = stripped.split("|")
            cols = [c.strip() for c in cols[1:-1]]  # Remove first and last empty splits
            rows.append((i, cols))
        elif in_table and not stripped.startswith("|"):
            in_table = False

    return rows


def validate_row(line_num: int, cols: list[str]) -> list[str]:
    """Validate a single table row's columns.

    Args:
        line_num: The line number in the source file.
        cols: The column values for this row.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    if len(cols) != 5:
        errors.append(
            f"Line {line_num}: Expected 5 columns, got {len(cols)}: {cols}"
        )
        return errors

    api_name, description, auth, https, cors = cols

    if not api_name:
        errors.append(f"Line {line_num}: API name is empty.")

    if not description:
        errors.append(f"Line {line_num}: Description is empty for '{api_name}'.")

    # Auth can be wrapped in backticks or be 'No'
    auth_value = auth.strip("`")
    if auth_value not in VALID_AUTH:
        errors.append(
            f"Line {line_num}: Invalid Auth value '{auth}' for '{api_name}'. "
            f"Expected one of: {VALID_AUTH}"
        )

    if https not in VALID_HTTPS:
        errors.append(
            f"Line {line_num}: Invalid HTTPS value '{https}' for '{api_name}'. "
            f"Expected one of: {VALID_HTTPS}"
        )

    # Note: 'Unknown' is allowed for CORS since many APIs don't document it clearly
    if cors not in VALID_CORS:
        errors.append(
            f"Line {line_num}: Invalid CORS value '{cors}' for '{api_name}'. "
            f"Expected one of: {VALID_CORS}"
        )

    return errors
