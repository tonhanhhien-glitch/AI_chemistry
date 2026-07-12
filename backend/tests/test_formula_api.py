"""API regression tests for formula parsing."""

from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("NaCl", {"formula": "NaCl", "atoms": {"Na": 1, "Cl": 1}, "charge": 0}),
        (
            "SO4^2-",
            {"formula": "SO4^2-", "atoms": {"S": 1, "O": 4}, "charge": -2},
        ),
    ],
)
def test_formula_endpoint_success(formula: str, expected: dict[str, object]) -> None:
    response = client.get("/api/v1/formula", params={"formula": formula})

    assert response.status_code == 200
    assert response.json() == expected


@pytest.mark.parametrize(
    ("formula", "code"),
    [
        ("2H", "UNSUPPORTED_FORMULA_SYNTAX"),
        ("FeCl3", "UNSUPPORTED_ELEMENT"),
    ],
)
def test_formula_endpoint_validation_error(formula: str, code: str) -> None:
    response = client.get("/api/v1/formula", params={"formula": formula})

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == code
    assert isinstance(body["detail"]["message"], str)
    assert body["detail"]["message"]
