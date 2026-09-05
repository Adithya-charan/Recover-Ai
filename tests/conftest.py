"""
Test configuration for RecoverAI.

Ensures a clean, deterministic environment for every test run:
- LLM_PROVIDER defaults to "simulation" so the heavy Hugging Face model is
  never loaded unless a test explicitly opts in.
- RECOVERY_MODE defaults to "simulation" so no real payment gateway is hit.
- Existing env values set BEFORE pytest starts are respected (override=False),
  so a developer can still run with LLM_PROVIDER=huggingface if they want.
"""
import os
import pytest


def pytest_configure(config):
    """Set safe test defaults before any test module is collected."""
    os.environ.setdefault("LLM_PROVIDER", "simulation")
    os.environ.setdefault("RECOVERY_MODE", "simulation")
