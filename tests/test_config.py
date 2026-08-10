import pytest


from src.config import (
    ConfigurationError,
    get_database_dsn,
    get_positive_integer_setting,
    get_required_setting,
)



def test_get_required_setting_returns_trimmed_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A valid environment setting should be returned without extra spaces."""

    # Arrange
    monkeypatch.setenv(
        "TEST_REQUIRED_SETTING",
        "  example value  ",
    )

    # Act
    result = get_required_setting(
        "TEST_REQUIRED_SETTING"
    )

    # Assert
    assert result == "example value"


def test_get_required_setting_rejects_missing_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing required setting should raise ConfigurationError."""

    # Arrange
    monkeypatch.delenv(
        "TEST_MISSING_SETTING",
        raising=False,
    )

    # Act and assert
    with pytest.raises(
        ConfigurationError,
        match="TEST_MISSING_SETTING",
    ):
        get_required_setting("TEST_MISSING_SETTING")


def test_get_required_setting_rejects_blank_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A setting containing only spaces should be treated as missing."""

    # Arrange
    monkeypatch.setenv(
        "TEST_BLANK_SETTING",
        "   ",
    )

    # Act and assert
    with pytest.raises(
        ConfigurationError,
        match="TEST_BLANK_SETTING",
    ):
        get_required_setting("TEST_BLANK_SETTING")


def test_get_positive_integer_setting_returns_integer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A positive integer stored as text should become an integer."""

    # Arrange
    monkeypatch.setenv(
        "TEST_INTEGER_SETTING",
        "25",
    )

    # Act
    result = get_positive_integer_setting(
        "TEST_INTEGER_SETTING"
    )

    # Assert
    assert result == 25
    assert isinstance(result, int)


def test_get_positive_integer_setting_rejects_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-numeric text should be rejected."""

    # Arrange
    monkeypatch.setenv(
        "TEST_INTEGER_SETTING",
        "thirty",
    )

    # Act and assert
    with pytest.raises(
        ConfigurationError,
        match="must be an integer",
    ):
        get_positive_integer_setting(
            "TEST_INTEGER_SETTING"
        )


@pytest.mark.parametrize(
    "invalid_value",
    [
        "0",
        "-5",
    ],
)
def test_get_positive_integer_setting_rejects_non_positive_values(
    monkeypatch: pytest.MonkeyPatch,
    invalid_value: str,
) -> None:
    """Zero and negative numbers should be rejected."""

    # Arrange
    monkeypatch.setenv(
        "TEST_INTEGER_SETTING",
        invalid_value,
    )

    # Act and assert
    with pytest.raises(
        ConfigurationError,
        match="must be greater than zero",
    ):
        get_positive_integer_setting(
            "TEST_INTEGER_SETTING"
        )



@pytest.mark.parametrize(
    "placeholder",
    [
        "CHANGE_ME",
        "REPLACE_ME",
        "YOUR_PASSWORD",
        "PASSWORD_HERE",
    ],
)
def test_get_database_dsn_rejects_placeholder_passwords(
    monkeypatch: pytest.MonkeyPatch,
    placeholder: str,
) -> None:
    """Obvious placeholder database credentials should be rejected."""

    monkeypatch.setenv(
        "DATABASE_DSN",
        (
            "host=db port=5432 "
            "dbname=ecommerce_analytics "
            "user=pipeline_user "
            f"password={placeholder}"
        ),
    )

    with pytest.raises(
        ConfigurationError,
        match="placeholder",
    ):
        get_database_dsn()




def test_get_database_dsn_accepts_real_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-placeholder database DSN should be accepted."""

    valid_dsn = (
        "host=db port=5432 "
        "dbname=ecommerce_analytics "
        "user=pipeline_user "
        "password=test_secure_123"
    )

    monkeypatch.setenv(
        "DATABASE_DSN",
        valid_dsn,
    )

    result = get_database_dsn()

    assert result == valid_dsn


