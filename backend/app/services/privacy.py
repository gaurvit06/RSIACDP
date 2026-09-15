def mask_phone(phone: str) -> str:
    """
    Mask a phone number while keeping the last four digits visible.
    """

    if not phone:
        return phone

    digits = "".join(
        character
        for character in phone
        if character.isdigit()
    )

    if len(digits) <= 4:
        return "****"

    return "*" * (len(digits) - 4) + digits[-4:]


def mask_email(email: str) -> str:
    """
    Mask an email address while preserving its domain.
    """

    if not email or "@" not in email:
        return "****"

    username, domain = email.split("@", 1)

    if len(username) <= 2:
        masked_username = "*" * len(username)
    else:
        masked_username = (
            username[0]
            + "*" * (len(username) - 2)
            + username[-1]
        )

    return f"{masked_username}@{domain}"


def mask_upi(upi: str) -> str:
    """
    Mask the username portion of a UPI ID while preserving the provider.
    """

    if not upi or "@" not in upi:
        return "****"

    username, provider = upi.split("@", 1)

    if len(username) <= 2:
        masked_username = "*" * len(username)
    else:
        masked_username = (
            username[0]
            + "*" * (len(username) - 2)
            + username[-1]
        )

    return f"{masked_username}@{provider}"