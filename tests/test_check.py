import os
import subprocess

def test_check_help(runner):
    result = runner.run("pypi check --help")
    output = result.stdout.decode("utf-8")
    assert "Check a requirements.txt or pyproject.toml" in output


def test_check_file_not_found(runner):
    try:
        runner.run("pypi check non_existent_file.txt")
        assert False, "Should have failed with a file not found error"
    except subprocess.CalledProcessError as e:
        assert e.returncode == 1
        assert b"not found" in e.stdout or b"not found" in e.stderr


def test_check_requirements_txt(runner, tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("charinfo==0.1.0\nurllib3\n# comment line\n")
    
    result = runner.run(f"pypi check {req_file}")
    output = result.stdout.decode("utf-8")
    assert "charinfo" in output
    assert "urllib3" in output
    assert "Specified" in output
    assert "Latest" in output


def test_check_pyproject_toml_pep621(runner, tmp_path):
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text("""
[project]
name = "test-pkg"
version = "0.0.1"
dependencies = [
    "charinfo>=0.1.0",
]
""")
    
    result = runner.run(f"pypi check {pyproject_file}")
    output = result.stdout.decode("utf-8")
    assert "charinfo" in output
    assert "Specified" in output


def test_check_pyproject_toml_poetry(runner, tmp_path):
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text("""
[tool.poetry.dependencies]
python = "^3.8"
charinfo = "^0.1.0"
""")
    
    result = runner.run(f"pypi check {pyproject_file}")
    output = result.stdout.decode("utf-8")
    assert "charinfo" in output
    assert "Specified" in output


def test_check_json_output(runner, tmp_path):
    import json

    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.0.0\n")

    result = runner.run(f"pypi check {req_file} --json")
    records = json.loads(result.stdout.decode("utf-8"))
    assert len(records) == 1
    record = records[0]
    assert record["name"] == "requests"
    assert record["specified"] == "==2.0.0"
    assert record["error"] is None
    assert record["outdated"] is True
    assert record["wheel_support"] in ("supported", "no_wheels", "unsupported")
    assert record["last_updated"]  # ISO 8601 timestamp
    assert isinstance(record["abandoned"], bool)


def test_check_json_output_not_found(runner, tmp_path):
    import json

    req_file = tmp_path / "requirements.txt"
    req_file.write_text("this-package-definitely-does-not-exist-12345\n")

    result = runner.run(f"pypi check {req_file} --json")
    records = json.loads(result.stdout.decode("utf-8"))
    assert len(records) == 1
    assert records[0]["error"] == "not_found"
    assert records[0]["latest"] is None
