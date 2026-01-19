#!/usr/bin/env python3
"""
Tests for citation validation system.

These tests verify the deterministic citation validators work correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from newsletter_engine import validate_citations, validate_ps_citations


def test_invalid_citation_id_detected():
    """Test that invalid citation IDs are detected."""
    draft = "This is a fact [FAKE_1] and another fact [PS_1]."
    evidence_ids = ["PS_1", "VP_2", "KB_3"]
    
    result = validate_citations(draft, evidence_ids)
    
    assert "FAKE_1" in result['invalid_citation_ids'], \
        f"Expected FAKE_1 in invalid IDs, got: {result['invalid_citation_ids']}"
    assert "PS_1" not in result['invalid_citation_ids'], \
        "PS_1 should not be in invalid IDs"
    assert not result['passed'], \
        "Validation should fail with invalid citation ID"
    
    print("✅ test_invalid_citation_id_detected passed")


def test_missing_citation_sentence_flagged():
    """Test that factual sentences without citations are flagged."""
    draft = "According to a report, X happened. This is normal text."
    evidence_ids = ["PS_1"]
    
    result = validate_citations(draft, evidence_ids)
    
    assert len(result['missing_citations_sentences']) > 0, \
        "Should flag sentence with 'according to' but no citation"
    assert any("According to a report" in s for s in result['missing_citations_sentences']), \
        f"Expected flagged sentence, got: {result['missing_citations_sentences']}"
    assert not result['passed'], \
        "Validation should fail with missing citation"
    
    print("✅ test_missing_citation_sentence_flagged passed")


def test_factual_sentence_with_citation_passes():
    """Test that factual sentences WITH citations pass."""
    draft = "According to a report [PS_1], X happened."
    evidence_ids = ["PS_1"]
    
    result = validate_citations(draft, evidence_ids)
    
    assert len(result['missing_citations_sentences']) == 0, \
        f"Should not flag cited sentence, got: {result['missing_citations_sentences']}"
    assert result['passed'], \
        "Validation should pass with proper citation"
    
    print("✅ test_factual_sentence_with_citation_passes passed")


def test_multiple_factual_markers():
    """Test various factual markers are detected."""
    markers = [
        "According to research",
        "A study shows",
        "Data reveals",
        "45% of users",
        "5 million people",
        "Survey results",
        "Researchers found"
    ]
    
    evidence_ids = ["PS_1"]
    
    for marker in markers:
        draft = f"{marker} that something happened."
        result = validate_citations(draft, evidence_ids)
        
        assert len(result['missing_citations_sentences']) > 0, \
            f"Marker '{marker}' should be detected as needing citation"
    
    print("✅ test_multiple_factual_markers passed")


def test_ps_citation_requirement():
    """Test PS citation requirement validation."""
    # Test passing case
    draft_pass = "This uses [PS_1] and [PS_2] sources."
    result_pass = validate_ps_citations(draft_pass, must_use_min=1)
    
    assert result_pass['ps_citation_count'] == 2, \
        f"Should count 2 PS citations, got: {result_pass['ps_citation_count']}"
    assert result_pass['ps_passed'], \
        "Should pass with 2 PS citations when 1 required"
    
    # Test failing case
    draft_fail = "This uses [VP_1] but no PS sources."
    result_fail = validate_ps_citations(draft_fail, must_use_min=1)
    
    assert result_fail['ps_citation_count'] == 0, \
        "Should count 0 PS citations"
    assert not result_fail['ps_passed'], \
        "Should fail with 0 PS citations when 1 required"
    
    print("✅ test_ps_citation_requirement passed")


def test_ps_citation_unique_count():
    """Test that PS citations are counted uniquely."""
    # Same PS cited multiple times should count as 1
    draft = "First use [PS_1] and second use [PS_1] and [PS_2]."
    result = validate_ps_citations(draft, must_use_min=2)
    
    assert result['ps_citation_count'] == 2, \
        f"Should count 2 unique PS citations, got: {result['ps_citation_count']}"
    assert result['ps_passed'], \
        "Should pass with 2 unique PS citations"
    
    print("✅ test_ps_citation_unique_count passed")


def test_citation_count_valid_only():
    """Test that citation count only includes valid IDs."""
    draft = "Valid [PS_1] and invalid [FAKE_1] and valid [VP_2]."
    evidence_ids = ["PS_1", "VP_2"]
    
    result = validate_citations(draft, evidence_ids)
    
    assert result['citation_count'] == 2, \
        f"Should count only 2 valid citations, got: {result['citation_count']}"
    assert len(result['invalid_citation_ids']) == 1, \
        "Should have 1 invalid ID"
    
    print("✅ test_citation_count_valid_only passed")


def test_no_issues_passes():
    """Test that text with no issues passes validation."""
    draft = """This is a newsletter.
    
    Some facts here [PS_1] and more analysis.
    According to research [VP_2], this is true.
    Data shows [KB_3] that things happen.
    
    This is opinion text without citations, which is fine.
    """
    evidence_ids = ["PS_1", "VP_2", "KB_3"]
    
    result = validate_citations(draft, evidence_ids)
    
    assert result['passed'], \
        f"Should pass validation, got: {result}"
    assert len(result['invalid_citation_ids']) == 0
    assert len(result['missing_citations_sentences']) == 0
    
    print("✅ test_no_issues_passes passed")


def run_all_tests():
    """Run all citation validation tests."""
    print("=" * 70)
    print("CITATION VALIDATION TESTS")
    print("=" * 70)
    print()
    
    tests = [
        test_invalid_citation_id_detected,
        test_missing_citation_sentence_flagged,
        test_factual_sentence_with_citation_passes,
        test_multiple_factual_markers,
        test_ps_citation_requirement,
        test_ps_citation_unique_count,
        test_citation_count_valid_only,
        test_no_issues_passes,
    ]
    
    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed.append(test.__name__)
    
    print()
    print("=" * 70)
    if failed:
        print(f"❌ {len(failed)} test(s) FAILED:")
        for name in failed:
            print(f"   - {name}")
        return 1
    else:
        print(f"✅ ALL {len(tests)} TESTS PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
