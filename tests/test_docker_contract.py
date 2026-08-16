import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DockerContractTests(unittest.TestCase):
    def test_dockerfile_registers_app_without_dependency_reinstall(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("pip install --no-deps --editable apps/naqil", dockerfile)
        self.assertIn("PYTHONPATH", dockerfile)
        self.assertIn("import naqil", dockerfile)
        self.assertIn("naqil-boot", dockerfile)
        self.assertIn('CMD ["combined"]', dockerfile)

    def test_boot_script_prevents_app_name_concatenation(self):
        boot_script = (ROOT / "docker" / "boot.sh").read_text(encoding="utf-8")
        self.assertIn('printf "\\nnaqil\\n"', boot_script)
        self.assertNotIn('echo "naqil" >>', boot_script)

    def test_local_topology_contains_required_services(self):
        compose = (ROOT / "docker-compose.local.yml").read_text(encoding="utf-8")
        for service in (
            "mariadb:", "redis-cache:", "redis-queue:", "redis-socketio:",
            "backend:", "websocket:", "worker-short:", "worker-long:", "scheduler:", "migrate:",
        ):
            self.assertIn(service, compose)
        self.assertNotIn("DB_ROOT_PASSWORD: naqil_", compose)
        for service_mode in ("NAQIL_SERVICE: web", "NAQIL_SERVICE: websocket", "NAQIL_SERVICE: worker-short", "NAQIL_SERVICE: worker-long", "NAQIL_SERVICE: scheduler", "NAQIL_SERVICE: migrate"):
            self.assertIn(service_mode, compose)

    def test_railway_map_requires_controlled_migration(self):
        service_map = (ROOT / "railway.service-map.md").read_text(encoding="utf-8")
        self.assertIn("controlled release step", service_map)
        self.assertIn("must not be retried blindly", service_map)
        self.assertIn("Starter topology on Railway", service_map)


if __name__ == "__main__":
    unittest.main()
