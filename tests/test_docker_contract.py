import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DockerContractTests(unittest.TestCase):
    def test_dockerfile_registers_app_without_dependency_reinstall(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("pip install --no-deps --editable apps/naqil", dockerfile)
        self.assertIn("naqil-boot", dockerfile)

    def test_local_topology_contains_required_services(self):
        compose = (ROOT / "docker-compose.local.yml").read_text(encoding="utf-8")
        for service in (
            "mariadb:", "redis-cache:", "redis-queue:", "redis-socketio:",
            "backend:", "websocket:", "worker-short:", "worker-long:", "scheduler:", "migrate:",
        ):
            self.assertIn(service, compose)
        self.assertNotIn("DB_ROOT_PASSWORD: naqil_", compose)

    def test_railway_map_requires_controlled_migration(self):
        service_map = (ROOT / "railway.service-map.md").read_text(encoding="utf-8")
        self.assertIn("controlled release step", service_map)
        self.assertIn("must not be retried blindly", service_map)


if __name__ == "__main__":
    unittest.main()
