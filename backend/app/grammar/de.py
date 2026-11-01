"""German grammar plugin: validates the grammar JSON stored in vocabulary_grammar.data.

Only fields relevant to the part of speech are allowed (a noun card can't carry conjugations).
The same models will validate LLM output in Phase 3.
"""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

Case = Literal["nominativ", "akkusativ", "dativ", "genitiv"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class NounGrammar(_Strict):
    pos: Literal["noun"] = "noun"
    article: Literal["der", "die", "das"]
    plural: str | None = Field(default=None, max_length=120, description="e.g. 'die Termine' or '-' if none")
    genitive: str | None = Field(default=None, max_length=120)
    gender: Literal["masculine", "feminine", "neuter"] | None = None

    @model_validator(mode="after")
    def gender_matches_article(self) -> "NounGrammar":
        expected = {"der": "masculine", "die": "feminine", "das": "neuter"}[self.article]
        if self.gender is None:
            self.gender = expected
        elif self.gender != expected:
            raise ValueError(f"gender '{self.gender}' contradicts article '{self.article}'")
        return self


class PresentConjugation(_Strict):
    ich: str
    du: str
    er_sie_es: str
    wir: str
    ihr: str
    sie_Sie: str


class PrepositionRequirement(_Strict):
    preposition: str = Field(max_length=20)
    case: Case
    example: str | None = None


class VerbGrammar(_Strict):
    pos: Literal["verb"] = "verb"
    infinitive: str
    praesens: PresentConjugation | None = None
    praeteritum: str | None = Field(default=None, description="3rd person singular, e.g. 'vereinbarte'")
    partizip_ii: str | None = None
    auxiliary: Literal["haben", "sein", "haben/sein"] | None = None
    separable: bool | None = None
    separable_prefix: str | None = None
    reflexive: Literal["no", "akkusativ", "dativ", "optional"] | None = None
    prepositions: list[PrepositionRequirement] = Field(default_factory=list)
    object_case: Case | None = None

    @model_validator(mode="after")
    def prefix_consistent(self) -> "VerbGrammar":
        if self.separable_prefix and self.separable is False:
            raise ValueError("separable_prefix given but separable is false")
        if self.separable_prefix and not self.infinitive.startswith(self.separable_prefix):
            raise ValueError("separable_prefix must be the start of the infinitive")
        return self


class AdjectiveGrammar(_Strict):
    pos: Literal["adjective"] = "adjective"
    comparative: str | None = None
    superlative: str | None = Field(default=None, description="e.g. 'am schnellsten'")
    prepositions: list[PrepositionRequirement] = Field(default_factory=list)


class PrepositionGrammar(_Strict):
    pos: Literal["preposition"] = "preposition"
    cases: list[Case] = Field(min_length=1)
    wechselpraeposition: bool = False


GermanGrammar = Annotated[
    NounGrammar | VerbGrammar | AdjectiveGrammar | PrepositionGrammar, Field(discriminator="pos")
]
_adapter: TypeAdapter = TypeAdapter(GermanGrammar)

POS_WITH_GRAMMAR = {"noun", "verb", "adjective", "preposition"}


def validate_german_grammar(part_of_speech: str, data: dict | None) -> dict | None:
    """Return normalized grammar JSON, or None. Raises ValueError on invalid/mismatched data."""
    if not data:
        return None
    if part_of_speech not in POS_WITH_GRAMMAR:
        raise ValueError(f"grammar details are not supported for part of speech '{part_of_speech}'")
    payload = {**data, "pos": data.get("pos", part_of_speech)}
    if payload["pos"] != part_of_speech:
        raise ValueError(f"grammar.pos '{payload['pos']}' does not match part_of_speech '{part_of_speech}'")
    return _adapter.validate_python(payload).model_dump(exclude_none=True)
