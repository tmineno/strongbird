#!/usr/bin/env python3
"""Batch file reader for processing URLs from text files."""

from pathlib import Path
from typing import List


class BatchFileReader:
    """Reader for batch files containing URLs with optional globbing patterns."""

    def __init__(self):
        """Initialize the batch file reader."""
        pass

    def read_urls_from_file(self, file_path: str) -> List[str]:
        """
        Read URLs from a batch file.

        Args:
            file_path: Path to the batch file

        Returns:
            List of URLs (one per line, comments and empty lines filtered out)

        Raises:
            FileNotFoundError: If the batch file doesn't exist
            IOError: If the file cannot be read
        """
        batch_path = Path(file_path)

        if not batch_path.exists():
            raise FileNotFoundError(f"Batch file not found: {file_path}")

        if not batch_path.is_file():
            raise IOError(f"Path is not a file: {file_path}")

        try:
            with batch_path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise IOError(f"Failed to read batch file {file_path}: {e}")

        urls = []
        for line_num, line in enumerate(lines, 1):
            # Strip whitespace
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip comment lines (starting with #)
            if line.startswith("#"):
                continue

            # Basic URL validation - must start with http/https or be a file path
            if not (
                line.startswith(("http://", "https://", "file://"))
                or line.startswith("/")
            ):
                # Log warning but continue processing
                print(f"Warning: Line {line_num} doesn't look like a URL: {line}")
                continue

            urls.append(line)

        return urls

    def validate_batch_file(self, file_path: str) -> tuple[bool, str]:
        """
        Validate a batch file before processing.

        Args:
            file_path: Path to the batch file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            urls = self.read_urls_from_file(file_path)
            if not urls:
                return False, "Batch file contains no valid URLs"
            return True, f"Found {len(urls)} URLs in batch file"
        except FileNotFoundError as e:
            return False, str(e)
        except IOError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error validating batch file: {e}"
