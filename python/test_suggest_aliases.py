#!/usr/bin/env python3
"""
test_suggest_aliases.py
Unit tests for suggest_aliases.py using the standard unittest library.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module functions
import suggest_aliases

class TestSuggestAliases(unittest.TestCase):

    def test_get_recency_weight(self):
        # Total <= 1 should return 1.0
        self.assertEqual(suggest_aliases.get_recency_weight(0, 1), 1.0)
        self.assertEqual(suggest_aliases.get_recency_weight(0, 0), 1.0)
        
        # Test weighting sections
        total = 9
        # Index 0, 1, 2 (first third) -> 1.0
        self.assertEqual(suggest_aliases.get_recency_weight(0, total), 1.0)
        self.assertEqual(suggest_aliases.get_recency_weight(2, total), 1.0)
        # Index 3, 4, 5 (middle third) -> 1.5
        self.assertEqual(suggest_aliases.get_recency_weight(3, total), 1.5)
        self.assertEqual(suggest_aliases.get_recency_weight(5, total), 1.5)
        # Index 6, 7, 8 (last third) -> 2.0
        self.assertEqual(suggest_aliases.get_recency_weight(6, total), 2.0)
        self.assertEqual(suggest_aliases.get_recency_weight(8, total), 2.0)

    def test_generate_alias_name(self):
        # Test basic abbreviations
        self.assertEqual(suggest_aliases.generate_alias_name("git status"), "gst")
        self.assertEqual(suggest_aliases.generate_alias_name("docker compose up"), "dcup")
        self.assertEqual(suggest_aliases.generate_alias_name("python3 my_script.py"), "py3m")
        self.assertEqual(suggest_aliases.generate_alias_name("kubectl get pods"), "kgp")
        
        # Test fallback
        self.assertEqual(suggest_aliases.generate_alias_name(""), "")

    def test_is_service_command(self):
        self.assertTrue(suggest_aliases.is_service_command("systemctl restart apache2"))
        self.assertTrue(suggest_aliases.is_service_command("sudo systemctl status nginx"))
        self.assertTrue(suggest_aliases.is_service_command("journalctl -u docker"))
        self.assertFalse(suggest_aliases.is_service_command("git status"))
        self.assertFalse(suggest_aliases.is_service_command("ls -la"))

    def test_resolve_conflict_available(self):
        existing_aliases = {"gst": "git status"}
        system_commands = {"git", "ls"}
        
        # Available alias name
        alias, status = suggest_aliases.resolve_conflict("gco", "git checkout", existing_aliases, system_commands)
        self.assertEqual(alias, "gco")
        self.assertEqual(status, "Available")

    def test_resolve_conflict_duplicate(self):
        existing_aliases = {"gst": "git status"}
        system_commands = {"git"}
        
        # Same command already mapped
        alias, status = suggest_aliases.resolve_conflict("gst", "git status", existing_aliases, system_commands)
        self.assertEqual(alias, "gst")
        self.assertEqual(status, "Duplicate (already defined)")

    def test_resolve_conflict_existing_alias(self):
        existing_aliases = {"gst": "git status"}
        system_commands = {"git"}
        
        # Different command but same alias
        alias, status = suggest_aliases.resolve_conflict("gst", "git stash", existing_aliases, system_commands)
        self.assertTrue(alias.startswith("gst"))
        self.assertNotEqual(alias, "gst")
        self.assertIn("Conflict", status)

    def test_extract_candidates(self):
        # We need enough commands to meet min_uses
        commands = [
            "git status",
            "git status",
            "git status",
            "git status"
        ]
        candidates = suggest_aliases.extract_candidates(commands, min_uses=2)
        # Should detect "git status"
        commands_only = [c[0] for c in candidates]
        self.assertIn("git status", commands_only)

    def test_detect_service_interactions(self):
        commands = [
            "systemctl restart nginx",
            "sudo systemctl stop apache2.service",
            "systemctl --user restart pulse-audio",
            "sudo systemctl restart docker.service --now",
            "journalctl -u custom-service",
            "sudo journalctl --unit=db-service -f"
        ]
        
        services = suggest_aliases.detect_service_interactions(commands)
        
        self.assertIn("nginx", services)
        self.assertIn("apache2", services)
        self.assertIn("pulse-audio", services)
        self.assertIn("docker", services)
        self.assertIn("custom-service", services)
        self.assertIn("db-service", services)
        
        # Test uses_sudo tracking
        self.assertTrue(services["apache2"].uses_sudo)
        self.assertTrue(services["docker"].uses_sudo)
        self.assertTrue(services["db-service"].uses_sudo)
        self.assertFalse(services["nginx"].uses_sudo)

if __name__ == "__main__":
    unittest.main()
