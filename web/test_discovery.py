"""Crawler metadata must describe the generated pages and survive deployment headers."""

import base64
import hashlib
import json
import re
from typing import Any
from xml.etree import ElementTree


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
        digest = base64.b64encode(hashlib.sha256(block[1].encode()).digest()).decode()
        assert f"'sha256-{digest}'" in headers["Content-Security-Policy"]
    assert urls == expected
    robots = (out / "robots.txt").read_text()
    assert "Allow: /" in robots
    assert "Sitemap: https://www.inferenceproofs.ai/sitemap.xml" in robots
    assert "robots.txt sitemap.xml" in config["buildCommand"]
    assert "npm run assets" in config["buildCommand"]
