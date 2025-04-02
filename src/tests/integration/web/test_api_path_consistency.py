"""
Test API Path Consistency between frontend and backend.
This test ensures that API paths used in frontend JavaScript match backend routes.
"""

import os
import re
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute

# Import the main application
from src.main import app


class TestAPIPathConsistency(unittest.TestCase):
    """Test that frontend API calls use paths that match backend routes."""

    def setUp(self):
        """Set up test environment."""
        self.frontend_dir = (
            Path(__file__).parent.parent.parent.parent / "frontend" / "templates"
        )
        self.api_paths_in_js = self.extract_api_paths_from_templates()
        self.backend_routes = self.get_backend_routes()

    def extract_api_paths_from_templates(self):
        """Extract API paths from fetch() calls in JavaScript."""
        api_paths = []

        for template_file in self.frontend_dir.glob("**/*.html"):
            with open(template_file, "r") as f:
                content = f.read()

                # Find all fetch calls with regex
                fetch_calls = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", content)
                api_paths.extend(fetch_calls)

                # Also find all fetch calls with template literals
                # This is simplified and may need enhancement for complex template literals
                fetch_calls_template = re.findall(r"fetch\(`([^`$]+)", content)
                api_paths.extend(fetch_calls_template)

        return api_paths

    def get_backend_routes(self):
        """Get all registered API routes from the FastAPI app."""
        routes = []

        def collect_routes(app):
            for route in app.routes:
                if isinstance(route, APIRoute):
                    routes.append(route.path)
                # Handle mounted apps
                elif hasattr(route, "app") and isinstance(route.app, FastAPI):
                    prefix = route.path.rstrip("/")
                    for sub_route in route.app.routes:
                        if isinstance(sub_route, APIRoute):
                            routes.append(f"{prefix}{sub_route.path}")

        collect_routes(app)
        return routes

    def test_frontend_api_paths_match_backend_routes(self):
        """Test that all frontend API paths have corresponding backend routes."""
        for path in self.api_paths_in_js:
            # Skip non-API paths like static resources
            if not path.startswith("/api/"):
                continue

            # Check if this path would match any backend route
            # We need to handle path parameters
            path_parts = path.split("/")

            # For paths with dynamic IDs like /api/monitoring/tags/{tag_id}
            found_match = False
            for route in self.backend_routes:
                route_parts = route.split("/")

                # Skip if parts length doesn't match
                if len(path_parts) != len(route_parts):
                    continue

                # Check if path could match route with parameters
                match = True
                for i, (path_part, route_part) in enumerate(
                    zip(path_parts, route_parts)
                ):
                    if route_part.startswith("{") and route_part.endswith("}"):
                        # This is a parameter, always matches
                        continue
                    if path_part != route_part:
                        match = False
                        break

                if match:
                    found_match = True
                    break

            self.assertTrue(
                found_match, f"Frontend API path '{path}' has no matching backend route"
            )
