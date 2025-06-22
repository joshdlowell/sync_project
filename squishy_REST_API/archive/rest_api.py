from flask import Flask, jsonify, request
from os import environ
from mysql_functions import HashTableDB

app = Flask(__name__)

# Ensure all dependencies are present
env_complete = True
for variable in ['LOCAL_MYSQL_NAME',
                 'LOCAL_DATABASE',
                 'LOCAL_USER',
                 'LOCAL_PASSWORD',
                 ]:
    if not environ.get(variable):
        print(f"ERROR: Unable to bootstrap rest_api, {variable} env variable does not exist")
        env_complete = False
if not env_complete:
    exit(78)  # 78: Configuration error.


items = {}
local_db = HashTableDB(environ['LOCAL_MYSQL_NAME'],
                       environ['LOCAL_DATABASE'],
                       environ['LOCAL_USER'],
                       environ['LOCAL_PASSWORD'])


@app.route('/hashtable', methods=['GET', 'POST'])
def get_put_hashes():
    if request.method == 'GET':
        record = local_db.get_hash_record(request.query_string.decode())
        if not record:
            return jsonify({"message": "Path not found"}), 404
        else:
            return jsonify({"message": "Success", "data": record})
    elif request.method == 'POST':
        if 'path' not in request.json.keys():
            return jsonify({"message": "path required but not found in your request json"}), 400
        print("getting here")
        print(request.json)
        # for key, value in request.json.items():
        changes = local_db.insert_or_update_hash(**request.json)
        if not changes:
            return jsonify({"message": "Database error, see DB logs"}), 500
        return jsonify({"message": "Success", "data": changes})
    else:
        return jsonify({"message": f"'{request.method}' Method not allowed"}), 405


@app.route('/hash', methods=['GET'])
def get_hash():
    hash_value = local_db.get_single_hash_record(request.query_string.decode())
    if not hash_value:
        return jsonify({"message": "Path not found"}), 404
    return jsonify({"message": "Success", "data": hash_value})


@app.route('/timestamp', methods=['GET'])
def get_timestamp():
    path = request.query_string.decode()
    if path not in items.keys():
        return jsonify({"message": "Path not found"}), 404
    return jsonify({"message": "Success", "data": items[path]['current_dtg_latest']}), 200


@app.route('/priority', methods=['GET'])
def get_priority():
    priority = []
    for entry in items.keys():
        if items[entry].get('current_hash') != items[entry].get('target_hash'):
            priority.append(entry)
        return jsonify({"message": "Success", "data": priority}), 200


# Helper functions
# def add_db_entry(new_entry, request_dict, changes):
#     changes['Created'].append(new_entry['path'])
#     # new_entry = {'path': path}
#     for key, value in request_dict.items():
#         new_entry[key] = value
#     dirs = new_entry.get('dirs')
#     if dirs is not None: changes['Created'].extend([f"{new_entry['path']}/{x}" for x in dirs])
#     files = new_entry.get('files')
#     if files is not None: changes['Created'].extend([f"{new_entry['path']}/{x}" for x in files])
#     links = new_entry.get('links')
#     if links is not None: changes['Created'].extend([f"{new_entry['path']}/{x}" for x in links])
# def add_db_entry
#
#
# def update_db_entry(db_entry, request_dict, changes):
#     if db_entry.get('current_hash') != request_dict.get('current_hash'):
#         db_entry['current_hash'] = request_dict.get('current_hash')
#         changes['Modified'].append(db_entry['path'])
#
#     if db_entry.get('current_dtg_latest') != request_dict.get('current_dtg_latest'):
#         db_entry['current_dtg_latest'] = request_dict.get('current_dtg_latest')
#
#     for key in ['dirs', 'files', 'links']:
#         if request_dict.get(key) and db_entry.get(key) != sorted(request_dict.get(key)):
#             changes['Created'].extend([f"{db_entry['path']}/{x}" for x in request_dict.get(key) if x not in db_entry['dirs']])
#             changes['Deleted'].extend([f"{db_entry['path']}/{x}" for x in db_entry.get(key) if x not in request_dict.get('dirs')])
#             db_entry[key] = sorted(request_dict.get(key))


# @app.route('/api/items', methods=['GET'])
# def get_items():
#     return jsonify(items)
#
# @app.route('/api/items/<int:item_id>', methods=['GET'])
# def get_item(item_id):
#     item = next((item for item in items if item["id"] == item_id), None)
#     if item:
#         return jsonify(item)
#     return jsonify({"message": "Item not found"}), 404
#
# @app.route('/api/items', methods=['POST'])
# def create_item():
#     data = request.get_json()
#     new_item = {"id": len(items) + 1, "name": data['name']}
#     items.append(new_item)
#     return jsonify(new_item), 201
#
# @app.route('/api/items/<int:item_id>', methods=['PUT'])
# def update_item(item_id):
#     data = request.get_json()
#     item = next((item for item in items if item["id"] == item_id), None)
#     if item:
#         item['name'] = data['name']
#         return jsonify(item)
#     return jsonify({"message": "Item not found"}), 404
#
# @app.route('/api/items/<int:item_id>', methods=['DELETE'])
# def delete_item(item_id):
#     global items
#     items = [item for item in items if item["id"] != item_id]
#     return jsonify({"message": "Item deleted"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)