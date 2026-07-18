def test_search_is_deprecated(runner):
    """The search command is disabled because PyPI blocks the requests; it should say so."""
    result = runner.run("pypi search charinfo")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert "not available" in output
    assert "rsearch" in output


def test_search_help_message(runner):
    result = runner.run("pypi search --help")
    output = result.stdout.decode("utf-8")
    assert "Search for a package" in output
