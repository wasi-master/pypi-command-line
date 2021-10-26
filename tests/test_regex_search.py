import re


def test_regex_search(runner):
    result = runner.run("pypi regex-search discord-.+")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_regex_search_compact(runner):
    result = runner.run("pypi regex-search --compact discord-.+")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert re.search(r"(\d+)(,\s*[a-zA-Z0-9_-]+)*", output)


def test_regex_search_help_message(runner):
    result = runner.run("pypi regex-search --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
