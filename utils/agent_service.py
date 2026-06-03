"""Agent-style orchestration for automation generation.

The current environment does not expose an importable Google Antigravity SDK
module, so this service provides a stable app-facing orchestration interface
using the existing Gemini wrapper. When the SDK contract is available, the SDK
implementation can be placed behind the same request/result/event models.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Union

from .mermaid_renderer import FlowchartGenerator


@dataclass
class AutomationRequest:
    pdf_text: str
    domain: str
    extra_info: str = ""
    complexity: str = "moderate"
    include_tests: bool = True
    script_language: str = "Python"
    include_comments: bool = True


@dataclass
class ValidationIssue:
    component: str
    passed: bool
    message: str
    attempt: int = 1


@dataclass
class AutomationResult:
    summary: str
    mermaid_diagram: str
    block_diagram: str
    script: str
    unit_tests: str
    prerequisites: str
    validation_report: List[ValidationIssue] = field(default_factory=list)
    generation_mode: str = "local_orchestrator"


@dataclass
class AgentEvent:
    type: str
    message: str
    step: str
    metadata: Dict[str, Any] = field(default_factory=dict)


AgentStreamItem = Union[AgentEvent, AutomationResult]


class AutomationAgentService:
    """Coordinates generation, validation, retries, and progress events."""

    def __init__(self, gemini, max_retries: int = 2):
        self.gemini = gemini
        self.max_retries = max(0, max_retries)
        self.flowchart_generator = FlowchartGenerator()
        self.sdk_available = self._detect_antigravity_sdk()

    @staticmethod
    def _detect_antigravity_sdk() -> bool:
        for module_name in ("google_antigravity", "google.antigravity"):
            try:
                if importlib.util.find_spec(module_name):
                    return True
            except ModuleNotFoundError:
                continue
        return False

    def run(self, request: AutomationRequest) -> AutomationResult:
        result: Optional[AutomationResult] = None
        for item in self.stream(request):
            if isinstance(item, AutomationResult):
                result = item
        if result is None:
            raise RuntimeError("Automation generation did not produce a result")
        return result

    def stream(self, request: AutomationRequest) -> Iterator[AgentStreamItem]:
        report: List[ValidationIssue] = []
        mode = "antigravity_sdk" if self.sdk_available else "local_orchestrator"

        yield AgentEvent(
            "status",
            f"Starting automation generation in {mode.replace('_', ' ')} mode.",
            "initialize",
            {"generation_mode": mode},
        )

        yield AgentEvent("tool_start", "Generating document summary.", "summary")
        summary = self.gemini.gemini_summarize(
            request.pdf_text, request.domain, request.extra_info
        )
        if not summary:
            yield AgentEvent("error", "Summary generation failed.", "summary")
            raise RuntimeError("Summary generation failed")
        yield AgentEvent("tool_result", "Summary generated.", "summary")

        yield AgentEvent("tool_start", "Generating Mermaid flowchart.", "diagram")
        mermaid_diagram = self.gemini.gemini_generate_mermaid_diagram(
            summary, request.domain, request.extra_info, request.complexity
        )
        report_start = len(report)
        mermaid_diagram = self._repair_mermaid(
            mermaid_diagram or "", summary, request, report
        )
        yield from self._events_for_report(report[report_start:], "diagram")
        yield AgentEvent("tool_result", "Flowchart generated and validated.", "diagram")

        block_diagram = self._build_block_diagram_description(request.domain)

        yield AgentEvent("tool_start", "Generating automation script.", "script")
        script = self.gemini.gemini_generate_script(
            summary, request.domain, request.extra_info
        )
        report_start = len(report)
        script = self._repair_script(script or "", summary, request, report)
        yield from self._events_for_report(report[report_start:], "script")
        yield AgentEvent("tool_result", "Script generated and validated.", "script")

        unit_tests = ""
        if request.include_tests:
            yield AgentEvent("tool_start", "Generating unit tests.", "unit_tests")
            unit_tests = self.gemini.gemini_generate_unit_tests(
                summary, script, request.domain, request.extra_info
            ) or ""
            report_start = len(report)
            unit_tests = self._validate_or_clean_tests(unit_tests, report)
            yield from self._events_for_report(report[report_start:], "unit_tests")
            yield AgentEvent("tool_result", "Unit tests generated.", "unit_tests")
        else:
            yield AgentEvent("status", "Unit test generation skipped by request.", "unit_tests")

        yield AgentEvent("tool_start", "Identifying prerequisites.", "prerequisites")
        prerequisites = self.gemini.gemini_generate_prerequisites(
            summary, request.domain, request.extra_info
        )
        if not prerequisites:
            prerequisites = "Prerequisites could not be generated. Review the script before use."
            report.append(
                ValidationIssue(
                    "prerequisites",
                    False,
                    "Prerequisites generation returned an empty result.",
                )
            )
            yield AgentEvent(
                "validation",
                "Prerequisites generation returned an empty result.",
                "prerequisites",
                {"passed": False},
            )
        yield AgentEvent("tool_result", "Prerequisites generated.", "prerequisites")

        result = AutomationResult(
            summary=summary,
            mermaid_diagram=mermaid_diagram,
            block_diagram=block_diagram,
            script=script,
            unit_tests=unit_tests,
            prerequisites=prerequisites,
            validation_report=report,
            generation_mode=mode,
        )
        yield AgentEvent("complete", "Automation package is ready.", "complete")
        yield result

    def _repair_mermaid(
        self,
        mermaid_code: str,
        summary: str,
        request: AutomationRequest,
        report: List[ValidationIssue],
    ) -> str:
        candidate = self._strip_code_fence(mermaid_code)

        for attempt in range(1, self.max_retries + 2):
            passed, message = self._validate_mermaid(candidate)
            report.append(ValidationIssue("mermaid", passed, message, attempt))
            if passed:
                return candidate

            if attempt <= self.max_retries:
                corrected = self._ask_for_mermaid_fix(
                    candidate, message, summary, request
                )
                if corrected:
                    candidate = self._strip_code_fence(corrected)

        fallback = self.flowchart_generator.generate_automation_flowchart(
            summary, request.domain, request.complexity
        )
        fallback = self._strip_code_fence(fallback)
        passed, message = self._validate_mermaid(fallback)
        report.append(ValidationIssue("mermaid_fallback", passed, message))
        return fallback

    def _ask_for_mermaid_fix(
        self,
        mermaid_code: str,
        validation_error: str,
        summary: str,
        request: AutomationRequest,
    ) -> Optional[str]:
        prompt = f"""
