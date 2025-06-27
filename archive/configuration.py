from dataclasses import dataclass
from os import environ
from typing import Optional


# @dataclass
# class Config:
#     rest_api_name: str
#     rest_api_port: str
#
#     @property
#     def rest_api_url(self) -> str:
#         return f"http://{self.rest_api_name}:{self.rest_api_port}"
#
#     @classmethod
#     def from_env(cls) -> 'Config':
#         api_name = environ.get('REST_API_NAME')
#         api_port = environ.get('REST_API_PORT')
#
#         if not api_name:
#             raise ValueError("REST_API_NAME environment variable is required")
#         if not api_port:
#             raise ValueError("REST_API_PORT environment variable is required")
#
#         return cls(rest_api_name=api_name, rest_api_port=api_port)
