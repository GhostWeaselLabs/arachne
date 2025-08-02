"""Schema validation utilities and adapters."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .issue import Issue


@runtime_checkable
class SchemaValidator(Protocol):
    """Protocol for optional schema validation adapters."""

    def validate_payload(self, model: Any, payload: Any) -> Issue | None:
        """Validate payload against model schema.

        Args:
            model: Schema model (e.g., Pydantic model)
            payload: Data to validate

        Returns:
            Issue if validation fails, None if valid
        """
        ...


class PydanticAdapter:
    """Optional Pydantic adapter for schema validation.

    Only available if Pydantic is installed.
    """

    def __init__(self) -> None:
        try:
            import pydantic  # type: ignore[import-not-found]

            self._pydantic = pydantic
        except Exception:
            self._pydantic = None

    def validate_payload(self, model: Any, payload: Any) -> Issue | None:
        """Validate payload against Pydantic model.

        Args:
            model: Pydantic model class
            payload: Data to validate

        Returns:
            Issue if validation fails, None if valid
        """
        if self._pydantic is None:
            return Issue(
                severity="warning",
                message="Pydantic not available for schema validation",
                location="adapter:pydantic",
            )

        try:
            # Attempt validation
            model.model_validate(payload)
            return None
        except Exception as e:
            return Issue(
                severity="error",
                message=f"Schema validation failed: {e}",
                location=f"schema:{model.__name__}",
            )
