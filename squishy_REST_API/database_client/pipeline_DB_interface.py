from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple

# TODO need pipline implementation
class PipelineDBConnection(ABC):
    """
    Database access class for core site pipeline database operations.

    This class provides methods to interact with the pipeline database
    for storing and retrieving information.
    """

    def get_pipeline_updates(self) -> list[str]:
        """
        Retrieve unprocessed pipeline updates to the baseline from the pipeline database.

        Returns:
            A list of path strings representing unprocessed pipeline updates.
        """
        pass
