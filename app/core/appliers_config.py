def process_default(data):
    # Default processing function that returns data as-is
    return data

def process_for_applier2(data):
    # EXAMPLE:
    # Custom processing for another applier
    # Extract specific parts of the data or transform it
    processed_data = {
        'job_ids': list(data.keys()),
        'jobs': [job_data['job_title'] for job_data in data.values()]
    }
    return processed_data

# Appliers configuration for modularity :D
APPLIERS = {
    'skyvern': {
        'queue_name': 'skyvern_queue',
        'process_function': process_default
    },
    'greenhouse': {
        'queue_name': 'greenhouse_queue',
        'process_function': process_default
    },
    'applier2': {
        'queue_name': 'other_applier_queue',
        'process_function': process_for_applier2
    },
    # Add more appliers as needed, letsgo!
}
