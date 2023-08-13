#!/usr/bin/env python3

import json
import shlex
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO / ".github" / "workflows" / "ci.yml"


def find_models():
    for model_yaml in REPO.glob("models/*/*.yaml"):
        chip_name = model_yaml.parent.name
        model_name = model_yaml.stem
        yield f"model-{chip_name}-{model_name}", model_yaml


def _run(cmd):
    return {"run": " ".join(shlex.quote(str(x)) for x in cmd)}


def gen_yaml_job(path):
    return {
        "runs-on": "ubuntu-22.04",
        "steps": [
            {"uses": "actions/checkout@v3"},
            {
                "uses": "actions/setup-python@v4",
                "with": {"python-version": "3.10"},
            },
            _run(["pip", "install", "-r", "requirements.txt"]),
            _run(["esphome", "compile", path.relative_to(REPO)]),
        ],
    }


def gen_jobs():
    yaml_jobs = sorted(find_models())
    for job_name, yaml in yaml_jobs:
        yield job_name, gen_yaml_job(yaml)


def gen_toplevel():
    return {
        "name": "CI",
        "run-name": "Build all YAML files",
        "on": ["push", "pull-request"],
        "jobs": {k: v for k, v in gen_jobs()},
    }


def main():
    OUTPUT_FILE.write_text(
        json.dumps(gen_toplevel(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == '__main__':
    main()
