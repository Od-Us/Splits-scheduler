"""Fixtures communes.

Ces tests nécessitent ``pytest-homeassistant-custom-component`` ; sans lui
(par exemple en lançant les tests de l'application principale), ils sont
simplement ignorés.
"""

import importlib.util

import pytest

if importlib.util.find_spec("pytest_homeassistant_custom_component") is None:
    collect_ignore_glob = ["test_*.py"]
else:

    @pytest.fixture(autouse=True)
    def auto_enable_custom_integrations(enable_custom_integrations):
        """Autorise le chargement de custom_components/ dans les tests."""
        yield
