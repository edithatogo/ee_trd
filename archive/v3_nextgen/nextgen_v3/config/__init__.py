import os
from ..io.loaders import load_config

def load_settings():
    path = os.path.join(os.path.dirname(__file__), 'settings.yaml')
    return load_config(path)

def load_correlations():
    path = os.path.join(os.path.dirname(__file__), 'correlations.yaml')
    return load_config(path)