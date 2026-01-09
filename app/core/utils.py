"""Utility functions for the application."""


def validate_sku_format(sku: str) -> tuple[bool, str | None]:
    """
    Validate SKU format: [CLASS]-[MATERIAL]-[SIZE]-[LENGTH]

    Args:
        sku: The SKU string to validate

    Returns:
        A tuple of (is_valid, error_message). If valid, error_message is None.
    """
    sku_parts = sku.split("-")

    if len(sku_parts) != 4:
        return (
            False,
            f"Invalid SKU format. Expected format: [CLASS]-[MATERIAL]-[SIZE]-[LENGTH], "
            f"but got '{sku}'",
        )

    # Validate that all parts are non-empty
    if any(not part.strip() for part in sku_parts):
        return False, "All SKU components must be non-empty"

    return True, None
