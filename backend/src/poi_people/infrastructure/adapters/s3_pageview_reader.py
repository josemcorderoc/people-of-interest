"""S3 pageview reader — reads bz2-compressed pageview dumps from S3.

Parses the Wikimedia pageview_complete TSV format and filters to known persons.
"""

from __future__ import annotations

import bz2
import io
import logging
from collections.abc import Iterator

from poi_people.domain.entities.pageview_record import PageviewRecord

logger = logging.getLogger(__name__)


def _parse_pageview_line(line: str) -> tuple[str, str, int] | None:
    """Parse a single line from the Wikimedia pageview_complete dump.

    Format: domain_code page_title count_views total_response_size
    Example: en.wikipedia Barack_Obama 12345 0

    Returns:
        Tuple of (lang, article_title, views) or None if line is invalid.
    """
    parts = line.strip().split(" ")
    if len(parts) < 3:
        return None

    domain_code = parts[0]
    page_title = parts[1]
    try:
        views = int(parts[2])
    except ValueError:
        return None

    # Filter to Wikipedia project (xx.wikipedia or xx)
    if ".wikipedia" in domain_code:
        lang = domain_code.split(".")[0]
    elif "." not in domain_code:
        # Simple language code like "en"
        lang = domain_code
    else:
        # Non-Wikipedia projects (e.g., xx.wikisource)
        return None

    # Decode underscores to spaces for article title matching
    article_title = page_title.replace("_", " ")

    return lang, article_title, views


def read_pageviews_from_s3(
    s3_client,
    bucket: str,
    key: str,
    date,
    title_to_person_id: dict[str, str],
    target_langs: set[str] | None = None,
) -> Iterator[PageviewRecord]:
    """Read and parse a bz2-compressed pageview dump from S3.

    Args:
        s3_client: A boto3 S3 client instance.
        bucket: S3 bucket name.
        key: S3 object key for the dump file.
        date: The date these pageviews cover.
        title_to_person_id: Mapping of article_title -> wikidata_id.
        target_langs: Optional set of language codes to filter to.

    Yields:
        PageviewRecord for each matching person found in the dump.

    Raises:
        S3ReadError: If S3 is unreachable or the object cannot be read.
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
    except Exception as exc:
        logger.error("Failed to read s3://%s/%s: %s", bucket, key, exc)
        raise S3ReadError(f"Failed to read s3://{bucket}/{key}") from exc

    body = response["Body"].read()
    try:
        decompressed = bz2.decompress(body)
    except Exception as exc:
        logger.error("Failed to decompress s3://%s/%s: %s", bucket, key, exc)
        raise S3ReadError(f"Failed to decompress s3://{bucket}/{key}") from exc

    matched = 0
    total_lines = 0

    for line in io.TextIOWrapper(io.BytesIO(decompressed), encoding="utf-8"):
        total_lines += 1
        parsed = _parse_pageview_line(line)
        if parsed is None:
            continue

        lang, article_title, views = parsed

        if target_langs and lang not in target_langs:
            continue

        person_id = title_to_person_id.get(article_title)
        if person_id is None:
            continue

        matched += 1
        yield PageviewRecord(
            person_id=person_id,
            lang=lang,
            date=date,
            views=views,
        )

    logger.info(
        "Processed %d lines from s3://%s/%s, matched %d records",
        total_lines, bucket, key, matched,
    )


class S3ReadError(Exception):
    """Raised when S3 read or decompression fails."""
