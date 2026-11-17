"""Page CSS must retain shared rules and fail closed when its prepared source is stale."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


def test_page_styles_keep_shared_rules(board_site: Any) -> None:
    build = board_site.build
    sections = json.loads((board_site.out / "styles.json").read_text())["sections"]
    home = build.page_styles("home")
    learn = build.page_styles("system learnpage")
    scale = build.page_styles("system scalepage")
    system = build.page_styles("system syspage")
    assert ".gpk{" in home  # Glossary previews also appear outside Learn.
    assert ".ln{" in home  # Scale and 404 cards share name typography.
    for part in sections:
        css, scope = part["css"], part["scope"]
        if scope == "shared":
            assert all(css in page for page in (home, learn, scale, system))
        else:
            assert css not in home
            assert (css in learn) == (scope in {"learn", "details"})
            assert (css in scale) == (scope in {"scale", "details"})
            assert (css in system) == (scope == "details")
    assert len(home) < sum(len(p["css"]) for p in sections) * 0.6


def test_style_source_digest_is_checked(board_site: Any, tmp_path: Path) -> None:
    for name in ("words.css", "words.js", "styles.json", "fonts"):
        src = board_site.out / name
        if src.is_dir():
            shutil.copytree(src, tmp_path / name)
        else:
            shutil.copyfile(src, tmp_path / name)
    build = board_site.build
    build.setup(build.V, tmp_path)
    try:
        (tmp_path / "words.css").write_text("body { color: red; }")
        with pytest.raises(RuntimeError, match=r"styles\.json is stale"):
            build.page_styles("home")
    finally:
        build.setup(build.V, board_site.out)


def test_prepared_styles_reproduce(board_site: Any) -> None:
    web = Path(__file__).parent
    if not shutil.which("node") or not (web / "node_modules/esbuild").exists():
        pytest.skip("npm ci in web/ installs the CSS preparer")
    subprocess.run(["node", str(web / "styles.mjs")], cwd=board_site.out, check=True)
    assert (board_site.out / "styles.json").read_bytes() == (web / "styles.json").read_bytes()
