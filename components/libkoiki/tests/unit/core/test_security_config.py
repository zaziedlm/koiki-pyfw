import importlib
import warnings


def test_security_config_import_does_not_emit_pydantic_config_deprecation():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        module = importlib.import_module("libkoiki.core.security_config")
        importlib.reload(module)

    assert not any(
        "Support for class-based `config` is deprecated" in str(warning.message)
        for warning in caught
    )


def test_update_config_uses_pydantic_v2_serialization():
    module = importlib.import_module("libkoiki.core.security_config")
    module = importlib.reload(module)

    module.update_config(enable_cors=False, max_devices_per_user=3)

    config = module.get_security_config()
    assert config.enable_cors is False
    assert config.max_devices_per_user == 3
    assert config.login_security.max_attempts_per_email == 5
