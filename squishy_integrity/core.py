from time import time
from contextlib import contextmanager
from typing import List, Tuple

from squishy_integrity import IntegrityCheckFactory, config, logger


@contextmanager
def performance_monitor(merkle_service, operation_name: str):
    """Context manager to monitor operation performance."""
    start_time = time()
    # Log start
    merkle_service.hash_storage.put_log(
        message="Starting Merkle compute",
        detailed_message="Starting new session",
        session_id=config.session_id
    )
    try:
        yield
    finally:
        duration = time() - start_time
        minutes = int(duration // 60)
        seconds = duration % 60
        # Log completion
        merkle_service.hash_storage.put_log(
            message="Completed Merkle compute",
            detailed_message="Session Completed",
            session_id=config.session_id
        )
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


def process_paths(merkle_service, paths_list: List[str], root_path: str,
                  max_runtime_min: int) -> Tuple[int, int]:
    """
    Process paths within time limit.

    Returns:
        Tuple of (processed_count, total_count)
    """
    finish_time = time() + max_runtime_min * 60
    processed_count = 0

    for dir_path in paths_list:
        if time() > finish_time:
            logger.info(f"Time limit reached, stopping processing")
            break
        logger.info(f"Processing path: {dir_path}")
        try:
            merkle_service.compute_merkle_tree(root_path, dir_path)
            processed_count += 1
            logger.info(f"Processed path: {dir_path}")
        except Exception as e:
            logger.error(f"Failed to process path {dir_path}: {e}")
            continue

    return processed_count, len(paths_list)


def main() -> int:
    """Main entry point to run a routine update.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """

    logger.info("Starting integrity check routine")

    merkle_service = IntegrityCheckFactory.create_service()
    root_path = config.get('root_path')
    logger.info(f"Discovered root path {root_path}")
    max_runtime_min = config.get('max_runtime_min', 10)

    with performance_monitor(merkle_service, "Integrity check routine"):

        try:
            logger.info(f"Collecting paths to process")
            paths_list = get_paths_to_process(merkle_service, root_path)
            logger.info(f"Processing {len(paths_list)} paths")

            processed_count, total_count = process_paths(
                merkle_service, paths_list, root_path, max_runtime_min
            )

            logger.info(f"Completed: processed {processed_count} of {total_count} paths")
            return 0  # Success

        except Exception as e:
            logger.error(f"Fatal error in main routine: {e}")
            return 1  # Failure