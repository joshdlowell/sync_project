import unittest
from unittest.mock import patch, Mock
import os
from squishy_integrity.configuration.config import Config, ConfigError


class TestConfig(unittest.TestCase):
    def setUp(self):
        # Reset singleton instance for each test
        Config._instance = None
        Config._config = None
        Config._session_id = None

    def test_config_singleton(self):
        """Test that Config is a singleton."""
        config1 = Config()
        config2 = Config()
        self.assertIs(config1, config2)

    def test_default_configuration(self):
        """Test that default configuration is loaded correctly."""
        config = Config()
        self.assertEqual(config.get('rest_api_host'), 'squishy-rest-api')
        self.assertEqual(config.get('rest_api_port'), 5000)
        self.assertEqual(config.get('root_path'), '/baseline')
        self.assertEqual(config.get('max_runtime_min'), 10)
        self.assertEqual(config.get('debug'), False)
        self.assertEqual(config.get('log_level'), 'INFO')

    def test_config_from_dict(self):
        """Test configuration from dictionary."""
        config_dict = {
            'rest_api_host': 'custom-host',
            'rest_api_port': 8080,
            'max_runtime_min': 15,
            'debug': True
        }
        config = Config(config_dict)
        self.assertEqual(config.get('rest_api_host'), 'custom-host')
        self.assertEqual(config.get('rest_api_port'), 8080)
        self.assertEqual(config.get('max_runtime_min'), 15)
        self.assertEqual(config.get('debug'), True)

    @patch.dict(os.environ, {
        'REST_API_HOST': 'env-host',
        'REST_API_PORT': '9090',
        'DEBUG': 'true',
        'LOG_LEVEL': 'debug'
    })
    def test_config_from_environment(self):
        """Test configuration from environment variables."""
        config = Config()
        self.assertEqual(config.get('rest_api_host'), 'env-host')
        self.assertEqual(config.get('rest_api_port'), 9090)
        self.assertEqual(config.get('debug'), True)
        self.assertEqual(config.get('log_level'), 'DEBUG')

    def test_rest_api_url_property(self):
        """Test rest_api_url property."""
        config = Config()
        expected_url = f"http://{config.get('rest_api_host')}:{config.get('rest_api_port')}"
        self.assertEqual(config.rest_api_url, expected_url)

    def test_session_id_property(self):
        """Test session_id property."""
        config = Config()
        session_id = config.session_id
        self.assertIsNotNone(session_id)
        self.assertIsInstance(session_id, str)
        self.assertEqual(len(session_id), 32)  # 16 bytes = 32 hex chars

    def test_convert_value_integer(self):
        """Test _convert_value for integer types."""
        config = Config()
        self.assertEqual(config._convert_value('rest_api_port', '8080'), 8080)
        self.assertEqual(config._convert_value('max_retries', '5'), 5)

    def test_convert_value_integer_error(self):
        """Test _convert_value with invalid integer."""
        config = Config()
        with self.assertRaises(ConfigError):
            config._convert_value('rest_api_port', 'invalid')

    def test_convert_value_boolean(self):
        """Test _convert_value for boolean types."""
        config = Config()
        self.assertTrue(config._convert_value('debug', 'true'))
        self.assertTrue(config._convert_value('debug', '1'))
        self.assertTrue(config._convert_value('debug', 'yes'))
        self.assertTrue(config._convert_value('debug', 'on'))
        self.assertFalse(config._convert_value('debug', 'false'))
        self.assertFalse(config._convert_value('debug', '0'))

    def test_convert_value_string(self):
        """Test _convert_value for string types."""
        config = Config()
        self.assertEqual(config._convert_value('rest_api_host', 'localhost'), 'localhost')

    def test_log_level_validation(self):
        """Test log level validation."""
        config = Config({'log_level': 'invalid'})
        self.assertEqual(config.get('log_level'), 'INFO')

        config = Config({'log_level': 'warning'})
        self.assertEqual(config.get('log_level'), 'WARNING')

    def test_is_debug_mode(self):
        """Test is_debug_mode method."""
        config = Config({'debug': True})
        self.assertTrue(config.is_debug_mode())

        config = Config({'debug': False})
        self.assertFalse(config.is_debug_mode())

    def test_dict_access(self):
        """Test dictionary-style access."""
        config = Config()
        self.assertEqual(config['rest_api_host'], 'squishy-rest-api')
        self.assertTrue('rest_api_host' in config)
        self.assertFalse('nonexistent_key' in config)

    def test_set_method(self):
        """Test _set method for testing purposes."""
        config = Config()
        config._set('test_key', 'test_value')
        self.assertEqual(config.get('test_key'), 'test_value')

    def test_repr(self):
        """Test string representation."""
        config = Config()
        repr_str = repr(config)
        self.assertIn('Config', repr_str)
        self.assertIn('rest_api_host', repr_str)