import os
from unittest.mock import patch

import pytest

from smartrouter.core.license import EnterpriseFeatureException, LicenseManager


@pytest.fixture
def license_manager():
    return LicenseManager()


def test_verify_feature_valid_license(license_manager):
    with patch.dict(os.environ, {"SMARTROUTER_LICENSE_KEY": "SR_ENT_VALID_KEY"}):
        assert license_manager.verify_feature("SSO") is True


def test_verify_feature_invalid_license(license_manager):
    with patch.dict(os.environ, {"SMARTROUTER_LICENSE_KEY": "INVALID_KEY"}):
        with pytest.raises(EnterpriseFeatureException) as excinfo:
            license_manager.verify_feature("Audit Logs")
        assert "Audit Logs is an Enterprise feature" in str(excinfo.value)
        assert "Get a license key at smartrouter.io" in str(excinfo.value)


def test_verify_feature_missing_license(license_manager):
    with patch.dict(os.environ, clear=True):
        if "SMARTROUTER_LICENSE_KEY" in os.environ:
            del os.environ["SMARTROUTER_LICENSE_KEY"]  # Ensuring it's gone
        with pytest.raises(EnterpriseFeatureException) as excinfo:
            license_manager.verify_feature("Custom Routing")
        assert "Custom Routing is an Enterprise feature" in str(excinfo.value)
        assert "Get a license key at smartrouter.io" in str(excinfo.value)


def test_license_manager_singleton():
    manager1 = LicenseManager()
    manager2 = LicenseManager()
    assert manager1 is manager2
