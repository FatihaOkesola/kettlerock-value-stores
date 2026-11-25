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


# A public test seed, never the private one: used to build a full world and traffic history for tests
TEST_SEED = "0123456789abcdef" * 4


@pytest.fixture(scope="session")
def test_sealed_bytes(params, tables):
    from kettlerock_engine.world import draw_world
    return draw_world(TEST_SEED, params, tables)


@pytest.fixture(scope="session")
def traffic_components(cfg, params, tables, test_sealed_bytes):
    from kettlerock_engine.traffic import build_traffic
    return build_traffic(cfg, params, tables, TEST_SEED, test_sealed_bytes, keep_components=True)


@pytest.fixture(scope="session")
def traffic_table(cfg, params, tables, test_sealed_bytes):
    from kettlerock_engine.traffic import build_traffic
    return build_traffic(cfg, params, tables, TEST_SEED, test_sealed_bytes)
