from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import read_json, slugify, write_json


DEFAULT_STORE = Path(".mediinsight/projects.json")


def project_key(config: dict[str, Any]) -> str:
    explicit = str(config.get("project_id", "")).strip()
    if explicit:
        return slugify(explicit)
    return slugify(str(config.get("product_name") or config.get("project") or "meditherapy"))


def load_projects(path: Path = DEFAULT_STORE) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "projects": {}}
    data = read_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("projects"), dict):
        raise ValueError(f"Invalid MediInsight project store: {path}")
    return data


def get_project(name: str, path: Path = DEFAULT_STORE) -> dict[str, Any]:
    key = slugify(name)
    project = load_projects(path)["projects"].get(key)
    if not project:
        raise KeyError(f"Unknown project '{name}'. Save its URLs first.")
    return dict({"project_id": key}, **project)


def list_projects(path: Path = DEFAULT_STORE) -> list[dict[str, Any]]:
    projects = load_projects(path)["projects"]
    return [dict({"project_id": key}, **value) for key, value in sorted(projects.items())]


def save_project(config: dict[str, Any], path: Path = DEFAULT_STORE) -> dict[str, Any]:
    key = project_key(config)
    store = load_projects(path)
    current = dict(store["projects"].get(key, {}))
    channels = merge_channels(current.get("channels", []), config.get("channels", []))
    profile = {
        "project": config.get("project") or current.get("project") or key,
        "product_name": config.get("product_name") or current.get("product_name") or key,
        "channels": channels,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    image_url = config.get("product_image_url") or current.get("product_image_url")
    if image_url:
        profile["product_image_url"] = image_url
    store["projects"][key] = profile
    write_json(path, store)
    return dict({"project_id": key}, **profile)


def merge_config(profile: dict[str, Any], run_config: dict[str, Any]) -> dict[str, Any]:
    merged = dict(profile)
    merged.update({key: value for key, value in run_config.items() if key != "channels"})
    merged["channels"] = merge_channels(profile.get("channels", []), run_config.get("channels", []))
    return merged


def merge_channels(existing: list[dict], incoming: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for channel in [*existing, *incoming]:
        if not channel.get("url"):
            continue
        identity = str(channel.get("name") or channel["url"])
        merged[identity] = {
            "name": identity,
            "type": channel.get("type", "public_page"),
            "url": channel["url"],
        }
    return list(merged.values())
