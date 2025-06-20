#!/bin/python3
from time import time
from mysql_functions import HashTableDB


def main():
    # Initialize database connection
    db = HashTableDB(
        host='local_squishy_db',  # Docker container name
        database='local_squishy_db',
        user='squishy',
        password='squishy'
    )

    # Get list of tables
    result = db.show_all_tables()

    # Insert/Update a record
    success = db.insert_or_update_hash(
        path='/home/user/documents',
        current_hash='abc123def456',
        target_hash='xyz789uvw012',
        dirs='[dir1,dir2,dir3]',
        files='[file1.txt,file2.txt]',
        links='[link1,link2]'
    )
    print(f"Insert/Update successful: {success}")

    # Get a specific record
    record = db.get_hash_record('/home/user/documents')
    if record:
        print(f"Record found: {record}")

    # Update specific fields
    updated = db.update_hash(
        '/home/user/documents',
        current_hash='new_hash_value',
        current_dtg_latest=time()
    )
    print(f"Update successful: {updated}")

    # Search by hash
    matches = db.search_by_hash('abc123def456', 'current')
    print(f"Found {len(matches)} matching records")

    # Get all records
    all_records = db.get_all_records()
    print(f"Total records: {len(all_records)}")
    print(all_records)


if __name__ == "__main__":
    main()