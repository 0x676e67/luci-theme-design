#!/usr/bin/env python3
import re
import os
import sys
import hashlib

import requests

REPO = os.getenv("REPOSITORY", "netbirdio/netbird")
GITHUB_TOKEN = os.getenv("TOKEN")

session = requests.Session()


def fetch_latest_release():
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    res = session.get(
        f"https://api.github.com/repos/{REPO}/releases/latest",
        headers=headers,
    )
    res.raise_for_status()
    release = res.json()

    tag_name = release["tag_name"]
    # v1.0.0 -> 1.0.0
    pkg_version = tag_name[1:]
    tarball_url = f"https://github.com/{REPO}/archive/refs/tags/{tag_name}.tar.gz"

    res = session.get(tarball_url, headers=headers)
    hasher = hashlib.new("sha256")
    hasher.update(res.content)
    sha256 = hasher.hexdigest()
    return pkg_version, sha256


def main():
    version, sha256 = fetch_latest_release()
    if os.getenv("GITHUB_ACTIONS"):
        print(f"::set-output name=NETBIRD_VERSION::{version}")

    with open("netbird/Makefile") as f:
        makefile = f.read()

    makefile = re.sub(r"PKG_VERSION:=([^\n]+)", f"PKG_VERSION:={version}", makefile)
    makefile = re.sub(r"PKG_HASH:=([^\n]+)", f"PKG_HASH:={sha256}", makefile)

    with open("netbird/Makefile", "w") as f:
        f.write(makefile)
    return 0


if __name__ == "__main__":
    sys.exit(main())
