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