Fix this Mermaid flowchart for the {request.domain} domain.

Validation error: {validation_error}

Rules:
- Return only Mermaid code.
- Start with flowchart TD.
- Quote all node labels.
- Keep decision labels inside double braces.
- Do not include Markdown fences or explanations.

Summary:
{summary[:1500]}

Current Mermaid:
{mermaid_code}
"""
        return self.gemini.gemini_generate_content(
            prompt, operation="Mermaid correction"
        )

    def _repair_script(
        self,
        script: str,
        summary: str,
        request: AutomationRequest,
        report: List[ValidationIssue],
    ) -> str:
        candidate = self._strip_code_fence(script)

        for attempt in range(1, self.max_retries + 2):
            passed, message = self._validate_python_script(candidate)
            report.append(ValidationIssue("script", passed, message, attempt))
            if passed:
                return candidate

            if attempt <= self.max_retries:
                corrected = self._ask_for_script_fix(
                    candidate, message, summary, request
                )
                if corrected:
                    candidate = self._strip_code_fence(corrected)

        return candidate

    def _ask_for_script_fix(
        self,
        script: str,
        validation_error: str,
        summary: str,
        request: AutomationRequest,
    ) -> Optional[str]:
        prompt = f"""
Fix this generated Python automation script for the {request.domain} domain.

Validation error: {validation_error}

Rules:
- Return only Python code.
- Do not include Markdown fences.
- Do not use eval, exec, os.system, shell=True, or hardcoded credentials.
- Include clear error handling and a main guard.

