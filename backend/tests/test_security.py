import pytest
import bcrypt

from app.core.security import hash_password, verify_password


def test_password_hash_verifies_correct_password():
    password = "WifiPlan-Pass-123!"
    assert verify_password(password, hash_password(password))


def test_password_hash_rejects_incorrect_password():
    assert not verify_password("not-the-password", hash_password("WifiPlan-Pass-123!"))


def test_hash_rejects_password_over_bcrypt_byte_limit():
    with pytest.raises(ValueError, match="72 UTF-8 bytes"):
        hash_password("a" * 73)


def test_verification_rejects_password_over_bcrypt_byte_limit():
    assert not verify_password("a" * 73, hash_password("WifiPlan-Pass-123!"))


def test_hash_rejects_empty_password():
    with pytest.raises(ValueError, match="1 to 72 UTF-8 bytes"):
        hash_password("")


def test_existing_bcrypt_hashes_remain_compatible():
    password = "Existing-WifiPlan-Hash!"
    legacy_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
    assert verify_password(password, legacy_hash)


def test_verification_rejects_malformed_hash():
    assert not verify_password("WifiPlan-Pass-123!", "not-a-bcrypt-hash")


def test_hash_rejects_utf8_password_over_bcrypt_byte_limit():
    with pytest.raises(ValueError, match="72 UTF-8 bytes"):
        hash_password("é" * 37)
