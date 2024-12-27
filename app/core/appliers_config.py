def process_default(data):
    # Default processing function that returns data as-is
    return data

def process_for_skyvern(data):
    """
    Processes data for skyvern.
    Filters out applications with the portal field in the specified list,
    while retaining the original structure with 'user_id' and 'content'.
    """
    user_id = data.get("user_id")
    content = data.get("content", {})

    if not isinstance(content, dict):
        return {"user_id": user_id, "content": {}}

    filtered_content = {
        key: value
        for key, value in content.items()
        if isinstance(value, dict) and value.get('portal') not in ["workaday", "sium", "this_is_an_example"]
    }

    # Return the filtered data in the same structure
    return {"user_id": user_id, "content": filtered_content}

def process_for_providers(data):
    """
    Processes data for providers.
    Filters applications with the portal field matching the specified list,
    while retaining the original structure with 'user_id' and 'content'.
    """
    user_id = data.get("user_id")
    content = data.get("content", {})

    if not isinstance(content, dict):
        return {"user_id": user_id, "content": {}}

    filtered_content = {
        key: value
        for key, value in content.items()
        if isinstance(value, dict) and value.get('portal') in ["workaday", "sium", "this_is_an_example"]
    }

    # Return the filtered data in the same structure
    return {"user_id": user_id, "content": filtered_content}



# Appliers configuration for modularity
APPLIERS = {
    'skyvern': {
        'queue_name': 'skyvern_queue',
        'process_function': process_for_skyvern
    },
    'providers': {
        'queue_name': 'providers_queue',
        'process_function': process_for_providers
    },
    # Add more appliers as needed
}
