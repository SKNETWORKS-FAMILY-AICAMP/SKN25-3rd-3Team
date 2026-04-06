from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit


RECIPE_SOURCE_NAME = "10000recipe"

SPACE_PATTERN = re.compile(r"\s+")
NUMERIC_QUANTITY_PATTERN = re.compile(
    r"(\d+\s*/\s*\d+|\d+(?:\.\d+)?)\s*(kg|g|ml|l|개|대|줄기|인분|T|t|큰술|작은술|장|알|팩|봉|줌|숟가락|스푼)",
    re.IGNORECASE,
)
QUALITATIVE_QUANTITY_PATTERN = re.compile(
    r"(약간|톡톡|툭툭|적당량|적당히|조금|소량|한줌|한 꼬집|한꼬집|넉넉히|선택)$"
)
UNIT_NORMALIZATION = {
    "g": "g",
    "kg": "kg",
    "ml": "ml",
    "l": "l",
    "개": "piece",
    "대": "stalk",
    "줄기": "stalk",
    "인분": "serving",
    "T": "tbsp",
    "t": "tsp",
    "큰술": "tbsp",
    "작은술": "tsp",
    "장": "sheet",
    "알": "piece",
    "팩": "pack",
    "봉": "bag",
    "줌": "handful",
    "숟가락": "spoon",
    "스푼": "spoon",
}
QUALITATIVE_UNIT_NORMALIZATION = {
    "약간": "to_taste",
    "적당량": "to_taste",
    "적당히": "to_taste",
    "조금": "small_amount",
    "소량": "small_amount",
    "톡톡": "sprinkle",
    "툭툭": "sprinkle",
    "한줌": "handful",
    "한 꼬집": "pinch",
    "한꼬집": "pinch",
    "넉넉히": "generous",
    "선택": "optional",
}
OPTIONAL_INGREDIENT_KEYWORDS = {"선택"}
TOOL_KEYWORDS = frozenset(
    {
        "도마",
        "칼",
        "볼",
        "접시",
        "대접",
        "냄비",
        "프라이팬",
        "후라이팬",
        "집게",
        "그릇",
        "국자",
        "주걱",
        "나이프",
        "스푼",
        "포크",
        "채반",
        "뒤집개",
        "장갑",
        "랩",
        "전자레인지",
        "계량스푼",
        "유리볼",
    }
)


def _normalize_spaces(text: str) -> str:
    return SPACE_PATTERN.sub(" ", text).strip()


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _coerce_optional_text(value: Any) -> str | None:
    text = _normalize_spaces(_coerce_text(value))
    return text or None


def _find_quantity_match(text: str) -> tuple[re.Match[str] | None, str | None]:
    numeric_match = NUMERIC_QUANTITY_PATTERN.search(text)
    if numeric_match is not None:
        return numeric_match, "numeric"

    qualitative_match = QUALITATIVE_QUANTITY_PATTERN.search(text)
    if qualitative_match is not None:
        return qualitative_match, "qualitative"

    return None, None


def _parse_quantity_value(quantity_number_text: str) -> float:
    normalized_number_text = quantity_number_text.replace(" ", "")
    if "/" in normalized_number_text:
        numerator_text, denominator_text = normalized_number_text.split("/", 1)
        return float(numerator_text) / float(denominator_text)

    return float(normalized_number_text)


def _extract_quantity(text: str) -> tuple[str | None, float | None, str | None, str | None]:
    quantity_match, quantity_match_type = _find_quantity_match(text)
    if quantity_match is None or quantity_match_type is None:
        return None, None, None, None

    quantity_text = _normalize_spaces(quantity_match.group(0))
    if quantity_match_type == "qualitative":
        return (
            quantity_text,
            None,
            quantity_text,
            QUALITATIVE_UNIT_NORMALIZATION.get(quantity_text, quantity_text),
        )

    quantity_value = _parse_quantity_value(quantity_match.group(1))
    quantity_unit_raw = quantity_match.group(2)
    quantity_unit_normalized = UNIT_NORMALIZATION.get(
        quantity_unit_raw,
        UNIT_NORMALIZATION.get(quantity_unit_raw.lower(), quantity_unit_raw.lower()),
    )
    return quantity_text, quantity_value, quantity_unit_raw, quantity_unit_normalized


