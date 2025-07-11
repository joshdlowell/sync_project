import unittest
from unittest.mock import patch, Mock


class TestInit(unittest.TestCase):
    def test_version_import(self):
        """Test that version can be imported."""
        from squishy_integrity import __version__
        self.assertIsInstance(__version__, str)
        self.assertEqual(__version__, "1.2.0")

    def test_config_import(self):
        """Test that config can be imported."""
        from squishy_integrity import config
        self.assertIsNotNone(config)

    def test_logger_import(self):
        """Test that logger can be imported."""
        from squishy_integrity import logger
        self.assertIsNotNone(logger)

    @patch('squishy_integrity.IntegrityCheckFactory')
    def test_integrity_check_factory_import(self, mock_factory):
        """Test that IntegrityCheckFactory can be imported."""
        from squishy_integrity import IntegrityCheckFactory
        self.assertIsNotNone(IntegrityCheckFactory)

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        from squishy_integrity import __all__
        expected_exports = ['config', 'logger', 'IntegrityCheckFactory']
        self.assertEqual(set(__all__), set(expected_exports))