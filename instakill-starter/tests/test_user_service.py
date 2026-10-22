
import pytest

from app.domain.models import User
from app.services.user_service import prepare_user


def test_prepare_user_strips_whitespace():
    user = prepare_user("  alex  ")

    assert isinstance(user, User)
    assert user.username == "alex"
    assert user.id is None


def test_prepare_user_rejects_empty_username():
    with pytest.raises(ValueError, match="Username must not be empty"):
        prepare_user("   ")
