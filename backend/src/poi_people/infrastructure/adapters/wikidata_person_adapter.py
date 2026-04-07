"""Wikidata person adapter — stream-processes gzipped Wikidata JSON dump.

Extracts human entities (P31=Q5) with birth dates and sitelinks,
mapping occupations to categories via config.
"""

from __future__ import annotations

import datetime
import gzip
import json
import logging
from collections.abc import Iterator
from pathlib import Path

from poi_people.domain.entities.person import Gender, Person, PersonCategory
from poi_people.infrastructure.config.models import PersonCategoryMapping

logger = logging.getLogger(__name__)

# Wikidata property IDs
P31_INSTANCE_OF = "P31"
Q5_HUMAN = "Q5"
P106_OCCUPATION = "P106"
P18_IMAGE = "P18"
P21_GENDER = "P21"
P27_NATIONALITY = "P27"
P569_BIRTH_DATE = "P569"
P570_DEATH_DATE = "P570"

# Gender QID mapping
GENDER_MAP: dict[str, Gender] = {
    "Q6581097": "male",
    "Q6581072": "female",
}


def _get_claim_values(entity: dict, prop: str) -> list[dict]:
    """Extract mainsnak datavalues for a property from Wikidata claims."""
    claims = entity.get("claims", {}).get(prop, [])
    result = []
    for claim in claims:
        mainsnak = claim.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        if datavalue:
            result.append(datavalue)
    return result


def _get_entity_id_values(entity: dict, prop: str) -> list[str]:
    """Extract Q-IDs for entity-valued properties."""
    ids = []
    for dv in _get_claim_values(entity, prop):
        value = dv.get("value", {})
        if isinstance(value, dict) and value.get("entity-type") == "item":
            ids.append(f"Q{value['numeric-id']}")
    return ids


def _is_human(entity: dict) -> bool:
    """Check if the entity is an instance of human (P31=Q5)."""
    return Q5_HUMAN in _get_entity_id_values(entity, P31_INSTANCE_OF)


def _parse_date(entity: dict, prop: str) -> datetime.date | None:
    """Parse a Wikidata time value to a Python date."""
    for dv in _get_claim_values(entity, prop):
        value = dv.get("value", {})
        if isinstance(value, dict) and "time" in value:
            time_str = value["time"]
            # Wikidata format: +YYYY-MM-DDT00:00:00Z
            try:
                date_part = time_str.lstrip("+").split("T")[0]
                return datetime.date.fromisoformat(date_part)
            except (ValueError, IndexError):
                continue
    return None


def _get_label(entity: dict, lang: str = "en") -> str | None:
    """Get entity label for a specific language."""
    labels = entity.get("labels", {})
    label_obj = labels.get(lang, {})
    return label_obj.get("value")


def _get_labels(entity: dict, languages: list[str]) -> dict[str, str]:
    """Get labels for multiple languages."""
    labels = entity.get("labels", {})
    result = {}
    for lang in languages:
        label_obj = labels.get(lang, {})
        value = label_obj.get("value")
        if value:
            result[lang] = value
    return result


def _get_sitelinks(entity: dict, languages: list[str]) -> dict[str, str]:
    """Get Wikipedia article titles from sitelinks."""
    sitelinks = entity.get("sitelinks", {})
    result = {}
    for lang in languages:
        site_key = f"{lang}wiki"
        site_obj = sitelinks.get(site_key, {})
        title = site_obj.get("title")
        if title:
            result[lang] = title
    return result


def _get_image_filename(entity: dict) -> str | None:
    """Extract image filename from P18."""
    for dv in _get_claim_values(entity, P18_IMAGE):
        value = dv.get("value")
        if isinstance(value, str):
            return value
    return None


def _get_gender(entity: dict) -> Gender:
    """Extract gender from P21."""
    gender_ids = _get_entity_id_values(entity, P21_GENDER)
    for gid in gender_ids:
        if gid in GENDER_MAP:
            return GENDER_MAP[gid]
    if gender_ids:
        return "other"
    return "unknown"


def _get_nationality(entity: dict) -> str | None:
    """Extract first nationality label from P27."""
    nationality_ids = _get_entity_id_values(entity, P27_NATIONALITY)
    if nationality_ids:
        # Return the QID; resolving to label would require another lookup
        return nationality_ids[0]
    return None


def _resolve_category(
    occupation_qids: list[str], category_mapping: PersonCategoryMapping
) -> PersonCategory:
    """Resolve occupation QIDs to a person category using the config mapping."""
    for qid in occupation_qids:
        cat = category_mapping.resolve(qid)
        if cat != "other":
            return cat  # type: ignore[return-value]
    return "other"


def parse_entity(
    entity: dict,
    languages: list[str],
    category_mapping: PersonCategoryMapping,
) -> Person | None:
    """Parse a single Wikidata entity JSON object into a Person.

    Returns None if the entity is not a human, lacks birth date, or lacks sitelinks.
    """
    if entity.get("type") != "item":
        return None

    if not _is_human(entity):
        return None

    birth_date = _parse_date(entity, P569_BIRTH_DATE)
    if birth_date is None:
        return None

    article_titles = _get_sitelinks(entity, languages)
    if not article_titles:
        return None

    wikidata_id = entity.get("id", "")
    if not wikidata_id:
        return None

    # Get name (prefer English label, fall back to first available)
    name = _get_label(entity, "en")
    if not name:
        names = _get_labels(entity, languages)
        name = next(iter(names.values()), None)
    if not name:
        return None

    names_by_lang = _get_labels(entity, languages)
    occupation_qids = _get_entity_id_values(entity, P106_OCCUPATION)
    category = _resolve_category(occupation_qids, category_mapping)

    return Person(
        wikidata_id=wikidata_id,
        name=name,
        names_by_lang=names_by_lang,
        article_titles=article_titles,
        category=category,
        birth_date=birth_date,
        death_date=_parse_date(entity, P570_DEATH_DATE),
        nationality=_get_nationality(entity),
        occupations=[qid for qid in occupation_qids],
        image_filename=_get_image_filename(entity),
        gender=_get_gender(entity),
    )


def stream_persons_from_dump(
    dump_path: Path,
    languages: list[str],
    category_mapping: PersonCategoryMapping,
) -> Iterator[Person]:
    """Stream Person entities from a gzipped Wikidata JSON dump.

    The dump is expected to be a gzipped JSON array (one entity per line,
    opening/closing brackets on first/last lines).

    Args:
        dump_path: Path to the .json.gz Wikidata dump file.
        languages: Language edition codes to extract sitelinks for.
        category_mapping: P106 occupation mapping for category resolution.

    Yields:
        Person domain objects for qualifying entities.
    """
    count = 0
    yielded = 0

    with gzip.open(dump_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip().rstrip(",")
            if line in ("", "[", "]"):
                continue

            count += 1
            if count % 500_000 == 0:
                logger.info("Processed %d entities, yielded %d persons", count, yielded)

            try:
                entity = json.loads(line)
            except json.JSONDecodeError:
                continue

            person = parse_entity(entity, languages, category_mapping)
            if person is not None:
                yielded += 1
                yield person

    logger.info("Finished: processed %d entities, yielded %d persons", count, yielded)
