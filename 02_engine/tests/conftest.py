import pytest
from kettlerock_engine.config import load_config
from kettlerock_engine.params import Params
from kettlerock_engine.build import build_structure


@pytest.fixture(scope="session")
def cfg():
    return load_config()


@pytest.fixture(scope="session")
def params(cfg):
    return Params(cfg.calibrated_parameters, cfg.calibrated_vectors)


@pytest.fixture(scope="session")
def tables(cfg):
    return build_structure(cfg)
