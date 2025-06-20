import requests
from time import sleep
from os import environ

# TODO Add logging of errors
# Load required bootstrap configs and fail if unsuccessful
if not environ.get('REST_API_NAME'):
    print("ERROR: Unable to bootstrap rest_connector, REST_API_NAME env variable does not exist")
    exit(78)  # 78: Configuration error.
if not environ.get('REST_API_PORT'):
    print("ERROR: Unable to bootstrap rest_connector, REST_API_PORT env variable does not exist")
    exit(78)  # 78: Configuration error.

REST_API = f"http://{environ['REST_API_NAME']}:{environ['REST_API_PORT']}"


def put_hashtable(hash_info) -> dict[str, set]:
    valid_keys = ['path', 'current_hash', 'current_dtg_latest', 'dirs', 'files', 'links']
    # hash_info's keys are the path, no need to verify it is present
    required_keys = ['current_hash', 'current_dtg_latest']
    changes = []
    # Reformat hash_info into db API format
    for item in hash_info.keys():
        # Validate and sanitize candidate hash entry
        missing_keys = False
        for key in hash_info[item].keys():
            if key not in valid_keys:
                print(f"Includes invalid key: '{key}'  in rest_connector.put_hashtable.")
                missing_keys = True
        for key in required_keys:
            if key not in hash_info[item].keys():
                print(f"Does not include required key: '{key}'  in rest_connector.put_hashtable.")
                missing_keys = True
        if missing_keys:
            print(f"ERROR: Malformed request in rest_connector.put_hashtable, skipping.\n")
            continue

        code, update = _db_put("hashtable",
                                    {'path': item,
                                        'current_hash': hash_info[item]['current_hash'],
                                        'current_dtg_latest': hash_info[item]['current_dtg_latest'],
                                        'dirs': hash_info[item].get('dirs'),
                                        'files': hash_info[item].get('files'),
                                        'links': hash_info[item].get('links')
                                    })
        if code != 200:
            print(f"ERROR: REST API returned {code}: {update}.")
            continue

        changes.append(update)

    # Process changes into more useful format
    sorted_changes = {'Created': set(), 'Deleted': set(), 'Modified': set()}
    for change in changes:
        for key in sorted_changes.keys():
            sorted_changes[key].update(set(change[key]))
    return sorted_changes


def get_single_hash(path) -> str | None:
    response = _db_get("hash", path)
    return _db_process_response(response)


def get_hashtable(path) -> dict | None:
    response = _db_get("hashtable", path)
    return _db_process_response(response)


def get_oldest_updates(root_path, percent=10):
    """
    Returns a list containing the directories in the ROOT_PATH that have the oldest "last verified time".The
    length of the list is the given "percent" of directories in the ROOT PATH
    """
    base_response = get_hashtable(root_path)
    # Base case 1, no entries in database
    if not base_response['current_dtg_latest']:
        print(f"STATUS: Local database is empty, requesting full hash")
        return [root_path]
    # Base case 2, no dirs in root path
    if len(base_response['dirs']) == 0:
        print(f"STATUS: no child directories in database, requesting full hash")
        return [root_path]
    # Build and sort list low to high by timestamp
    timestamps = []
    for directory in base_response['dirs']:
        timestamps.append(get_single_timestamp(directory))
    ordered_list = [x for _, x in sorted(zip(timestamps, base_response['dirs']))]
    # Calculate number of dirs to include in final list
    update_num = int(len(base_response['dirs']) * percent / 100) + 1
    # Edge case for empty dir
    if update_num > len(base_response['dirs']):
        update_num = len(base_response['dirs'])
    print(f"number I wanted: {update_num}")
    return ordered_list[:update_num]


def get_single_timestamp(path) -> float | None:
    response = _db_get("timestamp", path)
    return _db_process_response(response)


def get_priority_updates() -> str | None:
    response = _db_get('priority')
    return _db_process_response(response)


def _db_process_response(response):
    code, content = response
    if code == 200:
        return content
    return None


def _db_put(endpoint, request):
    return _db_contact('put', f'{REST_API}/{endpoint}', request)


def _db_get(endpoint, params=None):
    return _db_contact('get', f'{REST_API}/{endpoint}', params)


def _db_contact(req_type, endpoint, args):
    for i in range(3):
        for j in range(5):
            try:
                match req_type:
                    case 'put':
                        response = requests.post(endpoint, json=args)
                    case 'get':
                        response = requests.get(endpoint, params=args)
                    case _:
                        return 405, f"'{req_type}' is not an allowed method."
            except requests.exceptions.RequestException as e:
                print(f"my print statement {e}")
                return 0, e

            if response.status_code == 200:
                return response.status_code, response.json().get('data')
            if response.status_code == 404:
                return response.status_code, response.json().get('message')

            print(f"ERROR: Unable to contact local database on attempt #{i * 5 + j + 1}")
            print(f"ERROR {response.status_code}, {response.json().get('message')}")
            sleep(5)
        print(f"ERROR: Failed to contact local database {endpoint} endpoint, pausing.")
        sleep(60)
    exit(69)  # 69: Service unavailable.