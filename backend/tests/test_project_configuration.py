from django.conf import settings
from django.test import SimpleTestCase


class ProjectConfigurationTests(SimpleTestCase):

    def test_required_apps_are_installed(self):
        self.assertIn("rest_framework", settings.INSTALLED_APPS)
        self.assertIn("accounts", settings.INSTALLED_APPS)
        self.assertIn("complaints", settings.INSTALLED_APPS)
        self.assertIn("dashboard", settings.INSTALLED_APPS)

    def test_media_settings_are_configured(self):
        self.assertTrue(settings.MEDIA_URL)
        self.assertTrue(settings.MEDIA_ROOT)

    def test_rest_framework_is_configured(self):
        self.assertTrue(hasattr(settings, "REST_FRAMEWORK"))

    def test_jwt_is_configured(self):
        self.assertIn(
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"],
        )

    def test_root_url_configuration_exists(self):
        from config import urls

        self.assertTrue(hasattr(urls, "urlpatterns"))
