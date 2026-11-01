from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import register

API = "/api/v1"

VEREINBAREN = {
    "term": "vereinbaren",
    "part_of_speech": "verb",
    "cefr_level": "B1",
    "translations": {"en": "to arrange, to agree", "hi": "तय करना"},
    "source_sentence": "Wir müssen einen Termin vereinbaren.",
    "collocations": ["einen Termin vereinbaren", "einen Preis vereinbaren", "einen Termin vereinbaren"],
    "grammar": {
        "infinitive": "vereinbaren", "praeteritum": "vereinbarte", "partizip_ii": "vereinbart",
        "auxiliary": "haben", "separable": False, "object_case": "akkusativ",
    },
    "examples": [{"sentence": "Wir haben einen Termin vereinbart.", "translation": "We arranged an appointment."}],
}


def test_create_and_get_verb_card(auth_client):
    r = auth_client.post(f"{API}/vocabulary", json=VEREINBAREN)
    assert r.status_code == 201, r.text
    card = r.json()
    assert card["lemma"] == "vereinbaren"
    assert card["language"] == "de"
    assert card["grammar"]["pos"] == "verb" and card["grammar"]["auxiliary"] == "haben"
    assert card["collocations"] == ["einen Termin vereinbaren", "einen Preis vereinbaren"]  # deduped
    assert card["examples"][0]["sentence"].startswith("Wir haben")
    assert auth_client.get(f"{API}/vocabulary/{card['id']}").json()["term"] == "vereinbaren"


def test_noun_grammar_validation(auth_client):
    ok = auth_client.post(f"{API}/vocabulary", json={
        "term": "Termin", "part_of_speech": "noun", "translations": {"en": "appointment"},
        "grammar": {"article": "der", "plural": "die Termine", "genitive": "des Termins"}})
    assert ok.status_code == 201, ok.text
    assert ok.json()["grammar"]["gender"] == "masculine"
    bad_article = auth_client.post(f"{API}/vocabulary", json={
        "term": "Bank", "part_of_speech": "noun", "grammar": {"article": "dem"}})
    assert bad_article.status_code == 422
    contradiction = auth_client.post(f"{API}/vocabulary", json={
        "term": "Haus", "part_of_speech": "noun", "grammar": {"article": "das", "gender": "feminine"}})
    assert contradiction.status_code == 422


def test_grammar_must_match_part_of_speech(auth_client):
    r = auth_client.post(f"{API}/vocabulary", json={
        "term": "schnell", "part_of_speech": "adjective", "grammar": {"pos": "verb", "infinitive": "x"}})
    assert r.status_code == 422
    r = auth_client.post(f"{API}/vocabulary", json={
        "term": "und", "part_of_speech": "conjunction", "grammar": {"something": 1}})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_grammar"


def test_separable_verb_and_preposition(auth_client):
    r = auth_client.post(f"{API}/vocabulary", json={
        "term": "teilnehmen", "part_of_speech": "verb",
        "grammar": {"infinitive": "teilnehmen", "separable": True, "separable_prefix": "teil",
                    "auxiliary": "haben", "partizip_ii": "teilgenommen",
                    "prepositions": [{"preposition": "an", "case": "dativ",
                                      "example": "Ich nehme an dem Kurs teil."}]}})
    assert r.status_code == 201, r.text
    assert r.json()["grammar"]["prepositions"][0]["case"] == "dativ"


def test_duplicate_lemma_and_sense(auth_client):
    base = {"term": "Bank", "part_of_speech": "noun", "grammar": {"article": "die"}}
    assert auth_client.post(f"{API}/vocabulary", json={**base, "sense_key": "bench"}).status_code == 201
    assert auth_client.post(f"{API}/vocabulary", json={**base, "sense_key": "financial"}).status_code == 201
    dup = auth_client.post(f"{API}/vocabulary", json={**base, "sense_key": "bench"})
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "duplicate_card"


def test_update_and_delete(auth_client):
    card = auth_client.post(f"{API}/vocabulary", json=VEREINBAREN).json()
    colls = auth_client.get(f"{API}/collections").json()
    business = next(c for c in colls if c["name"] == "Business German")
    upd = {**VEREINBAREN, "personal_note": "Used at work a lot", "collection_ids": [business["id"]], "examples": []}
    r = auth_client.put(f"{API}/vocabulary/{card['id']}", json=upd)
    assert r.status_code == 200, r.text
    assert r.json()["personal_note"] == "Used at work a lot"
    assert r.json()["collection_ids"] == [business["id"]]
    assert r.json()["examples"] == []
    counts = {c["name"]: c["card_count"] for c in auth_client.get(f"{API}/collections").json()}
    assert counts["Business German"] == 1
    assert auth_client.delete(f"{API}/vocabulary/{card['id']}").status_code == 204
    assert auth_client.get(f"{API}/vocabulary/{card['id']}").status_code == 404


def test_search_filter_pagination(auth_client):
    for i, (term, pos, cefr) in enumerate([("Termin", "noun", "A2"), ("vereinbaren", "verb", "B1"),
                                           ("schnell", "adjective", "A1"), ("Besprechung", "noun", "B1")]):
        auth_client.post(f"{API}/vocabulary", json={"term": term, "part_of_speech": pos, "cefr_level": cefr,
                                                     "translations": {"en": f"meaning {i}"}})
    assert auth_client.get(f"{API}/vocabulary", params={"q": "termin"}).json()["total"] == 1
    assert auth_client.get(f"{API}/vocabulary", params={"q": "meaning 3"}).json()["items"][0]["term"] == "Besprechung"
    assert auth_client.get(f"{API}/vocabulary", params={"pos": "noun"}).json()["total"] == 2
    assert auth_client.get(f"{API}/vocabulary", params={"cefr": "B1"}).json()["total"] == 2
    page = auth_client.get(f"{API}/vocabulary", params={"page_size": 3, "page": 2}).json()
    assert page["total"] == 4 and len(page["items"]) == 1


def test_user_isolation(client):
    register(client, "anna@example.com")
    card = client.post(f"{API}/vocabulary", json={"term": "Termin", "part_of_speech": "noun"}).json()
    anna_coll = client.get(f"{API}/collections").json()[0]["id"]

    bob = TestClient(app)
    register(bob, "bob@example.com", "Bob")
    assert bob.get(f"{API}/vocabulary/{card['id']}").status_code == 404
    assert bob.put(f"{API}/vocabulary/{card['id']}", json={"term": "x", "part_of_speech": "noun"}).status_code == 404
    assert bob.delete(f"{API}/vocabulary/{card['id']}").status_code == 404
    assert bob.get(f"{API}/vocabulary").json()["total"] == 0
    # Bob cannot attach his card to Anna's collection.
    r = bob.post(f"{API}/vocabulary", json={"term": "Haus", "part_of_speech": "noun", "collection_ids": [anna_coll]})
    assert r.status_code == 404
    # Bob's own duplicate lemma is fine (uniqueness is per user).
    assert bob.post(f"{API}/vocabulary", json={"term": "Termin", "part_of_speech": "noun"}).status_code == 201


def test_custom_collection(auth_client):
    r = auth_client.post(f"{API}/collections", json={"name": "Arbeit", "color": "#1d4ed8"})
    assert r.status_code == 201 and r.json()["card_count"] == 0
    assert auth_client.post(f"{API}/collections", json={"name": "Arbeit"}).status_code == 409
