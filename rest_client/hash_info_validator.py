from .configuration import config

class HashInfoValidator:
    # These should align with the Hashtable requirements in the database
    VALID_KEYS = config.get('hash_validator_keys')
    REQUIRED_KEYS = config.get('hash_validator_required_keys')

    def validate(self, hash_info: dict) -> list:
        """Validate hash_info and return list of validation errors."""
        errors = []

        for path, item_data in hash_info.items():
            item_errors = self._validate_item(path, item_data)
            errors.extend(item_errors)

        return errors

    def _validate_item(self, path: str, item_data: dict) -> list:
        errors = []

        # Check for invalid keys
        for key in item_data.keys():
            if key not in self.VALID_KEYS:
                errors.append(f"Invalid key '{key}' in item '{path}'")

        # Check for missing required keys
        for key in self.REQUIRED_KEYS:
            if key not in item_data:
                errors.append(f"Missing required key '{key}' in item '{path}'")

        return errors