def _extract_ingredient_name(normalized_text: str) -> tuple[str | None, str | None]:
    quantity_match, _ = _find_quantity_match(normalized_text)
    ingredient_name_source = normalized_text if quantity_match is None else normalized_text[: quantity_match.start()]
    ingredient_name_raw = _normalize_spaces(ingredient_name_source).strip(" ,")
    if not ingredient_name_raw:
        return None, None

    return ingredient_name_raw, ingredient_name_raw.lower().replace(" ", "")


def _resolve_entity_type(ingredient_name_raw: str | None, normalized_text: str) -> str:
    token_source = ingredient_name_raw or normalized_text
    return "tool" if any(keyword in token_source for keyword in TOOL_KEYWORDS) else "ingredient"


def _extract_source_recipe_id(url: str) -> str | None:
    normalized_url = _normalize_spaces(url)
    if not normalized_url:
        return None

    parsed_url = urlsplit(normalized_url)
    if "10000recipe.com" not in parsed_url.netloc:
        return None

    path_segments = [segment for segment in parsed_url.path.split("/") if segment]
    if len(path_segments) >= 2 and path_segments[0] == "recipe" and path_segments[1].isdigit():
        return path_segments[1]

    return None


def parse_ingredient(raw_text: Any) -> dict[str, Any]:
    raw_text_value = _coerce_text(raw_text)
    normalized_text = _normalize_spaces(raw_text_value.replace("구매", " "))
    quantity_text, quantity_value, quantity_unit_raw, quantity_unit_normalized = _extract_quantity(normalized_text)
    ingredient_name_raw, ingredient_name_raw_normalized = _extract_ingredient_name(normalized_text)
    entity_type = _resolve_entity_type(ingredient_name_raw, normalized_text)
    is_optional = quantity_text in OPTIONAL_INGREDIENT_KEYWORDS
    warnings: list[str] = []

    if entity_type == "tool":
        warnings.append("tool_detected")
    if quantity_text is None:
        warnings.append("missing_quantity")
    elif quantity_value is None and not is_optional:
        warnings.append("non_numeric_quantity")
    if is_optional:
        warnings.append("optional_ingredient")

    if not ingredient_name_raw:
        parse_status = "failed"
        warnings.append("missing_ingredient_name")
    elif quantity_text is None or quantity_value is None:
        parse_status = "partial"
    else:
        parse_status = "parsed"

    return {
        "raw_text": raw_text_value,
        "normalized_text": normalized_text,
        "ingredient_name_raw": ingredient_name_raw,
        "ingredient_name_raw_normalized": ingredient_name_raw_normalized,
        "quantity_text": quantity_text,
        "quantity_value": quantity_value,
        "quantity_min": None,
        "quantity_max": None,
        "quantity_unit_raw": quantity_unit_raw,
        "quantity_unit_normalized": quantity_unit_normalized,
        "is_optional": is_optional,
        "annotations": [],
        "entity_type": entity_type,
        "parse_status": parse_status,
        "warnings": warnings,
    }


def build_parsed_recipe_payload(raw_recipe: dict[str, Any], parsed_ingredients: list[dict[str, Any]]) -> dict[str, Any]:
    raw_recipe_id = str(raw_recipe["_id"])
    title = _normalize_spaces(_coerce_text(raw_recipe.get("title")))
    url = _normalize_spaces(_coerce_text(raw_recipe.get("url")))
    warnings: list[str] = []

    if not title:
        warnings.append("missing_title")
    if not url:
        warnings.append("missing_url")

    has_header_error = not title or not url
    has_failed_ingredient = any(ingredient["parse_status"] == "failed" for ingredient in parsed_ingredients)
    has_partial_ingredient = any(ingredient["parse_status"] == "partial" for ingredient in parsed_ingredients)

    if not parsed_ingredients:
        warnings.append("missing_ingredients")
        parse_status = "failed"
    else:
        if has_failed_ingredient:
            warnings.append("ingredient_parse_failed")
        elif has_partial_ingredient:
            warnings.append("ingredient_parse_partial")

        parse_status = "partial" if has_header_error or has_failed_ingredient or has_partial_ingredient else "parsed"

    return {
        "raw_recipe_id": raw_recipe_id,
        "source": RECIPE_SOURCE_NAME,
        "source_recipe_id": _extract_source_recipe_id(url),
        "title": title,
        "url": url,
        "category_name": _coerce_optional_text(raw_recipe.get("category_name")),
        "category_param": _coerce_optional_text(raw_recipe.get("category_param")),
        "category_id": _coerce_optional_text(raw_recipe.get("category_id")),
        "parse_status": parse_status,
        "warnings": warnings,
    }
