"""Move the three existing releases to the Actions bot without changing tags."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import quote

BOT = "github-actions[bot]"
REPO = "ai-aimbot/AIMr"
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "release-repair.json").read_text())
BACKUP = Path(os.environ.get("REPAIR_DIR", str(Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "release-repair")))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def api(path, method="GET", data=None):
    args = ["gh", "api", f"repos/{REPO}/{path}", "--method", method]
    if data is not None:
        args += ["--input", "-"]
    result = subprocess.run(args, input=json.dumps(data) if data is not None else None,
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def release(tag):
    matches = [r for r in api("releases?per_page=100") if r["tag_name"] == tag]
    require(len(matches) <= 1, f"More than one release for {tag}")
    return matches[0] if matches else None


def tag_sha(tag):
    return api(f"git/ref/tags/{quote(tag, safe='')}")["object"]["sha"]


def verify_tags():
    for tag, sha in MANIFEST["tags"].items():
        require(tag_sha(tag) == sha, f"Tag changed: {tag}")


def verify_file(asset, directory=None):
    path = (directory or BACKUP) / asset["name"]
    require(path.is_file(), f"Backup is missing: {path.name}")
    require(path.stat().st_size == asset["size"], "Backup size does not match")
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(block)
    digest = "sha256:" + checksum.hexdigest()
    require(digest == asset["digest"], "Backup checksum does not match")


def verify_metadata(actual, expected):
    for key in ("name", "body", "prerelease", "target_commitish"):
        require((actual.get(key) or "") == (expected.get(key) or ""),
                f"Release changed: {expected['tag_name']} / {key}")
    require(not actual.get("immutable"), "Release is immutable")


def verify_assets(actual, expected, complete):
    want = {a["name"]: a for a in expected["assets"]}
    got = {a["name"]: a for a in actual["assets"]}
    require(len(got) == len(actual["assets"]), "Duplicate asset names")
    require(set(got) <= set(want), "Unexpected release asset")
    if complete:
        require(set(got) == set(want), "Release asset is missing")
    for name, asset in got.items():
        if actual["author"]["login"] == BOT:
            require(asset["uploader"]["login"] == BOT, "Asset uploader is not the bot")
            if not complete and actual["draft"] and asset["state"] == "starter" and asset["size"] == 0:
                continue
        for key in ("size", "digest", "content_type", "label"):
            require(asset.get(key) == want[name].get(key), f"Asset changed: {name} / {key}")


def verify_state(actual, expected):
    if actual is None:
        return
    require(actual["id"] == expected["original_id"] or actual["author"]["login"] == BOT,
            "Release has an unexpected publisher")
    verify_metadata(actual, expected)
    verify_assets(actual, expected, complete=actual["id"] == expected["original_id"])
    if actual["id"] == expected["original_id"]:
        require(not actual["draft"], "Original release is now a draft")


def backup():
    require(os.environ.get("GH_REPO") == REPO, "Wrong repository")
    BACKUP.mkdir(parents=True, exist_ok=True)
    run_id = os.environ.get("BACKUP_RUN_ID", "").strip()
    if run_id:
        require(run_id.isdecimal(), "Backup run ID must contain digits only")
        subprocess.run(["gh", "run", "download", run_id, "--repo", REPO,
                        "--name", "release-repair-backup", "--dir", str(BACKUP)], check=True)
    verify_tags()
    for expected in MANIFEST["releases"]:
        actual = release(expected["tag_name"])
        verify_state(actual, expected)
        for asset in expected["assets"]:
            path = BACKUP / asset["name"]
            if not path.exists() and os.environ.get("RUNNER_ENVIRONMENT") == "self-hosted":
                source = Path(os.environ["REPAIR_OFFLINE_BACKUP"])
                verify_file(asset, source)
                shutil.copy2(source / asset["name"], path)
            if not path.exists():
                require(actual is not None, "Supply a prior backup run ID to restore this release")
                current = next((a for a in actual["assets"] if a["name"] == asset["name"]), None)
                require(current is not None, "Supply a prior backup run ID to restore this asset")
                with path.open("wb") as output:
                    subprocess.run(["gh", "api", f"repos/{REPO}/releases/assets/{current['id']}",
                                    "-H", "Accept: application/octet-stream"], stdout=output, check=True)
            verify_file(asset)
    (BACKUP / "manifest.json").write_text(json.dumps(MANIFEST, indent=2) + "\n")
    print("Backup verified. All tag SHAs match.", flush=True)


def probe():
    tag = MANIFEST["probe_tag"]
    require(release(tag) is None, "The test tag already has a release")
    created = api("releases", "POST", {"tag_name": tag, "name": "Publisher check",
                                       "draft": True, "make_latest": "false"})
    try:
        require(created["author"]["login"] == BOT, "Token does not publish as the Actions bot")
        require(created["draft"], "Publisher check must stay a draft")
    finally:
        api(f"releases/{created['id']}", "DELETE")
    print("Actions bot publisher check passed.", flush=True)


def upload(release_id, asset):
    url = f"https://uploads.github.com/repos/{REPO}/releases/{release_id}/assets?name={quote(asset['name'])}"
    if asset.get("label"):
        url += "&label=" + quote(asset["label"])
    result = subprocess.run(["gh", "api", url, "--method", "POST", "--input",
                             str(BACKUP / asset["name"]), "-H", "Content-Type: " + asset["content_type"]],
                            text=True, capture_output=True, check=True)
    created = json.loads(result.stdout)
    require(created["uploader"]["login"] == BOT, "Upload did not use the Actions bot")


def repair():
    require(os.environ.get("GITHUB_ACTIONS") == "true", "Run the repair through GitHub Actions")
    require(os.environ.get("GITHUB_REPOSITORY") == REPO, "Wrong repository")
    require(json.loads((BACKUP / "manifest.json").read_text()) == MANIFEST, "Backup manifest changed")
    durable = None
    if os.environ.get("RUNNER_ENVIRONMENT") == "self-hosted":
        require(os.environ.get("REPAIR_OFFLINE_BACKUP"), "A private backup path is required on a local runner")
        durable = Path(os.environ["REPAIR_OFFLINE_BACKUP"]).resolve()
        require(durable != BACKUP.resolve(), "The durable backup must be separate from the job backup")
        require(Path(os.environ["GITHUB_WORKSPACE"]).resolve() not in (durable, *durable.parents),
                "The durable backup must be outside the checkout")
        require(Path(os.environ["RUNNER_TEMP"]).resolve() not in (durable, *durable.parents),
                "The durable backup must be outside the job temporary directory")
        require(json.loads((durable / "manifest.json").read_text()) == MANIFEST, "Private backup manifest changed")
        for expected in MANIFEST["releases"]:
            for asset in expected["assets"]:
                verify_file(asset, durable)
    else:
        artifacts = api(f"actions/runs/{os.environ['GITHUB_RUN_ID']}/artifacts")["artifacts"]
        require(any(a["name"] == "release-repair-backup" and not a["expired"] for a in artifacts),
                "A saved workflow backup is required before changing releases")
    verify_tags()
    for expected in MANIFEST["releases"]:
        verify_state(release(expected["tag_name"]), expected)
        for asset in expected["assets"]:
            verify_file(asset)
    probe()
    receipt = []
    for expected in MANIFEST["releases"]:
        tag = expected["tag_name"]
        verify_tags()
        current = release(tag)
        verify_state(current, expected)
        if current and current["id"] == expected["original_id"]:
            api(f"releases/{current['id']}", "DELETE")
            current = None
        if current is None:
            data = {k: expected[k] for k in ("tag_name", "target_commitish", "name", "body", "prerelease")}
            current = api("releases", "POST", {**data, "draft": True, "make_latest": "false"})
        require(current["author"]["login"] == BOT, "Replacement publisher is not the bot")
        for asset in expected["assets"]:
            existing = next((a for a in current["assets"] if a["name"] == asset["name"]), None)
            if existing and existing["state"] == "starter" and existing["size"] == 0 and current["draft"]:
                api(f"releases/assets/{existing['id']}", "DELETE")
                existing = None
            if existing is None:
                upload(current["id"], asset)
        current = api(f"releases/{current['id']}")
        verify_metadata(current, expected)
        verify_assets(current, expected, complete=True)
        api(f"releases/{current['id']}", "PATCH", {
            "draft": False, "make_latest": "true" if tag == MANIFEST["latest_tag"] else "false"})
        current = api(f"releases/{current['id']}")
        require(not current["draft"], "Replacement is still a draft")
        receipt.append({"tag": tag, "id": current["id"], "publisher": current["author"]["login"],
                        "url": current["html_url"], "assets": [
                            {k: a[k] for k in ("name", "size", "digest", "browser_download_url")}
                            for a in current["assets"]]})
        (BACKUP / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if durable:
            (durable / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"Verified bot release: {tag} ({len(receipt)} / {len(MANIFEST['releases'])})", flush=True)
    verify_tags()
    require(api("releases/latest")["tag_name"] == MANIFEST["latest_tag"], "Latest release changed")
    print("All releases, assets, and tags verified.", flush=True)


if __name__ == "__main__":
    require(len(sys.argv) == 2 and sys.argv[1] in ("backup", "repair"), "Use backup or repair")
    globals()[sys.argv[1]]()
