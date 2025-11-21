"""
Template rendering system.

This module provides a simple template engine for rendering HTML templates.
"""

import re
from typing import Any, Dict, Optional
from pathlib import Path
from qakeapi.core.response import HTMLResponse


class TemplateEngine:
    """
    Simple template engine.

    Supports variable substitution and basic control structures.
    """

    def __init__(self, directory: str):
        """
        Initialize template engine.

        Args:
            directory: Directory containing templates
        """
        self.directory = Path(directory).resolve()

        if not self.directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

    def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """
        Render template with context.

        Args:
            template_name: Template file name
            context: Template context variables

        Returns:
            Rendered HTML string
        """
        context = context or {}

        # Load template
        template_path = self.directory / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")

        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Process for loops first (loops may contain variables and conditionals)
        content = self._process_loops(content, context)

        # Process if statements {% if condition %}...{% endif %}
        content = self._process_conditionals(content, context)

        # Replace variables {{ variable }} (after loops and conditionals)
        content = self._replace_variables(content, context)

        return content

    def _replace_variables(self, content: str, context: Dict[str, Any]) -> str:
        """
        Replace template variables.

        Args:
            content: Template content
            context: Template context

        Returns:
            Content with variables replaced
        """

        def replace_var(match):
            var_name = match.group(1).strip()
            # Support dot notation for nested access
            value = self._get_nested_value(context, var_name)
            return str(value) if value is not None else ""

        pattern = r"\{\{\s*([^}]+)\s*\}\}"
        return re.sub(pattern, replace_var, content)

    def _get_nested_value(self, context: Dict[str, Any], key: str) -> Any:
        """
        Get nested value from context using dot notation.

        Args:
            context: Context dictionary
            key: Key with optional dot notation

        Returns:
            Value or None
        """
        parts = key.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                return None

        return value

    def _process_conditionals(self, content: str, context: Dict[str, Any]) -> str:
        """
        Process if/endif blocks.

        Args:
            content: Template content
            context: Template context

        Returns:
            Content with conditionals processed
        """
        pattern = r"\{\%\s*if\s+([^%]+)\s*\%\}(.*?)\{\%\s*endif\s*\%\}"

        def process_if(match):
            condition = match.group(1).strip()
            block = match.group(2)

            # Simple condition evaluation
            if self._evaluate_condition(condition, context):
                return block
            return ""

        return re.sub(pattern, process_if, content, flags=re.DOTALL)

    def _process_loops(self, content: str, context: Dict[str, Any]) -> str:
        """
        Process for/endfor blocks.

        Args:
            content: Template content
            context: Template context

        Returns:
            Content with loops processed
        """
        pattern = r"\{\%\s*for\s+(\w+)\s+in\s+([^%]+)\s*\%\}(.*?)\{\%\s*endfor\s*\%\}"

        def process_for(match):
            var_name = match.group(1).strip()
            iterable_key = match.group(2).strip()
            block = match.group(3)

            # Get iterable from context
            iterable = self._get_nested_value(context, iterable_key)
            if not iterable:
                return ""

            # Check if iterable
            try:
                iter(iterable)
            except TypeError:
                return ""

            # Render block for each item
            result = []
            items_list = list(iterable)
            for idx, item in enumerate(items_list):
                loop_context = context.copy()
                loop_context[var_name] = item
                loop_context["loop"] = {
                    "index": idx + 1,
                    "index0": idx,
                    "first": idx == 0,
                    "last": idx == len(items_list) - 1,
                }
                # Render with variables and conditionals
                rendered = self._replace_variables(block, loop_context)
                rendered = self._process_conditionals(rendered, loop_context)
                result.append(rendered)

            return "".join(result)

        return re.sub(pattern, process_for, content, flags=re.DOTALL)

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate condition expression.

        Args:
            condition: Condition string
            context: Template context

        Returns:
            True if condition is true
        """
        # Simple evaluation - check if variable exists and is truthy
        condition = condition.strip()

        # Handle "not" operator
        if condition.startswith("not "):
            var_name = condition[4:].strip()
            value = self._get_nested_value(context, var_name)
            return not bool(value)

        # Check if variable exists and is truthy
        value = self._get_nested_value(context, condition)
        return bool(value)


class TemplateRenderer:
    """
    Template renderer for use in route handlers.
    """

    def __init__(self, directory: str):
        """
        Initialize template renderer.

        Args:
            directory: Directory containing templates
        """
        self.engine = TemplateEngine(directory)

    def TemplateResponse(
        self,
        template_name: str,
        context: Dict[str, Any] = None,
        status_code: int = 200,
    ) -> HTMLResponse:
        """
        Render template and return HTML response.

        Args:
            template_name: Template file name
            context: Template context
            status_code: HTTP status code

        Returns:
            HTMLResponse instance
        """
        content = self.engine.render(template_name, context)
        return HTMLResponse(content, status_code=status_code)
