import json
from app.jocky import compile_jocky, compile_jocky_to_json


def test_planner_basic_scan_plan():
    source = "scan processes where signed == false"
    plan = compile_jocky(source)

    assert plan == {
        "version": "1",
        "statements": [
            {
                "operation": "scan",
                "target": "processes",
                "where": {
                    "field": "signed",
                    "operator": "eq",
                    "value": False,
                },
            }
        ],
    }


def test_planner_and_conditions_flattening():
    source = """
    scan processes
    where signed == false
    and network_connections > 0
    """
    plan = compile_jocky(source)

    assert plan == {
        "version": "1",
        "statements": [
            {
                "operation": "scan",
                "target": "processes",
                "where": {
                    "operator": "and",
                    "conditions": [
                        {
                            "field": "signed",
                            "operator": "eq",
                            "value": False,
                        },
                        {
                            "field": "network_connections",
                            "operator": "gt",
                            "value": 0,
                        },
                    ],
                },
            }
        ],
    }


def test_planner_full_specification_example():
    source = """
    scan processes
    where signed == false
    and network_connections > 0

    collect autoruns, scheduled_tasks

    hash files in "%TEMP%"
    check against reputation

    flag when signed == false
    severity = high

    report to server
    """
    plan = compile_jocky(source)

    expected = {
        "version": "1",
        "statements": [
            {
                "operation": "scan",
                "target": "processes",
                "where": {
                    "operator": "and",
                    "conditions": [
                        {
                            "field": "signed",
                            "operator": "eq",
                            "value": False,
                        },
                        {
                            "field": "network_connections",
                            "operator": "gt",
                            "value": 0,
                        },
                    ],
                },
            },
            {
                "operation": "collect",
                "targets": ["autoruns", "scheduled_tasks"],
            },
            {
                "operation": "hash",
                "target": "files",
                "path": "%TEMP%",
                "check_against": "reputation",
            },
            {
                "operation": "flag",
                "condition": {
                    "field": "signed",
                    "operator": "eq",
                    "value": False,
                },
                "severity": "high",
            },
            {
                "operation": "report",
                "destination": "server",
            },
        ],
    }
    assert plan == expected


def test_planner_json_serialization():
    source = "scan processes where name contains 'powershell'"
    json_str = compile_jocky_to_json(source)
    parsed = json.loads(json_str)

    assert parsed["version"] == "1"
    assert parsed["statements"][0]["operation"] == "scan"
    assert parsed["statements"][0]["where"]["operator"] == "contains"
    assert parsed["statements"][0]["where"]["value"] == "powershell"
