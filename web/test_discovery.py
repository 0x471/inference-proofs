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
