import re
from typing import Iterable

def slugify_part(value: str) -> str:
    """
    Converts a string to a slug-friendly format.
    Replaces spaces with hyphens, removes non-alphanumeric characters,
    and converts to lowercase.
    """
    value = value.lower()
    value = re.sub(r'[^a-z0-9\s-]', '', value)
    value = re.sub(r'[\s-]+', '-', value).strip('-')
    return value


def generate_club_slug(parts: Iterable[str | None]) -> str:
    cleaned_parts: list[str] = []
    for part in parts:
        if not part:
            continue
        if not isinstance(part, str):
            continue
        slug_part = slugify_part(part)
        if slug_part:
            cleaned_parts.append(slug_part)
    return '-'.join(cleaned_parts)
