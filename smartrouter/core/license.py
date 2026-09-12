import os
import typing


class EnterpriseFeatureException(Exception):
    pass


class LicenseManager:
    _instance = None

    def __new__(cls) -> typing.Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def verify_feature(self, feature_name: str) -> bool:
        license_key = os.getenv("SMARTROUTER_LICENSE_KEY")
        if not license_key or not license_key.startswith("SR_ENT_"):
            raise EnterpriseFeatureException(
                f"[SmartRouter] {feature_name} is an Enterprise feature. Get a license key at smartrouter.io"
            )
        return True


license_manager = LicenseManager()
