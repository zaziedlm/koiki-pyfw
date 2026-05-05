import pytest

from libkoiki.core.security import get_password_hash, verify_password


def test_get_password_hash_generates_bcrypt_2b_hash():
    hashed_password = get_password_hash("TestPass123@")

    assert hashed_password.startswith("$2b$")
    assert verify_password("TestPass123@", hashed_password) is True


def test_verify_password_rejects_wrong_password():
    hashed_password = get_password_hash("TestPass123@")

    assert verify_password("WrongPass123@", hashed_password) is False


def test_verify_password_accepts_existing_bcrypt_2b_hash():
    existing_hash = "$2b$12$wIrq8gKvsFKwKGtv.0sPwuOPNR/8.ENqgArMHAm9MF2l58J37RFTC"

    assert verify_password("TestPass123@", existing_hash) is True


@pytest.mark.parametrize(
    "invalid_hash",
    [
        "",
        "not-a-bcrypt-hash",
        "$2b$12$broken",
    ],
)
def test_verify_password_returns_false_for_invalid_hash(invalid_hash):
    assert verify_password("TestPass123@", invalid_hash) is False
