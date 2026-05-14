"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

Test Context Builder
Tests that company and sector context is built correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from context_builder import ContextBuilder


def test_context_builder_init():
    """Test that context builder initializes."""
    builder = ContextBuilder()
    assert builder is not None, "Context builder not initialized"
    assert len(builder.companies_data) > 0, "No companies loaded"
    print(f"✓ Context builder initialized with {len(builder.companies_data)} companies")


def test_company_context():
    """Test building company context."""
    builder = ContextBuilder()

    # Test with a known company
    context = builder.build_company_context("AAPL")
    assert context, "No context returned"
    assert "Apple" in context or "AAPL" in context, "Company name not in context"
    assert "Technology" in context, "Sector not in context"
    print(f"✓ Company context built for AAPL ({len(context)} chars)")


def test_sector_context():
    """Test building sector context."""
    builder = ContextBuilder()

    context = builder.build_sector_context("Technology")
    assert context, "No context returned"
    assert "Technology" in context, "Sector name not in context"
    assert "Companies:" in context, "Companies list not in context"
    print(f"✓ Sector context built for Technology ({len(context)} chars)")


def test_general_context():
    """Test building general context."""
    builder = ContextBuilder()

    context = builder.build_general_context()
    assert context, "No context returned"
    assert "CEO Transition" in context, "Title not in context"
    assert "1996-2025" in context, "Time period not in context"
    print(f"✓ General context built ({len(context)} chars)")


def test_unknown_company():
    """Test handling of unknown company."""
    builder = ContextBuilder()

    context = builder.build_company_context("UNKNOWN")
    assert "not found" in context.lower(), "Should indicate company not found"
    print(f"✓ Unknown company handled correctly")


if __name__ == "__main__":
    print("Running Context Builder Tests...\n")

    try:
        test_context_builder_init()
        test_company_context()
        test_sector_context()
        test_general_context()
        test_unknown_company()

        print("\n✓ All context builder tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
