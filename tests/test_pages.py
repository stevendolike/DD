from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest

import gen_pages


NESTED_DIRS = [
    "regions_json",
    "regions_json_2053",
    "regions_json_2083",
    "regions_json_2087",
    "regions_json_2096",
    "regions_json_443",
    "regions_json_8443",
]


@pytest.fixture
def generated_site(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo_root = tmp_path / "server" / "fixture" / "repo" / "main"
    repo_root.mkdir(parents=True)

    stats = {}
    expected = {}
    for index, directory in enumerate(NESTED_DIRS, start=1):
        country_lines = [f"192.0.2.{index}#HK", f"2001:db8::{index}#HK"]
        stats[directory] = {"HK": {"Fixture Carrier": len(country_lines)}}
        country_file = repo_root / directory / "HK" / "_all.txt"
        country_file.parent.mkdir(parents=True)
        country_file.write_text("\n".join(country_lines) + "\n", encoding="utf-8", newline="\n")
        aggregate_file = repo_root / directory / "_all.txt"
        aggregate_file.write_text("\n".join(country_lines) + "\n", encoding="utf-8", newline="\n")
        expected[directory] = country_lines

    flat_dir = "regions_json_preferred_asn"
    flat_lines = ["198.51.100.1:443#US", "198.51.100.2:2053#US"]
    stats[flat_dir] = {"US": len(flat_lines)}
    flat_root = repo_root / flat_dir
    flat_root.mkdir(parents=True)
    (flat_root / "US.txt").write_text("\n".join(flat_lines) + "\n", encoding="utf-8", newline="\n")
    (flat_root / "_all.txt").write_text("\n".join(flat_lines) + "\n", encoding="utf-8", newline="\n")
    expected[flat_dir] = flat_lines

    zero_dir = "regions_json_residential_443"
    zero_lines = ["203.0.113.10#GB", "203.0.113.11#GB"]
    stats[zero_dir] = {"GB": len(zero_lines), "ZZ": 0}
    zero_root = repo_root / zero_dir
    zero_root.mkdir(parents=True)
    (zero_root / "GB.txt").write_text("\n".join(zero_lines) + "\n", encoding="utf-8", newline="\n")
    (zero_root / "_all.txt").write_text("\n".join(zero_lines) + "\n", encoding="utf-8", newline="\n")
    expected[zero_dir] = zero_lines

    (repo_root / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False), encoding="utf-8", newline="\n"
    )

    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(gen_pages, "REPO", "fixture/repo")
    monkeypatch.setattr(gen_pages, "BRANCH", "main")
    gen_pages.main()

    return {
        "server_root": tmp_path / "server",
        "repo_root": repo_root,
        "expected": expected,
    }


@contextmanager
def serve_directory(root: Path):
    class RecordingHandler(SimpleHTTPRequestHandler):
        records = []

        def send_response(self, code, message=None):
            self.records.append((urlsplit(self.path).path, code))
            super().send_response(code, message)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(RecordingHandler, directory=str(root))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", RecordingHandler.records
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@contextmanager
def available_browser():
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        pytest.skip(f"browser-only check: Playwright is not installed ({exc})")

    with sync_playwright() as playwright:
        attempts = [({}, "bundled Chromium"), ({"channel": "chrome"}, "Chrome"), ({"channel": "msedge"}, "Edge")]
        errors = []
        browser = None
        for options, label in attempts:
            try:
                browser = playwright.chromium.launch(headless=True, **options)
                break
            except PlaywrightError as exc:
                errors.append(f"{label}: {exc}")
        if browser is None:
            pytest.skip("browser-only check: no supported browser is installed; " + " | ".join(errors))
        try:
            yield browser
        finally:
            browser.close()


def wait_for_detail(page):
    page.wait_for_function(
        """() => {
            const body = document.getElementById("d-body");
            return body.querySelector("#list") || body.textContent.includes("載入失敗");
        }""",
        timeout=5000,
    )


def assert_rendered_lines(page, expected, records):
    wait_for_detail(page)
    body = page.locator("#d-body")
    assert body.locator("#list").count() == 1, (
        f"detail did not render a real file response: {body.inner_text()!r}; "
        f"HTTP records={records!r}"
    )
    assert body.locator("#list").inner_text().splitlines() == expected
    assert body.locator("#cnt").inner_text() == f"· 顯示 {len(expected)} / {len(expected)} 條"


