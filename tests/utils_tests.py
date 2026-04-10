from utils.hash import hash_password, verify_password


def test_hash_password_is_not_plain_text():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_two_hashes_of_same_password_are_different():
    hash1 = hash_password("mypassword")
    hash2 = hash_password("mypassword")
    assert hash1 != hash2
