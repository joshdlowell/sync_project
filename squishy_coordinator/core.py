import json
from time import time
from contextlib import contextmanager
from typing import List, Tuple

from squishy_coordinator import CoordinatorFactory, config, logger


@contextmanager
def performance_monitor(coordinator_service, operation_name: str):
    """Context manager to monitor operation performance."""
    start_time = time()
    # Log start
    coordinator_service.put_log_entry(
        message="START SESSION - coordinator",
        detailed_message=f"Starting {operation_name} {'Core' if config.is_core else 'Remote'} tasks"
    )
    try:
        yield
    finally:
        duration = time() - start_time
        minutes = int(duration // 60)
        seconds = duration % 60
        if minutes > 0:
            duration = f"{minutes}m {seconds:.2f}s"
            logger.info(f"{operation_name} completed in {minutes}m {seconds:.2f}s")
        else:
            duration = f"{seconds:.2f}s"
        # Log completion
        message = f"Completed {operation_name} {'Core' if config.is_core else 'Remote'} tasks in {duration}"
        logger.info(message)
        coordinator_service.put_log_entry(message="FINISH SESSION - coordinator", detailed_message=message)


def run_core(coordinator_service):
    """Run core site tasks."""
    # get priority updates from local (updates where target hash doesn't match current)
    change_list = coordinator_service.get_priority_updates()

    # get authorized updates from pipeline mssql database
    auth_list = coordinator_service.get_pipeline_updates()

    # Verify no unscheduled changes and alert if found
    unauth_list = change_list - auth_list
    if len(unauth_list) > 0:
        logger.warning(f"Unauthorized changes to: {unauth_list}")
        coordinator_service.put_log_entry("Unauthorized changes detected.", json.dumps({'unauthorized':unauth_list}), 'WARNING')

    # Perform authorized update hashing per mssql
    updates = coordinator_service.recompute_hashes(auth_list)

    # Put new hashes and targets into the databases
    log_list = []
    for path, new_hash in updates:
        log_list.append(path)
        coordinator_service.update_target_hash(path, new_hash, new_hash)
    logger.info(f"Authorized hash updates complete: {log_list}")
    coordinator_service.put_log_entry("Authorized hash updates complete.", log_list)


def run_remote(coordinator_service):
    """Run remote site tasks."""
    # Verify hash status with core
    updates = coordinator_service.verify_hash_status()
    # Update targets as needed
    for path, local_hash, core_hash in updates:
        # Missing local files: (path, None, core_hash)
        # Additional local files: (path, local_hash, None)
        if local_hash is None or core_hash is None:
            # Parent path will be updated under mismatches
            continue
        # Hash mismatches: (path, local_hash, core_hash)
        # Keep current hash the same, this "flags" the path for priority update
        coordinator_service.update_target_hash(path, local_hash, core_hash)


def main() -> int:
    """Main entry point to run a routine update.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """

    logger.info("Starting coordinator routine")
    coordinator_service = CoordinatorFactory.create_service()

    with performance_monitor(coordinator_service, "Coordinator"):

        try:
            # Verify database entries for path integrity
            logger.info(f"Verifying database integrity")
            coordinator_service.verify_database_integrity()

            # Check if remote or core and run respective tasks
            if config.is_core:
                run_core(coordinator_service)
            else:
                run_remote(coordinator_service)

            # Consolidate logs
            logger.info(f"Consolidating logs")
            coordinator_service.consolidate_logs()
            # Ship consolidated logs to core and remove from local table
            logger.info(f"Shipping consolidated logs to core and removing from local table")
            coordinator_service.ship_logs_to_core()

            return 0  # Success

        except Exception as e:
            logger.error(f"Fatal error in main routine: {e}")
            return 1  # Failure
