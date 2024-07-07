#!/usr/bin/env python3

"""Publish firmware to S3 bucket."""

import argparse
import hashlib
import json
from pathlib import Path
import os
import sys
import urllib.parse

import s3fs
import esphome.const
import esphome.core
import esphome.config
import esphome.__main__


def get_cpp_def(key: str):
    for define in esphome.core.CORE.defines:
        if define.name == key:
            return define.value
    return None


def md5_file(path: Path) -> str:
    hasher = hashlib.md5()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


def get_manifest_contents():
    md5 = md5_file(Path(esphome.core.CORE.firmware_bin))
    version = esphome.const.__version__
    return {
        "name": esphome.core.CORE.friendly_name or esphome.core.CORE.name,
        "version": version,
        "builds": [
            {
                "chipFamily": get_cpp_def("ESPHOME_VARIANT").string,
                "ota": {
                    "md5": md5,
                    "path": f"{version}-{esphome.core.CORE.name}.{md5}.bin",
                },
            },
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--esphome-data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / ".esphome",
    )
    parser.add_argument("yaml_path", type=Path)
    opts = parser.parse_args()

    os.environ.setdefault("ESPHOME_DATA_DIR", str(opts.esphome_data_dir))
    esphome.core.CORE.config_path = str(opts.yaml_path)
    esphome.core.CORE.config = esphome.config.read_config({})
    esphome.__main__.generate_cpp_contents(esphome.core.CORE.config)

    manifest = get_manifest_contents()

    update_configs = esphome.core.CORE.config.get("update", [])
    update_configs = [x for x in update_configs if x["platform"] == "http_request"]

    if not update_configs:
        print(
            "No http_request update configs, nothing to upload.",
            file=sys.stderr,
        )
        return 0

    manifest_url = urllib.parse.urlparse(update_configs[0]["source"])
    endpoint_url = manifest_url._replace(path="").geturl()
    s3 = s3fs.S3FileSystem(endpoint_url=endpoint_url)

    manifest_uri = f"s3://{manifest_url.path}"
    firmware_file_name = manifest["builds"][0]["ota"]["path"]
    firmware_uri = f"s3://{Path(manifest_url.path).with_name(firmware_file_name)}"

    s3.put(esphome.core.CORE.firmware_bin, firmware_uri)
    with s3.open(manifest_uri, "w", encoding="utf-8") as f:
        json.dump(manifest, f)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
