import pytest
from unittest.mock import patch
from app.services.llm_service import generate_website_state, WEBSITE_DEFAULTS


class TestFallbackMechanism:
    """Tests for fallback when LLM fails."""

    def test_first_call_invalid_retry_succeeds(self, normal_input):
        """FB-01: First call invalid, retry succeeds."""
        call_count = 0

        def mock_ask_llm(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"invalid": "data"}
            return {
                "templateId": "template-services",
                "theme": {"primaryColor": "#2563EB", "accentColor": "#1E40AF", "fontFamily": "sans"},
                "meta": {"businessName": "Test", "category": "Jasa", "tagline": "Test"},
                "hero": {"title": "Test", "subtitle": "Test", "ctaText": "Test", "ctaWhatsappMessage": "Test"},
                "about": {"story": "Test", "highlights": ["Test"]},
                "services": [{"name": "A", "description": "B", "priceEstimate": "C"}] * 3,
                "testimonials": [{"customerName": "A", "review": "B"}] * 2,
                "contact": {"whatsappNumber": "6281234567890", "address": "Test"}
            }

        with patch("app.services.llm_service.ask_llm", side_effect=mock_ask_llm):
            data, is_fallback = generate_website_state(normal_input)

        assert not is_fallback
        assert call_count == 2

    def test_both_retries_fail_uses_fallback(self, normal_input):
        """FB-02: Both retries fail, fallback used."""
        def mock_ask_llm(*args, **kwargs):
            return {"invalid": "data"}

        with patch("app.services.llm_service.ask_llm", side_effect=mock_ask_llm):
            data, is_fallback = generate_website_state(normal_input)

        assert is_fallback
        assert data["templateId"] == WEBSITE_DEFAULTS["templateId"]

    def test_llm_exception_uses_fallback(self, normal_input):
        """FB-03: LLM exception triggers fallback."""
        def mock_ask_llm(*args, **kwargs):
            raise Exception("LLM unavailable")

        with patch("app.services.llm_service.ask_llm", side_effect=mock_ask_llm):
            data, is_fallback = generate_website_state(normal_input)

        assert is_fallback
        assert data["templateId"] == WEBSITE_DEFAULTS["templateId"]
