"""Unit tests for the S3 pageview reader."""

from __future__ import annotations

import bz2
import datetime
from unittest.mock import MagicMock

import pytest

from poi_people.infrastructure.adapters.s3_pageview_reader import (
    S3ReadError,
    _parse_pageview_line,
    read_pageviews_from_s3,
)


class TestParsePageviewLine:
    """Tests for individual line parsing."""

    def test_standard_wikipedia_line(self) -> None:
        result = _parse_pageview_line("en.wikipedia Barack_Obama 12345 0")
        assert result is not None
        lang, title, views = result
        assert lang == "en"
        assert title == "Barack Obama"
        assert views == 12345

    def test_simple_lang_code(self) -> None:
        result = _parse_pageview_line("en Barack_Obama 500 0")
        assert result is not None
        lang, title, views = result
        assert lang == "en"
        assert views == 500

    def test_non_wikipedia_project_filtered(self) -> None:
        result = _parse_pageview_line("en.wikisource Some_Page 100 0")
        assert result is None

    def test_short_line_returns_none(self) -> None:
        assert _parse_pageview_line("en Barack_Obama") is None

    def test_non_numeric_views_returns_none(self) -> None:
        assert _parse_pageview_line("en Barack_Obama abc 0") is None

    def test_underscores_replaced_with_spaces(self) -> None:
        result = _parse_pageview_line("en.wikipedia J._K._Rowling 800 0")
        assert result is not None
        _, title, _ = result
        assert title == "J. K. Rowling"


class TestReadPageviewsFromS3:
    """Tests for S3 reading with mock boto3."""

    @pytest.fixture
    def title_mapping(self) -> dict[str, str]:
        return {
            "Barack Obama": "Q76",
            "Angela Merkel": "Q567",
            "Lionel Messi": "Q615",
        }

    @pytest.fixture
    def pageview_data(self) -> bytes:
        lines = [
            "en.wikipedia Barack_Obama 12345 0",
            "en.wikipedia Angela_Merkel 5000 0",
            "en.wikipedia Lionel_Messi 8000 0",
            "en.wikipedia Unknown_Person 300 0",
            "de.wikipedia Angela_Merkel 3000 0",
            "fr.wikisource Some_Book 100 0",
        ]
        raw = "\n".join(lines).encode("utf-8")
        return bz2.compress(raw)

    @pytest.fixture
    def mock_s3_client(self, pageview_data: bytes) -> MagicMock:
        client = MagicMock()
        client.get_object.return_value = {"Body": MagicMock(read=MagicMock(return_value=pageview_data))}
        return client

    def test_reads_and_filters_persons(
        self, mock_s3_client: MagicMock, title_mapping: dict[str, str]
    ) -> None:
        records = list(
            read_pageviews_from_s3(
                s3_client=mock_s3_client,
                bucket="poi-pageview-dumps",
                key="pageviews/2026-04-01.bz2",
                date=datetime.date(2026, 4, 1),
                title_to_person_id=title_mapping,
            )
        )

        # Obama, Merkel (en), Messi, Merkel (de) = 4 matching records
        # Unknown_Person and wikisource are filtered
        assert len(records) == 4

        person_ids = {r.person_id for r in records}
        assert "Q76" in person_ids
        assert "Q567" in person_ids
        assert "Q615" in person_ids

    def test_filters_by_target_langs(
        self, mock_s3_client: MagicMock, title_mapping: dict[str, str]
    ) -> None:
        records = list(
            read_pageviews_from_s3(
                s3_client=mock_s3_client,
                bucket="poi-pageview-dumps",
                key="pageviews/2026-04-01.bz2",
                date=datetime.date(2026, 4, 1),
                title_to_person_id=title_mapping,
                target_langs={"en"},
            )
        )

        # Only en records: Obama, Merkel (en), Messi = 3
        assert len(records) == 3
        assert all(r.lang == "en" for r in records)

    def test_s3_error_raises_s3_read_error(self, title_mapping: dict[str, str]) -> None:
        client = MagicMock()
        client.get_object.side_effect = Exception("Access denied")

        with pytest.raises(S3ReadError):
            list(
                read_pageviews_from_s3(
                    s3_client=client,
                    bucket="bad-bucket",
                    key="nonexistent.bz2",
                    date=datetime.date(2026, 4, 1),
                    title_to_person_id=title_mapping,
                )
            )

    def test_records_have_correct_date(
        self, mock_s3_client: MagicMock, title_mapping: dict[str, str]
    ) -> None:
        target_date = datetime.date(2026, 4, 1)
        records = list(
            read_pageviews_from_s3(
                s3_client=mock_s3_client,
                bucket="poi-pageview-dumps",
                key="pageviews/2026-04-01.bz2",
                date=target_date,
                title_to_person_id=title_mapping,
            )
        )

        assert all(r.date == target_date for r in records)

    def test_empty_dump(self, title_mapping: dict[str, str]) -> None:
        client = MagicMock()
        compressed = bz2.compress(b"")
        client.get_object.return_value = {"Body": MagicMock(read=MagicMock(return_value=compressed))}

        records = list(
            read_pageviews_from_s3(
                s3_client=client,
                bucket="poi-pageview-dumps",
                key="empty.bz2",
                date=datetime.date(2026, 4, 1),
                title_to_person_id=title_mapping,
            )
        )
        assert len(records) == 0
