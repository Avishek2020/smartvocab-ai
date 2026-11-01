"""Vocabulary and collection services. Every query is scoped by user_id."""
from uuid import UUID

from sqlalchemy import String, cast, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.grammar import validate_grammar
from app.models import (
    CollectionCard,
    Language,
    User,
    VocabularyCard,
    VocabularyCollection,
    VocabularyExample,
    VocabularyGrammar,
)
from app.schemas.vocabulary import CardCreate, CardOut, CardPage, CardUpdate, CollectionCreate, CollectionOut, ExampleOut


def _language(db: Session, user: User) -> Language:
    return db.get(Language, user.preferences.target_language_id)


def _card_query(user: User):
    return (
        select(VocabularyCard)
        .where(VocabularyCard.user_id == user.id)
        .options(selectinload(VocabularyCard.examples), selectinload(VocabularyCard.grammar))
    )


def get_card(db: Session, user: User, card_id: UUID) -> VocabularyCard:
    card = db.scalar(_card_query(user).where(VocabularyCard.id == card_id))
    if card is None:
        raise AppError(404, "not_found", "Card not found")  # same answer for "not yours" — no existence leak
    return card


def _collection_ids(db: Session, card_ids: list[UUID]) -> dict[UUID, list[UUID]]:
    out: dict[UUID, list[UUID]] = {cid: [] for cid in card_ids}
    if card_ids:
        for coll_id, card_id in db.execute(
            select(CollectionCard.collection_id, CollectionCard.card_id).where(CollectionCard.card_id.in_(card_ids))
        ):
            out[card_id].append(coll_id)
    return out


def to_out(card: VocabularyCard, language_code: str, collection_ids: list[UUID]) -> CardOut:
    return CardOut(
        id=card.id, term=card.term, lemma=card.lemma, sense_key=card.sense_key, language=language_code,
        part_of_speech=card.part_of_speech, cefr_level=card.cefr_level, translations=card.translations,
        phonetic=card.phonetic, explanation=card.explanation, source_sentence=card.source_sentence,
        source_reference=card.source_reference, synonyms=card.synonyms, antonyms=card.antonyms,
        collocations=card.collocations, common_mistakes=card.common_mistakes, personal_note=card.personal_note,
        grammar=card.grammar.data if card.grammar else None,
        examples=[ExampleOut.model_validate(e) for e in card.examples],
        collection_ids=collection_ids, status=card.status, created_via=card.created_via, due_at=card.due_at,
        created_at=card.created_at, updated_at=card.updated_at,
    )


def card_out(db: Session, user: User, card: VocabularyCard) -> CardOut:
    lang = db.get(Language, card.language_id)
    return to_out(card, lang.code, _collection_ids(db, [card.id])[card.id])


def _check_collections(db: Session, user: User, ids: list[UUID]) -> list[UUID]:
    ids = list(dict.fromkeys(ids))
    if not ids:
        return []
    found = set(db.scalars(select(VocabularyCollection.id).where(
        VocabularyCollection.user_id == user.id, VocabularyCollection.id.in_(ids))))
    missing = [str(i) for i in ids if i not in found]
    if missing:
        raise AppError(404, "collection_not_found", "One or more collections were not found", missing)
    return ids


def _grammar(lang: Language, pos: str, data: dict | None) -> dict | None:
    try:
        return validate_grammar(lang.code, pos, data)
    except ValueError as e:
        raise AppError(422, "invalid_grammar", str(e).split("\n")[0], str(e)) from None


def _apply(card: VocabularyCard, data: CardCreate | CardUpdate) -> None:
    card.term = data.term
    card.lemma = data.lemma or data.term
    for field in ("sense_key", "part_of_speech", "cefr_level", "translations", "phonetic", "explanation",
                  "source_sentence", "source_reference", "synonyms", "antonyms", "collocations",
                  "common_mistakes", "personal_note"):
        setattr(card, field, getattr(data, field))


def create_card(db: Session, user: User, data: CardCreate) -> CardOut:
    lang = _language(db, user)
    grammar = _grammar(lang, data.part_of_speech, data.grammar)
    coll_ids = _check_collections(db, user, data.collection_ids)
    card = VocabularyCard(user_id=user.id, language_id=lang.id, created_via="manual", status="new")
    _apply(card, data)
    card.examples = [VocabularyExample(position=i, **e.model_dump()) for i, e in enumerate(data.examples)]
    if grammar:
        card.grammar = VocabularyGrammar(data=grammar)
    db.add(card)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "duplicate_card",
                       f"You already have a card for '{card.lemma}'"
                       + (f" ({card.sense_key})" if card.sense_key else "")
                       + ". Use a different sense to add another meaning.") from None
    for cid in coll_ids:
        db.add(CollectionCard(collection_id=cid, card_id=card.id))
    db.commit()
    return card_out(db, user, get_card(db, user, card.id))


