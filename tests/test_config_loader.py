import iot_lab.config as config_module


def test_load_config_without_yaml_dependency(tmp_path, monkeypatch):
    config_text = (
        "serial:\n"
        "  port: /dev/ttyUSB9\n"
        "  baudrate: 57600\n"
        "mqtt:\n"
        "  host: broker\n"
        "  port: 1884\n"
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_text)
    monkeypatch.setenv("IOT_LAB_CONFIG", str(config_path))
    config_module.load_config.cache_clear()  # type: ignore[attr-defined]
    cfg = config_module.load_config()
    assert cfg["serial"]["port"] == "/dev/ttyUSB9"
    assert cfg["serial"]["baudrate"] == 57600
    assert cfg["mqtt"]["port"] == 1884
