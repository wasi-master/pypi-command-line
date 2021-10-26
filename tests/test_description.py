def test_description(runner):
    result = runner.run("pypi description django")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_description_from_github(runner):
    result = runner.run("pypi description django --force-github")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_description_help_message(runner):
    result = runner.run("pypi description --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