def update_card(db: Session, user: User, card_id: UUID, data: CardUpdate) -> CardOut:
    card = get_card(db, user, card_id)
    lang = db.get(Language, card.language_id)
    grammar = _grammar(lang, data.part_of_speech, data.grammar)
    _apply(card, data)
    if data.status is not None:
        card.status = data.status
    card.examples = [VocabularyExample(position=i, **e.model_dump()) for i, e in enumerate(data.examples)]
    if grammar:
        if card.grammar:
            card.grammar.data = grammar
        else:
            card.grammar = VocabularyGrammar(data=grammar)
    else:
        card.grammar = None
    if data.collection_ids is not None:
        ids = _check_collections(db, user, data.collection_ids)
        db.execute(delete(CollectionCard).where(CollectionCard.card_id == card.id))
        for cid in ids:
            db.add(CollectionCard(collection_id=cid, card_id=card.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "duplicate_card", f"You already have a card for '{data.lemma or data.term}'") from None
    db.expire_all()
    return card_out(db, user, get_card(db, user, card.id))


def delete_card(db: Session, user: User, card_id: UUID) -> None:
    db.delete(get_card(db, user, card_id))
    db.commit()


def list_cards(db: Session, user: User, *, q: str | None, status: str | None, cefr: str | None,
               pos: str | None, collection_id: UUID | None, page: int, page_size: int) -> CardPage:
    stmt = _card_query(user)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            VocabularyCard.term.ilike(like), VocabularyCard.lemma.ilike(like),
            cast(VocabularyCard.translations, String).ilike(like),
        ))
    if status:
        stmt = stmt.where(VocabularyCard.status == status)
    if cefr:
        stmt = stmt.where(VocabularyCard.cefr_level == cefr)
    if pos:
        stmt = stmt.where(VocabularyCard.part_of_speech == pos)
    if collection_id:
        stmt = stmt.join(CollectionCard, CollectionCard.card_id == VocabularyCard.id).where(
            CollectionCard.collection_id == collection_id)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    cards = db.scalars(
        stmt.order_by(VocabularyCard.created_at.desc(), VocabularyCard.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    langs = {lang.id: lang.code for lang in db.scalars(select(Language))}
    colls = _collection_ids(db, [c.id for c in cards])
    return CardPage(items=[to_out(c, langs[c.language_id], colls[c.id]) for c in cards],
                    total=total or 0, page=page, page_size=page_size)


def list_collections(db: Session, user: User) -> list[CollectionOut]:
    rows = db.execute(
        select(VocabularyCollection, func.count(CollectionCard.card_id))
        .outerjoin(CollectionCard, CollectionCard.collection_id == VocabularyCollection.id)
        .where(VocabularyCollection.user_id == user.id)
        .group_by(VocabularyCollection.id)
        .order_by(VocabularyCollection.is_default.desc(), VocabularyCollection.created_at, VocabularyCollection.name)
    ).all()
    # Defaults keep their curated order (A1 → C2, then themes); custom collections follow, oldest first.
    from app.services.users import DEFAULT_COLLECTIONS
    order = {name: i for i, (name, _) in enumerate(DEFAULT_COLLECTIONS)}
    rows = sorted(rows, key=lambda r: (not r[0].is_default, order.get(r[0].name, 999), r[0].created_at))
    return [CollectionOut(id=c.id, name=c.name, description=c.description, color=c.color,
                          is_default=c.is_default, card_count=n) for c, n in rows]


def create_collection(db: Session, user: User, data: CollectionCreate) -> CollectionOut:
    coll = VocabularyCollection(user_id=user.id, language_id=user.preferences.target_language_id,
                                name=data.name.strip(), description=data.description, color=data.color)
    db.add(coll)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "duplicate_collection", f"A collection named '{data.name}' already exists") from None
    return CollectionOut(id=coll.id, name=coll.name, description=coll.description, color=coll.color,
                         is_default=False, card_count=0)
