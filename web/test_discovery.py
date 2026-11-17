"""Crawler metadata must describe the generated pages and survive deployment headers."""

import base64
import hashlib
import html as html_lib
import json
import re
import runpy
import shutil
import subprocess
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import pytest


def test_discovery_matches_public_pages(board_site: Any) -> None:
    out = board_site.out
    config = json.loads((out / "vercel.json").read_text())
    headers = {h["key"]: h["value"] for h in config["headers"][0]["headers"]}
    assert "X-Robots-Tag" not in headers
    sitemap = ElementTree.fromstring((out / "sitemap.xml").read_text())
    urls = {node.text for node in sitemap.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
    expected = set()
    for page in out.glob("*.html"):
        html = page.read_text()
        assert '<p class="sr" role="status" aria-atomic="true" id="live">' in html
        if page.stem == "404":
            assert '<meta name="robots" content="noindex">' in html
            continue
        canonical = re.search(r'<link rel="canonical" href="([^"]+)">', html)
        assert canonical
        expected.add(canonical[1])
        block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html)
        assert block
        data = json.loads(block[1])
        assert data["url"] == canonical[1]
        assert data["@type"] == "WebPage"
        headings = re.findall(r'<h2\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h2>', html, re.S)
        assert len(data.get("hasPart", [])) == len(headings)
        for part, (anchor, label) in zip(data.get("hasPart", []), headings, strict=True):
            assert part == {
                "@type": "WebPageElement",
                "@id": f"{canonical[1]}#{anchor}",
                "name": html_lib.unescape(re.sub(r"<[^>]+>", "", label)),
            }
        digest = base64.b64encode(hashlib.sha256(block[1].encode()).digest()).decode()
        assert f"'sha256-{digest}'" in headers["Content-Security-Policy"]
    assert urls == expected
    robots = (out / "robots.txt").read_text()
    assert "Allow: /" in robots
    assert "Sitemap: https://www.inferenceproofs.ai/sitemap.xml" in robots
    assert "robots.txt sitemap.xml" in config["buildCommand"]
    assert "npm run assets" in config["buildCommand"]


def test_agent_guide_and_topics(board_site: Any) -> None:
    out = board_site.out
    guide = (out / "llms.txt").read_text()
    config = json.loads((out / "vercel.json").read_text())
    assert "llms.txt public/" in config["buildCommand"]
    assert "does not certify AI safety" in guide
    assert "not an enacted treaty" in guide
    for page in out.glob("*.html"):
        if page.stem == "404":
            continue
        html = page.read_text()
        block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html)
        assert block
        data = json.loads(block[1])
        assert f"]({data['url']}): {data['description']}" in guide
        for part in data.get("hasPart", []):
            assert f"  - [{part['name']}]({part['@id']})" in guide
        assert data["about"]
        assert data["primaryImageOfPage"]["url"].startswith("https://www.inferenceproofs.ai/og/")
        assert 'href="/llms.txt"' in html
        if page.stem != "index":
            crumbs = data["breadcrumb"]["itemListElement"]
            assert crumbs[0]["item"] == "https://www.inferenceproofs.ai/"
            assert crumbs[-1]["item"] == data["url"]
        if page.stem == "deployment":
            assert "AI treaty verification" in data["keywords"]
            assert "Hypothetical US-China AI agreement" in data["keywords"]
            assert "United States (US) and China" in html.split("<body", 1)[1]
            assert "not a description of an existing deal" in html
            assert "State A" not in html
        else:
            assert "AI treaty verification" not in data["keywords"]
        if page.stem in {"index", "scale", "checks"}:
            assert "NVIDIA H200" in data["keywords"]
        if page.stem == "checks":
            assert "NVIDIA H200" in html.split("<body", 1)[1]
    assert "/404" not in guide
    redirects = {r["source"]: r for r in config["redirects"]}
    assert redirects["/treaty"]["permanent"] is True
    assert redirects["/system"]["permanent"] is False


def test_production_assets_keep_search_entries(board_site: Any) -> None:
    web = Path(__file__).parent
    if not shutil.which("node") or not (web / "node_modules/esbuild").exists():
        pytest.skip("npm ci in web/ installs the production asset builder")
    subprocess.run(["node", str(web / "assets.mjs")], cwd=board_site.out, check=True)
    text = (board_site.out / "public/search.json").read_text()
    assert json.loads(text) == json.loads((board_site.out / "search.json").read_text())
    assert len(text.splitlines()) == 1
    for name in ("words.css", "words.js", "search.json"):
        assert (board_site.out / "public" / name).stat().st_size < (
            board_site.out / name
        ).stat().st_size


def test_preview_serves_discovery_files_only() -> None:
    deployed = runpy.run_path(str(Path(__file__).with_name("serve.py")))["DEPLOYED"]
    for name in ("llms.txt", "robots.txt", "sitemap.xml", "search.json"):
        assert deployed.fullmatch(name)
    for name in (".env", "_data/facts.json", "serve.py", "learn/index.yaml"):
        assert not deployed.fullmatch(name)
