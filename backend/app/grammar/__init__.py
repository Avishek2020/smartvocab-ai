"""Language grammar plugins. Register a validator per learning-language code."""
from collections.abc import Callable

from app.grammar.de import validate_german_grammar

GrammarValidator = Callable[[str, dict | None], dict | None]

VALIDATORS: dict[str, GrammarValidator] = {"de": validate_german_grammar}


def validate_grammar(language_code: str, part_of_speech: str, data: dict | None) -> dict | None:
    validator = VALIDATORS.get(language_code)
    if validator is None:
        if data:
            raise ValueError(f"no grammar plugin registered for language '{language_code}'")
        return None
    return validator(part_of_speech, data)
