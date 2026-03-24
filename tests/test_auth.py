"""Unit tests for the user authentication module (src/app/auth.py)."""
import pytest

from src.app.auth import (
    AuthenticationError,
    InvalidTokenError,
    UserNotFoundError,
    UserRecord,
    authenticate_user,
    create_user,
    deactivate_user,
    generate_token,
    get_user,
    hash_password,
    revoke_token,
    validate_token,
    verify_password,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_stores():
    """Return a brand-new (user_store, token_store) pair for test isolation."""
    return {}, {}


# ---------------------------------------------------------------------------
# hash_password
# ---------------------------------------------------------------------------

class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("mypassword")
        assert isinstance(result, str)

    def test_contains_separator(self):
        result = hash_password("mypassword")
        assert ":" in result

    def test_salt_and_digest_present(self):
        result = hash_password("mypassword")
        parts = result.split(":")
        assert len(parts) == 2
        salt, digest = parts
        assert len(salt) == 32
        assert len(digest) == 64

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2

    def test_raises_type_error_for_non_string(self):
        with pytest.raises(TypeError):
            hash_password(12345)

    def test_empty_string_is_hashable(self):
        result = hash_password("")
        assert ":" in result


# ---------------------------------------------------------------------------
# verify_password
# ---------------------------------------------------------------------------

class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        hashed = hash_password("correct")
        assert verify_password("correct", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_empty_password_returns_false_for_non_empty_hash(self):
        hashed = hash_password("nonempty")
        assert verify_password("", hashed) is False

    def test_empty_password_hashed_verifies(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_returns_false_for_malformed_hash(self):
        assert verify_password("password", "nocolon") is False

    def test_returns_false_for_non_string_plain(self):
        hashed = hash_password("mypassword")
        assert verify_password(None, hashed) is False

    def test_returns_false_for_non_string_hashed(self):
        assert verify_password("mypassword", None) is False

    def test_case_sensitive(self):
        hashed = hash_password("Password")
        assert verify_password("password", hashed) is False

    def test_whitespace_matters(self):
        hashed = hash_password("pass word")
        assert verify_password("password", hashed) is False


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_creates_user_record(self):
        store, _ = _fresh_stores()
        record = create_user("alice", "securepass", store=store)
        assert isinstance(record, UserRecord)
        assert record.username == "alice"

    def test_user_is_active_by_default(self):
        store, _ = _fresh_stores()
        record = create_user("bob", "securepass", store=store)
        assert record.is_active is True

    def test_password_is_hashed(self):
        store, _ = _fresh_stores()
        record = create_user("carol", "securepass", store=store)
        assert record.hashed_password != "securepass"
        assert ":" in record.hashed_password

    def test_user_added_to_store(self):
        store, _ = _fresh_stores()
        create_user("dave", "securepass", store=store)
        assert "dave" in store

    def test_duplicate_username_raises_value_error(self):
        store, _ = _fresh_stores()
        create_user("eve", "securepass", store=store)
        with pytest.raises(ValueError, match="already taken"):
            create_user("eve", "differentpass", store=store)

    def test_empty_username_raises_value_error(self):
        store, _ = _fresh_stores()
        with pytest.raises(ValueError, match="empty"):
            create_user("", "securepass", store=store)

    def test_whitespace_only_username_raises_value_error(self):
        store, _ = _fresh_stores()
        with pytest.raises(ValueError, match="empty"):
            create_user("   ", "securepass", store=store)

    def test_short_password_raises_value_error(self):
        store, _ = _fresh_stores()
        with pytest.raises(ValueError, match="8 characters"):
            create_user("frank", "short", store=store)

    def test_password_exactly_8_chars_accepted(self):
        store, _ = _fresh_stores()
        record = create_user("grace", "12345678", store=store)
        assert record.username == "grace"

    def test_roles_stored(self):
        store, _ = _fresh_stores()
        record = create_user("hank", "securepass", roles=["admin"], store=store)
        assert "admin" in record.roles

    def test_roles_default_empty(self):
        store, _ = _fresh_stores()
        record = create_user("iris", "securepass", store=store)
        assert record.roles == []

    def test_username_stripped(self):
        store, _ = _fresh_stores()
        record = create_user("  jack  ", "securepass", store=store)
        assert record.username == "jack"
        assert "jack" in store


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

class TestGetUser:
    def test_returns_existing_user(self):
        store, _ = _fresh_stores()
        create_user("kim", "securepass", store=store)
        record = get_user("kim", store=store)
        assert record.username == "kim"

    def test_raises_user_not_found_for_missing_user(self):
        store, _ = _fresh_stores()
        with pytest.raises(UserNotFoundError):
            get_user("nobody", store=store)


# ---------------------------------------------------------------------------
# authenticate_user
# ---------------------------------------------------------------------------

class TestAuthenticateUser:
    def test_valid_credentials_returns_record(self):
        store, _ = _fresh_stores()
        create_user("lena", "goodpassword", store=store)
        record = authenticate_user("lena", "goodpassword", store=store)
        assert record.username == "lena"

    def test_wrong_password_raises_authentication_error(self):
        store, _ = _fresh_stores()
        create_user("mike", "goodpassword", store=store)
        with pytest.raises(AuthenticationError):
            authenticate_user("mike", "badpassword", store=store)

    def test_unknown_user_raises_authentication_error(self):
        store, _ = _fresh_stores()
        with pytest.raises(AuthenticationError):
            authenticate_user("ghost", "anypassword", store=store)

    def test_inactive_user_raises_authentication_error(self):
        store, _ = _fresh_stores()
        create_user("nina", "goodpassword", store=store)
        deactivate_user("nina", store=store)
        with pytest.raises(AuthenticationError, match="inactive"):
            authenticate_user("nina", "goodpassword", store=store)

    def test_error_message_does_not_leak_username_existence(self):
        store, _ = _fresh_stores()
        create_user("oscar", "goodpassword", store=store)
        try:
            authenticate_user("oscar", "wrong", store=store)
        except AuthenticationError as exc:
            wrong_pw_msg = str(exc)

        try:
            authenticate_user("nobody", "wrong", store=store)
        except AuthenticationError as exc:
            no_user_msg = str(exc)

        assert wrong_pw_msg == no_user_msg


# ---------------------------------------------------------------------------
# deactivate_user
# ---------------------------------------------------------------------------

class TestDeactivateUser:
    def test_deactivates_active_user(self):
        store, _ = _fresh_stores()
        create_user("pat", "securepass", store=store)
        deactivate_user("pat", store=store)
        assert store["pat"].is_active is False

    def test_deactivating_nonexistent_user_raises_user_not_found(self):
        store, _ = _fresh_stores()
        with pytest.raises(UserNotFoundError):
            deactivate_user("phantom", store=store)

    def test_already_inactive_user_stays_inactive(self):
        store, _ = _fresh_stores()
        create_user("quinn", "securepass", store=store)
        deactivate_user("quinn", store=store)
        deactivate_user("quinn", store=store)
        assert store["quinn"].is_active is False


# ---------------------------------------------------------------------------
# generate_token / validate_token / revoke_token
# ---------------------------------------------------------------------------

class TestTokenManagement:
    def test_generate_token_returns_string(self):
        token_store = {}
        token = generate_token("alice", token_store=token_store)
        assert isinstance(token, str)

    def test_generate_token_stored_in_store(self):
        token_store = {}
        token = generate_token("alice", token_store=token_store)
        assert token in token_store

    def test_generate_token_maps_to_username(self):
        token_store = {}
        token = generate_token("alice", token_store=token_store)
        assert token_store[token] == "alice"

    def test_validate_token_returns_username(self):
        token_store = {}
        token = generate_token("bob", token_store=token_store)
        assert validate_token(token, token_store=token_store) == "bob"

    def test_validate_invalid_token_raises_error(self):
        token_store = {}
        with pytest.raises(InvalidTokenError):
            validate_token("not-a-real-token", token_store=token_store)

    def test_revoke_token_removes_from_store(self):
        token_store = {}
        token = generate_token("carol", token_store=token_store)
        revoke_token(token, token_store=token_store)
        assert token not in token_store

    def test_validate_revoked_token_raises_error(self):
        token_store = {}
        token = generate_token("dave", token_store=token_store)
        revoke_token(token, token_store=token_store)
        with pytest.raises(InvalidTokenError):
            validate_token(token, token_store=token_store)

    def test_revoke_nonexistent_token_is_noop(self):
        token_store = {}
        revoke_token("ghost-token", token_store=token_store)

    def test_multiple_tokens_per_user(self):
        token_store = {}
        t1 = generate_token("eve", token_store=token_store)
        t2 = generate_token("eve", token_store=token_store)
        assert t1 != t2
        assert validate_token(t1, token_store=token_store) == "eve"
        assert validate_token(t2, token_store=token_store) == "eve"

    def test_tokens_are_unique(self):
        token_store = {}
        tokens = {generate_token("frank", token_store=token_store) for _ in range(100)}
        assert len(tokens) == 100

    def test_revoking_one_token_leaves_other_valid(self):
        token_store = {}
        t1 = generate_token("grace", token_store=token_store)
        t2 = generate_token("grace", token_store=token_store)
        revoke_token(t1, token_store=token_store)
        with pytest.raises(InvalidTokenError):
            validate_token(t1, token_store=token_store)
        assert validate_token(t2, token_store=token_store) == "grace"


# ---------------------------------------------------------------------------
# Integration: full auth flow
# ---------------------------------------------------------------------------

class TestAuthFlow:
    def test_register_login_token_flow(self):
        user_store, token_store = _fresh_stores()

        create_user("zara", "strongpass1", store=user_store)
        record = authenticate_user("zara", "strongpass1", store=user_store)
        token = generate_token(record.username, token_store=token_store)
        username = validate_token(token, token_store=token_store)
        assert username == "zara"

    def test_logout_invalidates_token(self):
        user_store, token_store = _fresh_stores()

        create_user("yuri", "strongpass1", store=user_store)
        record = authenticate_user("yuri", "strongpass1", store=user_store)
        token = generate_token(record.username, token_store=token_store)

        revoke_token(token, token_store=token_store)

        with pytest.raises(InvalidTokenError):
            validate_token(token, token_store=token_store)

    def test_deactivated_user_cannot_log_in(self):
        user_store, _ = _fresh_stores()

        create_user("xavier", "strongpass1", store=user_store)
        deactivate_user("xavier", store=user_store)

        with pytest.raises(AuthenticationError):
            authenticate_user("xavier", "strongpass1", store=user_store)
