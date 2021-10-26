import re


def test_browse(runner):
    result = runner.run("pypi browse numpy --url-only")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert re.search(r"(https?:\/\/)?([\w\-])+\.{1}([a-zA-Z]{2,63})([\/\w-]*)*\/?\??([^#\n\r]*)?#?([^\n\r]*)", output)


def test_browse_help_message(runner):
    result = runner.run("pypi browse --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
