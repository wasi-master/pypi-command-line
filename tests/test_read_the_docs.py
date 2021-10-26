def test_read_the_docs(runner):
    result = runner.run("pypi read-the-docs --url-only django context")
    output = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
