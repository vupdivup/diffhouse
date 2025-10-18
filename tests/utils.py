def create_failure_msg(msg: str, details: dict) -> str:
    """Create a detailed failure message for test assertions.

    Args:
        msg: The main failure message.
        details: Additional details to include in the message.

    Returns:
        str: The formatted failure message.

    """
    detail_lines = [f'==={k.upper()}===\n{v}' for k, v in details.items()]
    return f'{msg}\n' + '\n'.join(detail_lines)


def select_keys(d: dict, keys: list[str]) -> dict:
    """Pick keys from d, skipping missing keys.

    Args:
        d: The dictionary to pick from.
        keys: The list of keys to pick.

    Returns:
        A new dictionary with the selected keys and their values.

    """
    return {k: d[k] for k in keys if k in d}
