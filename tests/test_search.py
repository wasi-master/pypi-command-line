def test_search(runner):
    result = runner.run("pypi search charinfo")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_search_with_page(runner):
    result = runner.run("pypi search discord --page 2")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_search_help_message(runner):
    result = runner.run("pypi search --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
