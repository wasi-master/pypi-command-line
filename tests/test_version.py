def test_version(runner):
    result = runner.run("pypi version")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_version_with_another_package(runner):
    result = runner.run("pypi version charinfo")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_version_with_limit(runner):
    result = runner.run("pypi version discord --limit 1")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").strip()
    assert output, "No output was gotten"  # Assert if a output was returned
    assert len(output.splitlines()) == 2, "More that one item was gotten"


def test_version_help_message(runner):
    result = runner.run("pypi version --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
