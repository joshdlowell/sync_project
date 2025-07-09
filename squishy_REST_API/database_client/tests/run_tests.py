import unittest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_unit_tests():
    """Run all unit tests."""
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def run_integration_tests():
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = loader.discover('tests/integration', pattern='test_*_integration.py')
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def run_all_tests():
    """Run both unit and integration tests."""
    print("Running Unit Tests...")
    unit_result = run_unit_tests()

    print("\n" + "=" * 50)
    print("Running Integration Tests...")
    integration_result = run_integration_tests()

    return unit_result.wasSuccessful() and integration_result.wasSuccessful()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'unit':
            result = run_unit_tests()
        elif sys.argv[1] == 'integration':
            result = run_integration_tests()
        else:
            print("Usage: python run_tests.py [unit|integration]")
            sys.exit(1)
    else:
        result = run_all_tests()

    sys.exit(0 if result.wasSuccessful() else 1)
