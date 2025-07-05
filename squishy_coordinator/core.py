from time import time
from contextlib import contextmanager
from typing import List, Tuple

from squishy_coordinator import CoordinatorFactory, config, logger


@contextmanager
def performance_monitor(service, operation_name: str):
    """Context manager to monitor operation performance."""
    start_time = time()
    # Log start
    # service.hash_storage.put_log(
    #     message="Starting Merkle compute",
    #     detailed_message="Starting new session",
    #     session_id=config.session_id
    # )
    try:
        yield
    finally:
        duration = time() - start_time
        minutes = int(duration // 60)
        seconds = duration % 60
        # Log completion
        # service.hash_storage.put_log(
        #     message="Completed Merkle compute",
        #     detailed_message="Session Completed",
        #     session_id=config.session_id
        # )
        if minutes > 0:
            logger.info(f"{operation_name} completed in {minutes}m {seconds:.2f}s")
        else:
            logger.info(f"{operation_name} completed in {seconds:.2f}s")


def get_paths_to_process(merkle_service, root_path: str) -> List[str]:
    """Get and deduplicate paths that need processing."""
    priority = merkle_service.hash_storage.get_priority_updates()
    logger.info(f"Priority updates: {priority}")
    routine = merkle_service.hash_storage.get_oldest_updates(root_path)
    logger.info(f"Oldest updates: {routine}")
    return merkle_service.remove_redundant_paths_with_priority(priority, routine)


def run_core(coordinator_service):
    # get priority updates from local

        # get authorized updates from mssql
        # Verify no unscheduled changes and alert
    #
    # Perform update hashing per mssql
    #             # Post hash update to local (target and current)
    #             # post hash to mssql
    pass

def run_remote(coordinator_service):
    # Verify hash status with core
    updates = coordinator_service.verify_hash_status()
    # Update targets as needed
    for update in updates:
        coordinator_service.update_target_hash(update)


def main() -> int:
    """Main entry point to run a routine update.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """

    logger.info("Starting coordinator routine")

    coordinator_service = CoordinatorFactory.create_service()

    with performance_monitor(coordinator_service, "Coordinator routine"):

        try:
            # Verify database entries for path integrity
            logger.info(f"Verifying path integrity")
            coordinator_service.verify_path_integrity()

            # Check if remote or core and run respective tasks
            if config.is_core:
                run_core(coordinator_service)
                logger.info(f"Completed: Core task processing completed.")
            else:
                run_remote(coordinator_service)
                logger.info(f"Completed: Remote task processing completed.")

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
