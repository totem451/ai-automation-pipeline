from datetime import datetime, timezone


def get_current_datetime(timezone_name: str = "UTC") -> str:
    """Return the current date and time.

    Args:
        timezone_name: Timezone identifier. Only "UTC" is supported in this MVP.
                       Additional timezones can be added via the `zoneinfo` module.

    Returns:
        A human-readable string with the current date, time, day-of-week and timezone.
    """
    # For the MVP we always use UTC regardless of the parameter to avoid
    # pulling in extra dependencies.  We still surface the parameter so the
    # model can pass it naturally.
    now = datetime.now(tz=timezone.utc)
    day_name = now.strftime("%A")
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    return (
        f"Current date and time (UTC): {day_name}, {date_str} {time_str} UTC"
    )
