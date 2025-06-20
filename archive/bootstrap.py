#!/bin/python3
import yaml
import pathlib
# TODO Add logging of errors

CONFIG_YAML = pathlib.Path('boot.yaml')

# Load bootstrap configs from .yaml, contact local db and fail if unsuccessful
def init_bootstrap (return_keys):
    return_dict = {}
    values_dict = load_yaml (CONFIG_YAML)

    for key in return_keys:
        return_dict[key] = values_dict.get(key)

    return return_dict


def load_yaml(path):
    with open(path, 'r') as stream:
        values_dict = yaml.safe_load(stream)
    return values_dict
