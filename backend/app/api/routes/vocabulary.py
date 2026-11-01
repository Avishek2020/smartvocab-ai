from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.deps import DB, CurrentUser
from app.schemas.vocabulary import CardCreate, CardOut, CardPage, CardUpdate, CollectionCreate, CollectionOut
from app.services import vocabulary as svc

router = APIRouter(tags=["vocabulary"])


@router.get("/vocabulary", response_model=CardPage)
def list_cards(
    user: CurrentUser, db: DB,
    q: Annotated[str | None, Query(max_length=100)] = None,
    status_: Annotated[Literal["draft", "new", "learning", "review", "mastered", "suspended"] | None,
                       Query(alias="status")] = None,
    cefr: Annotated[Literal["A1", "A2", "B1", "B2", "C1", "C2"] | None, Query()] = None,
    pos: Annotated[str | None, Query(max_length=16)] = None,
    collection_id: UUID | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> CardPage:
    return svc.list_cards(db, user, q=q, status=status_, cefr=cefr, pos=pos, collection_id=collection_id,
                          page=page, page_size=page_size)


@router.post("/vocabulary", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def create_card(data: CardCreate, user: CurrentUser, db: DB) -> CardOut:
    return svc.create_card(db, user, data)


@router.get("/vocabulary/{card_id}", response_model=CardOut)
def get_card(card_id: UUID, user: CurrentUser, db: DB) -> CardOut:
    return svc.card_out(db, user, svc.get_card(db, user, card_id))


@router.put("/vocabulary/{card_id}", response_model=CardOut)
def update_card(card_id: UUID, data: CardUpdate, user: CurrentUser, db: DB) -> CardOut:
    return svc.update_card(db, user, card_id, data)


@router.delete("/vocabulary/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: UUID, user: CurrentUser, db: DB) -> Response:
    svc.delete_card(db, user, card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/collections", response_model=list[CollectionOut])
def list_collections(user: CurrentUser, db: DB) -> list[CollectionOut]:
    return svc.list_collections(db, user)


@router.post("/collections", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(data: CollectionCreate, user: CurrentUser, db: DB) -> CollectionOut:
    return svc.create_collection(db, user, data)
