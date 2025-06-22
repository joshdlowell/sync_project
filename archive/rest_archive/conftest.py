# """
# Test utilities for REST API package tests.
#
# This module provides common utilities and base classes for testing the REST API package.
# With the conversion from pytest to unittest, the fixtures previously defined here
# have been moved to the setUp methods in the test case classes.
# """
# import unittest
# from flask import Flask
#
# from squishy_REST_API.app_factory.app_factory import create_app
# from squishy_REST_API.DB_connections.local_memory import LocalMemoryConnection
#
#
# class BaseTestCase(unittest.TestCase):
#     """Base test case for all tests."""
#
#     def create_app(self):
#         """Create and configure a Flask application for testing."""
#         # Create test configuration
#         test_config = {
#             'TESTING': True,
#             'DEBUG': False,
#         }
#
#         # Create application with test configuration
#         return create_app(test_config)
#
#     def create_test_client(self, app):
#         """Create a test client for the Flask application."""
#         return app.test_client()
#
#     def create_mock_db(self):
#         """Create a mock database for testing."""
#         # Create an in-memory database or mock
#         return LocalMemoryConnection()
#     #
#     # return LocalMemoryConnection(
#     #     host='localhost',
#     #     database='test_db',
#     #     user='test_user',
#     #     password='test_password',
#     #     # Use a mock connection factory for testing
#     #     connection_factory=lambda **kwargs: None
#     # )
