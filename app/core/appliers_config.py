import os

# Supported ATS portals for providers
PROVIDER_PORTALS = [
    "workday", "greenhouse", "smartrecruiters", "dice", "applytojob",
    "lever", "workable", "bamboohr", "breezyhr", "infojobs", "infojobs_net", "totaljobs"
]


def process_default(data):
    """Default processing function that returns data as-is."""
    return data


def process_for_skyvern(data):
    """
    Processes data for skyvern.
    Filters out applications with the portal field in the PROVIDER_PORTALS list,
    while retaining the original structure with 'user_id' and 'content'.
    """
    user_id = data.get("user_id")
    content = data.get("content", {})

    if not isinstance(content, dict):
        return {"user_id": user_id, "content": {}}

    filtered_content = {
        key: value
        for key, value in content.items()
        if isinstance(value, dict) and value.get('portal') not in PROVIDER_PORTALS
    }

    # Return the filtered data in the same structure
    return {"user_id": user_id, "content": filtered_content} if filtered_content else None


def process_for_providers(data):
    """
    Processes data for providers.
    Filters applications with the portal field matching the PROVIDER_PORTALS list,
    while retaining the original structure with 'user_id' and 'content'.
    """
    user_id = data.get("user_id")
    content = data.get("content", {})

    if not isinstance(content, dict):
        return {"user_id": user_id, "content": {}}

    filtered_content = {
        key: value
        for key, value in content.items()
        if isinstance(value, dict) and value.get('portal') in PROVIDER_PORTALS
    }

    # Return the filtered data in the same structure
    return {"user_id": user_id, "content": filtered_content} if filtered_content else None


def _build_appliers_config():
    """
    Builds the APPLIERS configuration based on environment variables.

    Environment variables:
        ENABLE_SKYVERN_APPLIER: Set to 'true' to enable Skyvern applier (default: false)
        ENABLE_PROVIDERS_APPLIER: Set to 'true' to enable Providers applier (default: true)
        SKYVERN_QUEUE: Queue name for Skyvern (default: skyvern_queue)
        PROVIDERS_QUEUE: Queue name for Providers (default: providers_queue)
    """
    appliers = {}

    # Skyvern applier (disabled by default)
    if os.getenv("ENABLE_SKYVERN_APPLIER", "false").lower() == "true":
        appliers['skyvern'] = {
            'queue_name': os.getenv("SKYVERN_QUEUE", "skyvern_queue"),
            'process_function': process_for_skyvern
        }

    # Providers applier (enabled by default)
    if os.getenv("ENABLE_PROVIDERS_APPLIER", "true").lower() == "true":
        appliers['providers'] = {
            'queue_name': os.getenv("PROVIDERS_QUEUE", "providers_queue"),
            'process_function': process_for_providers
        }

    return appliers


# Appliers configuration - built from environment variables
APPLIERS = _build_appliers_config()
