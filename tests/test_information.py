def test_information(runner):
    result = runner.run("pypi information rich")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_information_with_version(runner):
    result = runner.run("pypi information rich --version 1.0.0")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "1.0.0" in output


def test_information_with_version_alt_syntax(runner):
    result = runner.run("pypi information rich==1.0.0")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "1.0.0" in output


def test_information_with_classifiers(runner):
    result = runner.run("pypi information rich --show-classifiers")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "── Classifiers ──" in output, "Classifiers were not found where it should have been"


def test_information_without_project_urls(runner):
    result = runner.run("pypi information rich --hide-project-urls")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "─── Project URLs ───" not in output, "Project urls were found where it shouldn't have been"


def test_information_without_requirements(runner):
    result = runner.run("pypi information rich --hide-requirements")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "── Requirements ──" not in output, "requirements were found where it shouldn't have been"


def test_information_without_github(runner):
    result = runner.run("pypi information rich --hide-github")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "─── GitHub ──" not in output, "Github was found where it shouldn't have been"


def test_information_without_stats(runner):
    result = runner.run("pypi information rich --hide-stats")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "─── Downloads ───" not in output, "Statistics were found where it shouldn't have been"


def test_information_without_meta(runner):
    result = runner.run("pypi information rich --hide-meta")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "─── Meta ────" not in output, "Statistics were found where it shouldn't have been"


def test_information_help(runner):
    result = runner.run("pypi information --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
