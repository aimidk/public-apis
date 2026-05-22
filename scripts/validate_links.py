#!/usr/bin/env python3
"""Script to validate links in the public-apis README.md file.

This script parses the README.md, extracts all URLs, and checks
whether they are accessible by making HTTP requests.
"""

import re
import sys
import time
import argparse
from typing import Optional

import requests

# Timeout for each HTTP request in seconds
REQUEST_TIMEOUT = 10

# Delay between requests to avoid rate limiting
REQUEST_DELAY = 0.5

# HTTP status codes considered as valid/accessible
VALID_STATUS_CODES = {200, 201, 301, 302, 303, 307, 308}

# Regex pattern to extract markdown links
URL_PATTERN = re.compile(r'https?://[^\s\)\]>"]+', re.IGNORECASE)


def extract_urls_from_file(filepath: str) -> list[str]:
    """Extract all URLs from a markdown file.

    Args:
        filepath: Path to the markdown file.

    Returns:
        A list of unique URLs found in the file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)

    urls = URL_PATTERN.findall(content)
    # Remove trailing punctuation that may have been captured
    urls = [url.rstrip('.,;') for url in urls]
    return list(dict.fromkeys(urls))  # Deduplicate while preserving order


def check_url(url: str, session: requests.Session) -> tuple[str, int, Optional[str]]:
    """Check if a URL is accessible.

    Args:
        url: The URL to check.
        session: A requests Session object for connection reuse.

    Returns:
        A tuple of (url, status_code, error_message).
        status_code is -1 and error_message is set if the request fails.
    """
    try:
        response = session.head(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            headers={'User-Agent': 'public-apis-link-validator/1.0'}
        )
        return (url, response.status_code, None)
    except requests.exceptions.ConnectionError as e:
        return (url, -1, f"Connection error: {e}")
    except requests.exceptions.Timeout:
        return (url, -1, "Request timed out")
    except requests.exceptions.RequestException as e:
        return (url, -1, f"Request failed: {e}")


def validate_links(filepath: str, verbose: bool = False) -> bool:
    """Validate all links found in the given file.

    Args:
        filepath: Path to the file containing links to validate.
        verbose: If True, print status for every URL checked.

    Returns:
        True if all links are valid, False otherwise.
    """
    urls = extract_urls_from_file(filepath)
    print(f"Found {len(urls)} unique URLs in '{filepath}'.\n")

    failed_links = []

    with requests.Session() as session:
        for i, url in enumerate(urls, start=1):
            url_str, status_code, error = check_url(url, session)

            if status_code in VALID_STATUS_CODES:
                if verbose:
                    print(f"[{i}/{len(urls)}] OK ({status_code}): {url_str}")
            else:
                reason = error if error else f"HTTP {status_code}"
                print(f"[{i}/{len(urls)}] FAILED ({reason}): {url_str}")
                failed_links.append((url_str, reason))

            time.sleep(REQUEST_DELAY)

    print(f"\n--- Validation Summary ---")
    print(f"Total URLs checked : {len(urls)}")
    print(f"Passed             : {len(urls) - len(failed_links)}")
    print(f"Failed             : {len(failed_links)}")

    if failed_links:
        print("\nFailed URLs:")
        for url, reason in failed_links:
            print(f"  - {url} ({reason})")
        return False

    print("\nAll links are valid!")
    return True


def main() -> None:
    """Entry point for the link validation script."""
    parser = argparse.ArgumentParser(
        description="Validate HTTP links in a markdown file."
    )
    parser.add_argument(
        'filepath',
        nargs='?',
        default='README.md',
        help="Path to the markdown file to validate (default: README.md)"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Print status for every URL, not just failures"
    )
    args = parser.parse_args()

    success = validate_links(args.filepath, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
