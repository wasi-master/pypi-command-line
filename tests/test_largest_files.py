def test_largest_files(runner):
    result = runner.run("pypi largest-files")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_largest_files_help(runner):
    result = runner.run("pypi largest-files --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