Summary:
{summary[:1500]}

Current script:
{script}
"""
        return self.gemini.gemini_generate_content(
            prompt, operation="script correction"
        )

    def _validate_or_clean_tests(
        self, unit_tests: str, report: List[ValidationIssue]
    ) -> str:
        cleaned = self._strip_code_fence(unit_tests)
        if not cleaned.strip():
            report.append(
                ValidationIssue("unit_tests", False, "Unit test generation returned empty output.")
            )
            return ""

        try:
            ast.parse(cleaned)
            report.append(ValidationIssue("unit_tests", True, "Unit tests parse as Python."))
        except SyntaxError as exc:
            report.append(
                ValidationIssue(
                    "unit_tests",
                    False,
                    f"Unit tests contain Python syntax error: {exc.msg}.",
                )
            )
        return cleaned

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        text = (text or "").strip()
        fence_match = re.search(r"```(?:\w+)?\s*(.*?)```", text, re.DOTALL)
        if fence_match:
            return fence_match.group(1).strip()
        return text

    @staticmethod
    def _validate_mermaid(mermaid_code: str) -> tuple[bool, str]:
        if not mermaid_code or not mermaid_code.strip():
            return False, "Mermaid output is empty."

        cleaned = mermaid_code.strip()
        if "```" in cleaned:
            return False, "Mermaid output contains Markdown code fences."

        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if not lines or not lines[0].startswith("flowchart"):
            return False, "Mermaid output must start with a flowchart directive."

        joined = "\n".join(lines)
        for open_char, close_char, label in (
            ("[", "]", "square brackets"),
            ("{", "}", "braces"),
            ("(", ")", "parentheses"),
        ):
            if joined.count(open_char) != joined.count(close_char):
                return False, f"Mermaid output has unbalanced {label}."

        if not any("-->" in line for line in lines[1:]):
            return False, "Mermaid output does not contain flowchart edges."

        return True, "Mermaid syntax passed basic validation."

    @staticmethod
    def _validate_python_script(script: str) -> tuple[bool, str]:
        if not script or not script.strip():
            return False, "Script output is empty."

        dangerous_patterns = [
            "rm -rf",
            "del /f",
            "format c:",
            "drop table",
            "delete from",
            "exec(",
            "eval(",
            "__import__",
            "subprocess.call",
            "os.system",
            "shell=True",
        ]
        lowered = script.lower()
        found = [pattern for pattern in dangerous_patterns if pattern.lower() in lowered]
        if found:
            return False, f"Potentially unsafe pattern detected: {', '.join(found)}."

        secret_patterns = [
            r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]
        for pattern in secret_patterns:
            if re.search(pattern, script, flags=re.IGNORECASE):
                return False, "Possible hardcoded credential detected."

        try:
            ast.parse(script)
        except SyntaxError as exc:
            return False, f"Python syntax error: {exc.msg}."

        return True, "Python script passed safety and syntax validation."

    @staticmethod
    def _build_block_diagram_description(domain: str) -> str:
        return (
            "Process Flow Description:\n\n"
            "This automation package includes an interactive Mermaid flowchart "
            "with process steps, decisions, error handling paths, retry logic, "
            f"and multiple end states for the {domain} automation workflow."
        )

    def _events_for_report(
        self, issues: List[ValidationIssue], step: str
    ) -> Iterator[AgentEvent]:
        for issue in issues:
            if issue.passed:
                yield AgentEvent(
                    "validation",
                    issue.message,
                    step,
                    {
                        "component": issue.component,
                        "attempt": issue.attempt,
                        "passed": True,
                    },
                )
            else:
                yield AgentEvent(
                    "validation",
                    issue.message,
                    step,
                    {
                        "component": issue.component,
                        "attempt": issue.attempt,
                        "passed": False,
                    },
                )
                if issue.attempt <= self.max_retries:
                    yield AgentEvent(
                        "retry",
                        f"Retrying {issue.component} after validation failure.",
                        step,
                        {
                            "component": issue.component,
                            "attempt": issue.attempt,
                        },
                    )
