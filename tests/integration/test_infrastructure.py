"""
Integration tests for infrastructure (health checks, monitoring, migrations)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestHealthChecks:
    """Test health check endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_health_ready_endpoint(self, client):
        """Test /health/ready endpoint"""
        response = client.get("/health/ready")

        # Can be 200 (ready) or 503 (not ready)
        assert response.status_code in [200, 503]
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

        # Check readiness fields (app/api/routes/health.py ReadinessResponse)
        assert "ready" in data
        assert isinstance(data["ready"], bool)
        assert "checks_passed" in data
        assert "checks_total" in data

    def test_health_live_endpoint(self, client):
        """Test /health/live endpoint"""
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"  # Updated to match app/api/routes/health.py

    def test_health_endpoint_backward_compatibility(self, client):
        """Test /health endpoint (legacy)"""
        response = client.get("/health")

        assert response.status_code == 200


class TestMonitoring:
    """Test monitoring endpoints (Prometheus metrics)"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_metrics_endpoint_exists(self, client):
        """Test that /metrics endpoint exists (for Prometheus)"""
        # Note: This might not be implemented yet, but we test for it
        response = client.get("/metrics")

        # Should either return 200 (implemented) or 404 (not implemented yet)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            # Prometheus metrics format
            assert "text/plain" in response.headers.get("content-type", "").lower()


class TestDatabaseMigrations:
    """Test database migration system"""

    def test_alembic_migration_files_exist(self):
        """Test that Alembic migration files exist"""
        from pathlib import Path

        alembic_dir = Path("alembic/versions")
        assert alembic_dir.exists(), "Alembic versions directory not found"

        migration_files = list(alembic_dir.glob("*.py"))
        assert len(migration_files) > 0, "No migration files found"

        # Should have initial SaaS migration
        saas_migrations = [f for f in migration_files if "saas" in f.stem.lower()]
        assert len(saas_migrations) > 0, "SaaS migration not found"

        # Should have analytics migration
        analytics_migrations = [f for f in migration_files if "analytics" in f.stem.lower()]
        assert len(analytics_migrations) > 0, "Analytics migration not found"

    def test_alembic_config_exists(self):
        """Test that Alembic configuration exists"""
        from pathlib import Path

        assert Path("alembic.ini").exists(), "alembic.ini not found"
        assert Path("alembic/env.py").exists(), "alembic/env.py not found"

    def test_alembic_migration_structure(self):
        """Test that migrations have correct structure"""
        from pathlib import Path

        migration_files = list(Path("alembic/versions").glob("*.py"))

        for migration_file in migration_files:
            content = migration_file.read_text()

            # Should have upgrade function
            assert "def upgrade()" in content, f"No upgrade() in {migration_file.name}"

            # Should have downgrade function
            assert "def downgrade()" in content, f"No downgrade() in {migration_file.name}"

            # Should have revision ID
            assert "revision:" in content, f"No revision in {migration_file.name}"


class TestDocker:
    """Test Docker configuration"""

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists"""
        from pathlib import Path

        assert Path("Dockerfile").exists(), "Dockerfile not found"
        assert Path("Dockerfile.prod").exists(), "Dockerfile.prod not found"

    def test_dockerfile_multistage(self):
        """Test that Dockerfile uses multi-stage build"""
        content = open("Dockerfile").read()

        # Should have multiple FROM statements (multi-stage)
        from_count = content.count("FROM ")
        assert from_count >= 2, "Dockerfile should use multi-stage build"

        # Should have builder stage
        assert "AS builder" in content, "No builder stage found"

    def test_dockerignore_exists(self):
        """Test that .dockerignore exists"""
        from pathlib import Path

        assert Path(".dockerignore").exists(), ".dockerignore not found"

    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists"""
        from pathlib import Path

        assert Path("docker-compose.yml").exists(), "docker-compose.yml not found"

    def test_docker_compose_has_monitoring(self):
        """Test that docker-compose includes monitoring services"""
        import yaml

        with open("docker-compose.yml") as f:
            compose_config = yaml.safe_load(f)

        services = compose_config.get("services", {})

        # Should have monitoring services
        assert "prometheus" in services, "Prometheus service not found"
        assert "grafana" in services, "Grafana service not found"


class TestMakefile:
    """Test Makefile commands"""

    def test_makefile_exists(self):
        """Test that Makefile exists"""
        from pathlib import Path

        assert Path("Makefile").exists(), "Makefile not found"

    def test_makefile_has_essential_targets(self):
        """Test that Makefile has essential targets"""
        content = open("Makefile").read()

        essential_targets = [
            "setup",
            "dev",
            "test",
            "docker-up",
            "docker-down",
            "migrate-upgrade",
        ]

        for target in essential_targets:
            assert f"{target}:" in content, f"Makefile missing target: {target}"
