def test_wheels(runner):
    result = runner.run("pypi wheels charinfo")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_version(runner):
    result = runner.run("pypi wheels charinfo 0.1.0")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_version_shortened(runner):
    result = runner.run("pypi wheels charinfo 0.1")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_version_alt(runner):
    result = runner.run("pypi wheels charinfo==0.1.0")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_version_shortened_alt(runner):
    result = runner.run("pypi wheels charinfo==0.1")
    output = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_supported_only(runner):
    result = runner.run("pypi wheels charinfo --supported-only")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_help_message(runner):
    result = runner.run("pypi wheels --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
