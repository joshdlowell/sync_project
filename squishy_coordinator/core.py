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
    detailed_message = f"Starting {operation_name} {'Core' if config.is_core else 'Remote'} tasks"
    logger.info(detailed_message)
    coordinator_service.put_log_entry(
        message="START SESSION",
        detailed_message=detailed_message
    )
    try:
        yield
    finally:
        duration = time() - start_time
        minutes, seconds = duration // 60, duration % 60
        if minutes > 0:
            duration = f"{minutes}m {seconds:.2f}s"
            logger.info(f"{operation_name} completed in {minutes}m {seconds:.2f}s")
        else:
            duration = f"{seconds:.2f}s"
        # Log completion
        detailed_message = f"Completed {operation_name} {'Core' if config.is_core else 'Remote'} tasks in {duration}"
        logger.info(detailed_message)
        coordinator_service.put_log_entry(
            message="FINISH SESSION",
            detailed_message=detailed_message
        )


def run_core(coordinator_service):
    """Run core site tasks."""
    # get priority updates from local (updates where target hash doesn't match current)
    change_list = coordinator_service.get_priority_updates()

    # get authorized updates from pipeline mssql database
    auth_list = coordinator_service.get_pipeline_updates()

    # Verify no unscheduled changes and alert if found
    unauth_list = [item for item in change_list if not any(item.startswith(auth_item) for auth_item in auth_list)]
    if len(unauth_list) > 0:
        logger.warning(f"Unauthorized changes to: {unauth_list}")
        coordinator_service.put_log_entry("Unauthorized changes detected.", json.dumps({'unauthorized_updates':unauth_list}), 'WARNING')

    # Perform authorized update hashing per pipeline
    updates = coordinator_service.recompute_hashes(auth_list)

    # Put new hashes and targets into the databases
    log_list = []
    for path, new_hash in updates:
        log_list.append(path)
        coordinator_service.update_target_hash(path, new_hash, new_hash)
    logger.info(f"Authorized hash updates complete: {log_list}")
    coordinator_service.put_log_entry("Authorized hash updates complete.", json.dumps({'authorized_updates': log_list}))


def run_remote(coordinator_service):
    """Run remote site tasks."""
    # Verify hash status with core
    updates = coordinator_service.verify_hash_status()
    # Update targets as needed and build list for core
    core_path_data = coordinator_service.log_and_create_updates(updates)
    # Send updates
    if coordinator_service.send_status_to_core(core_path_data):
        logger.info(f"Updated core with remote hash status")
    else:
        logger.info(f"Failed to update core with remote hash status")


def main() -> int:
    """Main entry point to run a routine update.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """

    logger.info("Starting coordinator routine")
    partial_failure = False
    coordinator_service = CoordinatorFactory.create_service()

    # Check if system is healthy
    if not coordinator_service.is_healthy():
        logger.error("Unable to run coordinator due to unhealthy REST service")
        return 1

    with performance_monitor(coordinator_service, "Coordinator - Verification"):

        try:
            # Verify database entries for path integrity
            logger.info(f"Verifying database integrity")
            coordinator_service.verify_database_integrity()

            # Check if remote or core and run respective tasks
            if config.is_core:
                run_core(coordinator_service)
            else:
                run_remote(coordinator_service)

        except Exception as e:
            logger.error(f"Fatal error in Verification routine: {e}")
            partial_failure = True
            # return 1  # Failure

    with performance_monitor(coordinator_service, "Coordinator - Log forwarding"):

        try:
            # Consolidate logs
            logger.info(f"Consolidating logs")
            coordinator_service.consolidate_logs()
            # Ship consolidated logs to core and remove from local table
            logger.info(f"Shipping consolidated logs to core and removing from local table")
            coordinator_service.ship_logs_to_core()

        except Exception as e:
            logger.error(f"Fatal error in Log forwarding routine: {e}")
            partial_failure = True
            # return 1  # Failure

    if partial_failure:
        return 1  # Failure or Partial failure
    else:
        return 0  # Success
