#!/usr/bin/env python3

"""For each site, validate there's no devices with duplicate IP addresses."""

from pathlib import Path

import esphome.core
import esphome.config


REPO_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_DIR / "site"


class ValidationError(Exception):
    pass


def load_config(config_path: Path):
    esphome.core.CORE.config_path = config_path
    return esphome.config.read_config({})


def get_ip(config):
    wifi = config.get("wifi", {})
    manual_ip = wifi.get("manual_ip")
    if not manual_ip:
        return None
    return str(manual_ip["static_ip"])


def validate_no_duplicate_addresses(site_dir: Path):
    addresses = {}
    for config_path in site_dir.glob("*.yaml"):
        config = load_config(config_path)
        ip = get_ip(config)
        if not ip:
            raise ValidationError(f"{config_path} has no static IP address")
        if ip in addresses:
            raise ValidationError(
                f"{config_path} shares an IP address with {addresses[ip]}"
            )
        addresses[ip] = config_path


def main():
    for site_dir in SITE_DIR.glob("*/"):
        validate_no_duplicate_addresses(site_dir)


if __name__ == "__main__":
    main()
