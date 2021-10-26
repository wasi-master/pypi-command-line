import re


def test_new_releases(runner):
    result = runner.run("pypi new-releases")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_new_releases_with_author(runner):
    result = runner.run("pypi new-releases ---author")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert re.search(r"\S+@\S+\.\S+", output)


def test_new_releases_without_link(runner):
    result = runner.run("pypi new-releases --no--link")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert " ┃ Link " not in output, "Link was found"


def test_new_releases_help(runner):
    result = runner.run("pypi new-releases --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
