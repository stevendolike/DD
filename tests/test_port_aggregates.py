import ipaddress
import json
import subprocess
import sys
import uuid
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPLIT_JSON = REPO_ROOT / "split_json.py"
REFORMAT = REPO_ROOT / "reformat.py"
SYSTEM_FILES = {"_all.txt", "_all_443.txt"}
REPORTED_PORTS = (2053, 2083, 2087, 2096, 443, 8443)
DYNAMIC_PORT = 9443


def _fixture_data():
    all_ports = [*REPORTED_PORTS, DYNAMIC_PORT]
    return [
        {
            "ip": "10.0.0.10",
            "port": all_ports,
            "meta": {
                "country": "us",
                "asOrganization": "Zeta Network",
                "asn": 0,
                "clientIp": "",
            },
        },
        {
            "ip": "10.0.0.2",
            "port": all_ports,
            "meta": {
                "country": "US",
                "asOrganization": "Alpha Network",
                "asn": 0,
                "clientIp": "",
            },
        },
        {
            "ip": "10.0.0.2",
            "port": [2053, 443, DYNAMIC_PORT],
            "meta": {
                "country": "US",
                "asOrganization": "Alpha Network",
                "asn": 0,
                "clientIp": "",
            },
        },
        {
            "ip": "2001:db8::2",
            "port": [2053, 443, DYNAMIC_PORT],
            "meta": {
                "country": "ca",
                "asOrganization": "Gamma Network",
                "asn": 0,
                "clientIp": "",
            },
        },
        {
            "ip": "192.0.2.20",
            "port": [2053, 443],
            "meta": {
                "country": "CA",
                "asOrganization": "Delta Network",
                "asn": 0,
                "clientIp": "",
            },
        },
        {
            "ip": "192.0.2.3",
            "port": [2053, 443],
            "meta": {
                "country": "CA",
                "asOrganization": "Epsilon Network",
                "asn": 0,
                "clientIp": "",
            },
        },
    ]


def _make_fixture(tmp_path):
    fixture = tmp_path / f"dd-port-aggregates-{uuid.uuid4().hex}"
    fixture.mkdir()
    with (fixture / "all.json").open("w", encoding="utf-8", newline="\n") as stream:
        json.dump({"data": _fixture_data()}, stream)
        stream.write("\n")
    return fixture


def _run(script, fixture):
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=fixture,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        f"{script.name} failed with {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return result


def _read_lf_lines(path):
    raw = path.read_bytes()
    assert raw.endswith(b"\n")
    assert b"\r" not in raw
    return raw.decode("utf-8").splitlines()


def _expected_by_port():
    expected = defaultdict(set)
    for item in _fixture_data():
        country = item["meta"]["country"].upper()
        for port in item["port"]:
            expected[port].add(f"{item['ip']}#{country}")
    return expected


def _aggregate_key(entry):
    ip, country = entry.rsplit("#", 1)
    return country, int(ipaddress.ip_address(ip))


def _country_org_union(port_dir):
    entries = set()
    for country_dir in sorted(path for path in port_dir.iterdir() if path.is_dir()):
        for org_file in sorted(country_dir.glob("*.txt")):
            if org_file.name in SYSTEM_FILES:
                continue
            entries.update(
                f"{ip}#{country_dir.name}"
                for ip in org_file.read_text(encoding="utf-8").splitlines()
                if ip
            )
    return entries


def test_split_json_builds_exact_top_level_aggregate_for_every_dynamic_port(tmp_path):
    fixture = _make_fixture(tmp_path)

    _run(SPLIT_JSON, fixture)

    expected_by_port = _expected_by_port()
    assert set(expected_by_port) == {*REPORTED_PORTS, DYNAMIC_PORT}
    for port, expected_set in expected_by_port.items():
        port_dir = fixture / f"regions_json_{port}"
        aggregate = port_dir / "_all.txt"
        lines = _read_lf_lines(aggregate)
        assert lines == sorted(expected_set, key=_aggregate_key)
        assert set(lines) == _country_org_union(port_dir)
        assert len(lines) == len(set(lines))
        assert all(
            ipaddress.ip_address(line.rsplit("#", 1)[0])
            and line.rsplit("#", 1)[1] in {"CA", "US"}
            for line in lines
        )
        assert not (port_dir / "_all_443.txt").exists()

    assert _read_lf_lines(fixture / "regions_json_2053" / "_all.txt") == [
        "192.0.2.3#CA",
        "192.0.2.20#CA",
        "2001:db8::2#CA",
        "10.0.0.2#US",
        "10.0.0.10#US",
    ]


def _snapshot_paths(root, paths):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(paths)
    }


def _port_country_snapshot(fixture, ports):
    paths = []
    for port in ports:
        paths.extend((fixture / f"regions_json_{port}").glob("*/*.txt"))
    return _snapshot_paths(fixture, paths)


def _port_aggregate_snapshot(fixture, ports):
    return _snapshot_paths(
        fixture,
        [fixture / f"regions_json_{port}" / "_all.txt" for port in ports],
    )


def _generated_snapshot(fixture):
    paths = [fixture / "stats.json"]
    paths.extend(
        path
        for path in fixture.rglob("*.txt")
        if path.relative_to(fixture).parts[0].startswith("regions_json")
    )
    return _snapshot_paths(fixture, paths)


def test_reformat_rebuilds_dynamic_port_aggregates_idempotently(tmp_path):
    fixture = _make_fixture(tmp_path)
    ports = sorted(_expected_by_port())

    _run(SPLIT_JSON, fixture)
    expected_aggregates = _port_aggregate_snapshot(fixture, ports)
    expected_country_files = _port_country_snapshot(fixture, ports)
    expected_all_443 = _snapshot_paths(fixture, fixture.rglob("_all_443.txt"))

    _run(SPLIT_JSON, fixture)
    assert _port_aggregate_snapshot(fixture, ports) == expected_aggregates
    assert _port_country_snapshot(fixture, ports) == expected_country_files
    assert _snapshot_paths(fixture, fixture.rglob("_all_443.txt")) == expected_all_443

    for relative_path in expected_aggregates:
        (fixture / relative_path).unlink()

    _run(REFORMAT, fixture)
    assert _port_aggregate_snapshot(fixture, ports) == expected_aggregates
    assert _port_country_snapshot(fixture, ports) == expected_country_files
    assert _snapshot_paths(fixture, fixture.rglob("_all_443.txt")) == expected_all_443

    once_reformatted = _generated_snapshot(fixture)
    _run(REFORMAT, fixture)
    assert _generated_snapshot(fixture) == once_reformatted
