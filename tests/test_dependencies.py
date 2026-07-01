"""Tests for the pypi dependencies command and _get_package_dependencies helper."""

import json
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from pypi_cli.__main__ import app, _get_package_dependencies


runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_info(name, version, requires_dist=None, summary=""):
    return {
        "name": name,
        "version": version,
        "summary": summary,
        "requires_dist": requires_dist or [],
    }


def _mock_response(info_dict, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = json.dumps({"info": info_dict})
    return resp


# ---------------------------------------------------------------------------
# Unit tests for _get_package_dependencies
# ---------------------------------------------------------------------------

class TestGetPackageDependencies:

    def test_no_deps(self):
        info = _make_info("pkg", "1.0")
        assert _get_package_dependencies(info, set()) == []

    def test_simple_dep(self):
        info = _make_info("pkg", "1.0", requires_dist=["requests>=2.0"])
        deps = _get_package_dependencies(info, set())
        assert len(deps) == 1
        assert deps[0].name == "requests"

    def test_marker_filters_out(self):
        import sys
        if sys.platform == "win32":
            pytest.skip("marker is True on win32")
        info = _make_info("pkg", "1.0", requires_dist=["pywin32 ; sys_platform == 'win32'"])
        deps = _get_package_dependencies(info, set())
        assert deps == []

    def test_extra_dep_excluded_without_extra(self):
        info = _make_info("pkg", "1.0", requires_dist=["cryptography ; extra == 'security'"])
        deps = _get_package_dependencies(info, set())
        assert deps == []

    def test_extra_dep_included_with_extra(self):
        info = _make_info("pkg", "1.0", requires_dist=["cryptography ; extra == 'security'"])
        deps = _get_package_dependencies(info, {"security"})
        assert len(deps) == 1
        assert deps[0].name == "cryptography"

    def test_invalid_requirement_is_skipped(self):
        info = _make_info("pkg", "1.0", requires_dist=["!!!invalid==="])
        deps = _get_package_dependencies(info, set())
        assert deps == []

    def test_none_requires_dist(self):
        info = _make_info("pkg", "1.0")
        info["requires_dist"] = None
        assert _get_package_dependencies(info, set()) == []


# ---------------------------------------------------------------------------
# Integration tests via CLI runner
# ---------------------------------------------------------------------------

class TestDependenciesCommand:

    def _patch_session_get(self, responses: dict):
        def fake_get(url, **kwargs):
            for name, data in responses.items():
                if f"/pypi/{name}/json" in url.lower():
                    if data is None:
                        resp = MagicMock()
                        resp.status_code = 404
                        resp.text = "{}"
                        return resp
                    return _mock_response(data)
            resp = MagicMock()
            resp.status_code = 404
            resp.text = "{}"
            return resp

        return patch("pypi_cli.__main__.session.get", side_effect=fake_get)

    def test_package_not_found(self):
        with self._patch_session_get({"totally-fake-pkg": None}):
            result = runner.invoke(app, ["dependencies", "totally-fake-pkg"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_single_package_no_deps(self):
        info = _make_info("mypkg", "1.0", summary="A simple package")
        with self._patch_session_get({"mypkg": info}):
            result = runner.invoke(app, ["dependencies", "mypkg", "--level", "1"])
        assert result.exit_code == 0
        assert "mypkg" in result.output
        assert "1.0" in result.output
        assert "Explored 0" in result.output

    def test_single_level_dep_shown(self):
        root_info = _make_info("myapp", "2.0", requires_dist=["requests>=2.0"])
        requests_info = _make_info("requests", "2.34.0")
        with self._patch_session_get({"myapp": root_info, "requests": requests_info}):
            result = runner.invoke(app, ["dependencies", "myapp", "--level", "1"])
        assert result.exit_code == 0
        assert "requests" in result.output
        assert "Explored 1" in result.output

    def test_depth_2_tree(self):
        root_info = _make_info("myapp", "1.0", requires_dist=["alpha>=1"])
        alpha_info = _make_info("alpha", "1.5", requires_dist=["beta>=0.5"])
        beta_info = _make_info("beta", "0.9")
        with self._patch_session_get({"myapp": root_info, "alpha": alpha_info, "beta": beta_info}):
            result = runner.invoke(app, ["dependencies", "myapp", "--level", "2"])
        assert result.exit_code == 0
        assert "alpha" in result.output
        assert "beta" in result.output
        assert "Explored 2" in result.output

    def test_extras_parsed_from_argument(self):
        root_info = _make_info("pkg", "1.0", requires_dist=[
            "core>=1.0",
            "bonus>=2.0 ; extra == 'opt'"
        ])
        core_info = _make_info("core", "1.1")
        bonus_info = _make_info("bonus", "2.5")
        with self._patch_session_get({"pkg": root_info, "core": core_info, "bonus": bonus_info}):
            result = runner.invoke(app, ["dependencies", "pkg[opt]", "--level", "1"])
        assert result.exit_code == 0
        assert "core" in result.output
        assert "bonus" in result.output

    def test_circular_dep_handled(self):
        a_info = _make_info("a", "1.0", requires_dist=["b>=1"])
        b_info = _make_info("b", "1.0", requires_dist=["a>=1"])
        with self._patch_session_get({"a": a_info, "b": b_info}):
            result = runner.invoke(app, ["dependencies", "a", "--level", "3"])
        assert result.exit_code == 0
        assert "circular" in result.output

    def test_level_option_limits_depth(self):
        root_info = _make_info("myapp", "1.0", requires_dist=["alpha>=1"])
        alpha_info = _make_info("alpha", "1.0", requires_dist=["hidden>=1"])
        with self._patch_session_get({"myapp": root_info, "alpha": alpha_info}):
            result = runner.invoke(app, ["dependencies", "myapp", "--level", "1"])
        assert result.exit_code == 0
        assert "hidden" not in result.output

    def test_summary_shown_in_root(self):
        info = _make_info("mypkg", "1.0", summary="Super useful utility")
        with self._patch_session_get({"mypkg": info}):
            result = runner.invoke(app, ["dependencies", "mypkg", "--level", "1"])
        assert "Super useful utility" in result.output
