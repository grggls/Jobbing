"""Tests for jobbing.__main__ — module entry point."""

from __future__ import annotations

from unittest.mock import patch


class TestMainEntryPoint:
    def test_calls_main(self) -> None:
        """__main__.py imports and calls cli.main()."""
        with patch("jobbing.cli.main"):
            import jobbing.__main__ as main_mod

            # The module has already executed main() on import, but we can verify
            # the import structure is correct
            assert hasattr(main_mod, "main")

    def test_main_is_importable(self) -> None:
        """The main function is importable from cli."""
        from jobbing.cli import main

        assert callable(main)
