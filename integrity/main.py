from time import time
import integritycheck
import rest_connector

if __name__ == '__main__':

    # # Load bootstrap configs from .yaml, contact local db and fail if unsuccessful
    # ROOTPATH = bootstrap.init_bootstrap (['root_path']).get('root_path')
    # # Check if we have required local variables to run
    # if not ROOTPATH:
    #     print("ERROR: Unable to bootstrap integrity check. Exiting")
    #     exit (-1)

    # api_object = DBAPI(squishy_db_type='postgresql', squishy_db_host='localhost', squishy_db_port=5002)
    root_path= '/media/devdrive'
    dirs_to_update = rest_connector.get_oldest_updates(root_path)
    priority_updates = rest_connector.get_priority_updates()

    print (dirs_to_update) # Debug statement
    print (len (dirs_to_update)) # Debug statement
    print (priority_updates) # Debug statement
    input (len (priority_updates)) # Debug statement

    all_changes = {}
    end_time = time() + (60 * 10)  # Don't start any new verifications after 10 minutes runtime

    # Start with dirs flagged for priority update, then check dirs with the oldest last checked times
    for upd_dir in [priority_updates, dirs_to_update]:
        if time() - end_time > 0:
            break
        upd_dir_hash, changes = integritycheck.DFS_merkle(root_path, upd_dir)

    # Update the parent(s) node hash values based on the new dir_path_hash
    # if root_path != dir_path:
    #     recompute_root(root_path, dir_path, changes)

    print (all_changes)
