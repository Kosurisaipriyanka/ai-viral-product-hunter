from marketplace_evidence import (
    delete_marketplace_evidence,
    list_marketplace_evidence,
    save_marketplace_evidence,
)


def sample():
    return {
        "product_keyword": "portable blender",
        "source": "Amazon India",
        "listing_title": "Sample portable blender",
        "listing_url": "https://example.com/listing",
        "listed_price_inr": 1499,
        "supplier_cost_inr": 600,
        "shipping_cost_inr": 100,
        "manually_checked": True,
        "evidence_notes": "Sample only",
    }


def test_save_list_and_delete_marketplace_evidence(tmp_path):
    db = tmp_path / "evidence.sqlite3"
    evidence_id = save_marketplace_evidence(sample(), db_path=db)
    rows = list_marketplace_evidence(db_path=db)
    assert len(rows) == 1
    assert rows[0]["id"] == evidence_id
    assert rows[0]["product_keyword"] == "portable blender"
    assert rows[0]["manually_checked"] == 1
    assert delete_marketplace_evidence(evidence_id, db_path=db) is True
    assert list_marketplace_evidence(db_path=db) == []


def test_marketplace_evidence_requires_valid_fields_and_url(tmp_path):
    db = tmp_path / "evidence.sqlite3"
    invalid = sample()
    invalid["listing_url"] = "javascript:alert(1)"
    try:
        save_marketplace_evidence(invalid, db_path=db)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid URL should be rejected")