def test_browser_routes_nested_and_flat_country_files_and_tracks_raw_link(generated_site):
    with serve_directory(generated_site["server_root"]) as (base_url, records), available_browser() as browser:
        context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = context.new_page()

        def redirect_raw(route):
            source = urlsplit(route.request.url)
            target_base = urlsplit(base_url)
            local_url = urlunsplit(
                (target_base.scheme, target_base.netloc, source.path, source.query, "")
            )
            response = route.fetch(url=local_url)
            route.fulfill(response=response)

        page.route("https://raw.githubusercontent.com/**", redirect_raw)
        page.goto(base_url + "/fixture/repo/main/docs/index.html")

        for directory in NESTED_DIRS:
            expected = generated_site["expected"][directory]
            page.locator(f'.card[data-dir="{directory}"]').click()
            assert_rendered_lines(page, expected, records)
            assert page.locator("#d-raw").get_attribute("href") == (
                f"https://raw.githubusercontent.com/fixture/repo/main/{directory}/_all.txt"
            )
            assert page.locator('#d-body tbody a[target="_blank"]').get_attribute("href") == (
                f"https://raw.githubusercontent.com/fixture/repo/main/{directory}/HK/_all.txt"
            )

            page.locator('.lnk[data-cc="HK"]').click()
            assert_rendered_lines(page, expected, records)
            nested_path = f"/fixture/repo/main/{directory}/HK/_all.txt"
            assert (nested_path, 200) in records
            assert page.locator("#d-raw").get_attribute("href") == (
                f"https://raw.githubusercontent.com/fixture/repo/main/{directory}/HK/_all.txt"
            )

            page.locator("#btn-all").click()
            assert page.locator("#list").inner_text().splitlines() == expected
            assert page.locator("#d-raw").get_attribute("href") == (
                f"https://raw.githubusercontent.com/fixture/repo/main/{directory}/_all.txt"
            )

        flat_dir = "regions_json_preferred_asn"
        flat_expected = generated_site["expected"][flat_dir]
        page.locator(f'.card[data-dir="{flat_dir}"]').click()
        assert_rendered_lines(page, flat_expected, records)
        assert page.locator('#d-body tbody a[target="_blank"]').get_attribute("href") == (
            f"https://raw.githubusercontent.com/fixture/repo/main/{flat_dir}/US.txt"
        )
        page.locator('.lnk[data-cc="US"]').click()
        assert_rendered_lines(page, flat_expected, records)
        flat_path = f"/fixture/repo/main/{flat_dir}/US.txt"
        assert (flat_path, 200) in records
        assert page.locator("#d-raw").get_attribute("href") == (
            f"https://raw.githubusercontent.com/fixture/repo/main/{flat_dir}/US.txt"
        )

        page.locator("#q").fill("2053")
        assert page.locator("#list").inner_text().splitlines() == ["198.51.100.2:2053#US"]
        assert page.locator("#cnt").inner_text() == "· 顯示 1 / 2 條"
        page.locator("#btn-copy").click()
        page.wait_for_function('document.getElementById("toast").classList.contains("on")')
        assert page.evaluate("navigator.clipboard.readText()") == "198.51.100.2:2053#US"


def test_browser_omits_zero_entry_countries_and_reports_real_counts(generated_site):
    with serve_directory(generated_site["server_root"]) as (base_url, records), available_browser() as browser:
        page = browser.new_page()

        def redirect_raw(route):
            source = urlsplit(route.request.url)
            target_base = urlsplit(base_url)
            local_url = urlunsplit(
                (target_base.scheme, target_base.netloc, source.path, source.query, "")
            )
            response = route.fetch(url=local_url)
            route.fulfill(response=response)

        page.route("https://raw.githubusercontent.com/**", redirect_raw)
        page.goto(base_url + "/fixture/repo/main/docs/index.html")

        directory = "regions_json_residential_443"
        card = page.locator(f'.card[data-dir="{directory}"]')
        assert card.locator(".cc").inner_text() == "1 個國家／地區"
        card.click()
        assert_rendered_lines(page, generated_site["expected"][directory], records)
        assert page.locator("#d-body tbody tr").count() == 1
        assert page.locator('.lnk[data-cc="GB"]').count() == 1
        assert page.locator('.lnk[data-cc="ZZ"]').count() == 0
        assert not any(path.endswith("/ZZ.txt") for path, _status in records)


def test_generated_html_keeps_country_routing_in_one_stats_driven_helper(generated_site):
    html = (generated_site["repo_root"] / "docs" / "index.html").read_text(encoding="utf-8")

    assert html.count("function fileFor(dir, c, mode)") == 1
    assert 'typeof countryStats === "number" ? ".txt" : "/_all.txt"' in html
    assert 'fetchText(fileFor(curCat.dir, c, c))' in html
    assert 'href="${RAW}/${fileFor(curCat.dir, c, c)}"' in html
    assert 'fetchText(curCat.dir + "/" + c + ".txt")' not in html
    assert 'href="${RAW}/${curCat.dir}/${c}.txt"' not in html
