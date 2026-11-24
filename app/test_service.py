import os
import unittest

os.environ["SERVICE_NAME"] = "catalog"
from service import render_metrics  # noqa: E402


class ServiceTest(unittest.TestCase):
    def test_metrics_are_prometheus_compatible(self):
        self.assertIn('http_requests_total{service="catalog"}', render_metrics())

    def test_runtime_has_no_external_dependency(self):
        self.assertEqual(os.environ["SERVICE_NAME"], "catalog")


if __name__ == "__main__":
    unittest.main()
