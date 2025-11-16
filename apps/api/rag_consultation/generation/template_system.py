"""
Template System - Response Template Management

Provides production-ready response template management with
query type and tone-specific templates.

Features:
- Query type-specific templates
- Tone-aware template selection
- Jinja2-based template rendering
- Template caching

Usage:
    template_system = TemplateSystem()
    template = template_system.get_template(
        query_type=QueryType.FACTUAL,
        formality=FormalityLevel.FORMAL
    )
"""

import logging
from typing import Dict, Optional

from jinja2 import Template

from app.rag_consultation.models import (
    FormalityLevel,
    QueryType,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


class TemplateSystem:
    """Response template management system.

    Provides templates for different query types and communication styles.

    Attributes:
        templates: Template cache by query type and formality
    """

    # Base templates for each query type
    BASE_TEMPLATES: Dict[QueryType, str] = {
        QueryType.FACTUAL: """Based on the available information:

{{ context }}

{{ answer }}

{% if sources %}
Sources: {{ sources }}
{% endif %}""",
        QueryType.PROCEDURAL: """Here's how to {{ task }}:

{{ steps }}

{% if notes %}
Important notes:
{{ notes }}
{% endif %}

{% if sources %}
References: {{ sources }}
{% endif %}""",
        QueryType.COMPARISON: """Comparison of {{ items }}:

{{ comparison_table }}

Summary:
{{ summary }}

{% if recommendation %}
Recommendation: {{ recommendation }}
{% endif %}""",
        QueryType.TROUBLESHOOTING: """Issue: {{ problem }}

Diagnosis:
{{ diagnosis }}

Solution:
{{ solution }}

{% if prevention %}
Prevention:
{{ prevention }}
{% endif %}""",
        QueryType.RECOMMENDATION: """Based on your requirements for {{ context }}:

Top Recommendations:
{{ recommendations }}

Rationale:
{{ rationale }}

{% if trade_offs %}
Trade-offs to consider:
{{ trade_offs }}
{% endif %}""",
        QueryType.EXPLORATORY: """Exploring {{ topic }}:

Overview:
{{ overview }}

Key Areas:
{{ key_areas }}

{{ detailed_content }}

{% if further_reading %}
Further Reading:
{{ further_reading }}
{% endif %}""",
        QueryType.CONVERSATIONAL: """{{ response }}""",
    }

    # Formal tone modifiers
    FORMAL_PREFIXES = {
        FormalityLevel.VERY_FORMAL: "Dear User,\n\n",
        FormalityLevel.FORMAL: "Hello,\n\n",
        FormalityLevel.NEUTRAL: "",
        FormalityLevel.CASUAL: "Hey there! ",
        FormalityLevel.VERY_CASUAL: "Hey! ",
    }

    FORMAL_SUFFIXES = {
        FormalityLevel.VERY_FORMAL: "\n\nBest regards,\nRAG Enterprise System",
        FormalityLevel.FORMAL: "\n\nBest regards",
        FormalityLevel.NEUTRAL: "",
        FormalityLevel.CASUAL: "\n\nHope this helps!",
        FormalityLevel.VERY_CASUAL: "\n\nCheers!",
    }

    # Urgency modifiers
    URGENCY_PREFIXES = {
        UrgencyLevel.CRITICAL: "⚠️ URGENT RESPONSE:\n\n",
        UrgencyLevel.HIGH: "⚡ Priority Response:\n\n",
        UrgencyLevel.MEDIUM: "",
        UrgencyLevel.LOW: "",
    }

    def __init__(self) -> None:
        """Initialize template system."""
        self._template_cache: Dict[str, Template] = {}
        logger.info("Template system initialized")

    def _get_cache_key(
        self,
        query_type: QueryType,
        formality: FormalityLevel,
        urgency: UrgencyLevel,
    ) -> str:
        """Generate cache key for template.

        Args:
            query_type: Query type
            formality: Formality level
            urgency: Urgency level

        Returns:
            Cache key string
        """
        return f"{query_type.value}_{formality.value}_{urgency.value}"

    def get_template(
        self,
        query_type: QueryType,
        formality: FormalityLevel = FormalityLevel.NEUTRAL,
        urgency: UrgencyLevel = UrgencyLevel.MEDIUM,
    ) -> Template:
        """Get template for query type and communication style.

        Args:
            query_type: Query type
            formality: Formality level
            urgency: Urgency level

        Returns:
            Jinja2 Template instance
        """
        cache_key = self._get_cache_key(query_type, formality, urgency)

        # Check cache
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        # Build template with modifiers
        base_template = self.BASE_TEMPLATES.get(
            query_type,
            self.BASE_TEMPLATES[QueryType.CONVERSATIONAL],
        )

        # Add urgency prefix
        urgency_prefix = self.URGENCY_PREFIXES.get(urgency, "")

        # Add formality modifiers
        formal_prefix = self.FORMAL_PREFIXES.get(formality, "")
        formal_suffix = self.FORMAL_SUFFIXES.get(formality, "")

        # Combine into full template
        full_template_str = f"{urgency_prefix}{formal_prefix}{base_template}{formal_suffix}"

        # Create Jinja2 template
        template = Template(full_template_str)

        # Cache template
        self._template_cache[cache_key] = template

        logger.debug(
            f"Created template for {query_type.value}, "
            f"formality={formality.value}, urgency={urgency.value}"
        )

        return template

    def render_template(
        self,
        query_type: QueryType,
        formality: FormalityLevel,
        urgency: UrgencyLevel,
        **kwargs,
    ) -> str:
        """Render template with provided context.

        Args:
            query_type: Query type
            formality: Formality level
            urgency: Urgency level
            **kwargs: Template context variables

        Returns:
            Rendered template string
        """
        template = self.get_template(query_type, formality, urgency)

        try:
            rendered = template.render(**kwargs)
            return rendered.strip()
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            # Fallback to simple response
            return kwargs.get("response", "Error rendering response template")

    def clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()
        logger.info("Template cache cleared")
