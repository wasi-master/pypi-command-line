import re


def test_new_packages(runner):
    result = runner.run("pypi new-packages")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_new_packages_with_author(runner):
    result = runner.run("pypi new-packages ---author")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert re.search(r"\S+@\S+\.\S+", output)


def test_new_packages_without_link(runner):
    result = runner.run("pypi new-packages --no--link")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert " ┃ Link " not in output, "Link was found"


def test_new_packages_help(runner):
    result = runner.run("pypi new-packages --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
