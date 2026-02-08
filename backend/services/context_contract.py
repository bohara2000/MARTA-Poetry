from typing import Any, Dict, List, Tuple


def _is_optional_str(value: Any) -> bool:
    return value is None or isinstance(value, str)


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def validate_context_payload(payload: Any) -> Tuple[bool, List[str]]:
    """Validate the context-service payload contract.

    Returns (is_valid, errors).
    """
    errors: List[str] = []

    if not isinstance(payload, dict):
        return False, ["payload must be a dict"]

    route_id = payload.get("route_id")
    if not isinstance(route_id, str) or not route_id.strip():
        errors.append("route_id must be a non-empty string")

    live_anchor = payload.get("live_anchor")
    if not isinstance(live_anchor, dict):
        errors.append("live_anchor must be a dict")
    else:
        if not _is_optional_str(live_anchor.get("neighborhood")):
            errors.append("live_anchor.neighborhood must be a string or null")
        if not _is_optional_str(live_anchor.get("place")):
            errors.append("live_anchor.place must be a string or null")
        if not _is_optional_str(live_anchor.get("poi")):
            errors.append("live_anchor.poi must be a string or null")

    fallback_anchors = payload.get("fallback_anchors")
    if not _is_str_list(fallback_anchors):
        errors.append("fallback_anchors must be a list of strings")

    signals = payload.get("signals")
    if not isinstance(signals, dict):
        errors.append("signals must be a dict")
    else:
        traffic = signals.get("traffic")
        if not (traffic is None or isinstance(traffic, (str, dict))):
            errors.append("signals.traffic must be a string, dict, or null")
        weather = signals.get("weather")
        if not (weather is None or isinstance(weather, dict)):
            errors.append("signals.weather must be a dict or null")
        solar = signals.get("solar")
        if not (solar is None or isinstance(solar, dict)):
            errors.append("signals.solar must be a dict or null")
        alerts = signals.get("alerts")
        if not isinstance(alerts, list):
            errors.append("signals.alerts must be a list")

    history = payload.get("history")
    if not isinstance(history, list):
        errors.append("history must be a list")

    meta = payload.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta must be a dict")
    else:
        if not isinstance(meta.get("source_timestamps"), dict):
            errors.append("meta.source_timestamps must be a dict")
        if not isinstance(meta.get("cache_hits"), dict):
            errors.append("meta.cache_hits must be a dict")

    return len(errors) == 0, errors