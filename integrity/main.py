from time import time
import integritycheck
import rest_connector

if __name__ == '__main__':

    # Set root path of baseline directory
    root_path= '/squishy/tests'

    # Get list of dirs who's current hashes don't match their target hashes
    priority_updates = rest_connector.get_priority_updates()

    # Get list (default 10%) of dirs with the oldest current hash timestamps
    dirs_to_update = rest_connector.get_oldest_updates(root_path)

    # Debug
    print (dirs_to_update) # Debug statement
    print (len (dirs_to_update)) # Debug statement
    print (priority_updates) # Debug statement
    input (len (priority_updates)) # Debug statement

    all_changes = {}
    # Don't start any new verifications after 10 minutes of runtime
    end_time = time() + (60 * 10)

    # TODO print status messages so they will show in container logs
    # Start with dirs flagged for priority update, then check dirs with the oldest last checked times
    for upd_dir in [priority_updates, dirs_to_update]:
        if time() - end_time > 0:
            break
        upd_dir_hash, changes = integritycheck.DFS_merkle(root_path, upd_dir)

    # TODO
    # rest_connector.put_logs(all_changes)
    print (all_changes)
