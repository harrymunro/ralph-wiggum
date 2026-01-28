"""Semantic auditor module for V-Ralph.

Provides an adversarial reviewer to catch green build hallucinations
by verifying implementations against specifications.
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from shared.claude import invoke_claude


class AuditVerdict(Enum):
    """Possible verdicts from the semantic auditor."""

    PASS = "pass"
    RETRY = "retry"
    ESCALATE = "escalate"


@dataclass
class AuditResult:
    """Result from an audit."""

    verdict: AuditVerdict
    feedback: str = ""
    reason: str = ""


class AuditorError(Exception):
    """Exception raised for auditor-related errors."""

    pass


def _log(message: str) -> None:
    """Log a message to the terminal."""
    print(f"[auditor] {message}")


def _load_auditor_prompt(path: str) -> str:
    """Load the auditor prompt template from file.

    Args:
        path: Path to the auditor.md prompt file.

    Returns:
        The prompt template string.

    Raises:
        FileNotFoundError: If the prompt file doesn't exist.
    """
    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Auditor prompt not found: {path}")
    return prompt_path.read_text()


def _format_auditor_prompt(template: str, spec: str, diff: str) -> str:
    """Format the auditor prompt with spec and diff.

    Args:
        template: The prompt template string.
        spec: The specification to verify against.
        diff: The code changes to audit.

    Returns:
        The formatted prompt string.
    """
    result = template.replace("{{spec}}", spec)
    result = result.replace("{{diff}}", diff)
    return result


def _parse_verdict(output: str) -> AuditResult:
    """Parse the auditor's output to extract the verdict.

    Args:
        output: The raw output from the Claude auditor call.

    Returns:
        AuditResult with the parsed verdict and any feedback/reason.
    """
    # Normalize the output - strip and look for verdict patterns
    output = output.strip()

    # Look for PASS - can be standalone or in code block
    if re.search(r"^PASS\s*$", output, re.MULTILINE):
        return AuditResult(verdict=AuditVerdict.PASS)

    # Look for RETRY: with feedback
    retry_match = re.search(r"^RETRY:\s*(.+)", output, re.MULTILINE | re.DOTALL)
    if retry_match:
        # Get the feedback - everything after RETRY: until end or next section
        feedback = retry_match.group(1).strip()
        # Truncate at any code block end or reasonable length
        if "```" in feedback:
            feedback = feedback.split("```")[0].strip()
        return AuditResult(verdict=AuditVerdict.RETRY, feedback=feedback)

    # Look for ESCALATE: with reason
    escalate_match = re.search(r"^ESCALATE:\s*(.+)", output, re.MULTILINE | re.DOTALL)
    if escalate_match:
        reason = escalate_match.group(1).strip()
        if "```" in reason:
            reason = reason.split("```")[0].strip()
        return AuditResult(verdict=AuditVerdict.ESCALATE, reason=reason)

    # If we can't parse a clear verdict, default to RETRY with the full output as feedback
    # This is conservative - we don't want to PASS without explicit confirmation
    _log("Warning: Could not parse clear verdict, defaulting to RETRY")
    return AuditResult(
        verdict=AuditVerdict.RETRY,
        feedback=f"Auditor output was unclear. Raw output: {output[:500]}",
    )


def audit_implementation(
    spec: str,
    diff: str,
    prompt_path: str = "micro_v/prompts/auditor.md",
    timeout: int = 180,
    working_dir: Optional[str] = None,
) -> AuditResult:
    """Audit an implementation against its specification.

    Spawns a fresh Claude instance with only the spec and diff,
    no context from the coding session. This provides an independent
    review to catch green build hallucinations.

    Args:
        spec: The specification to verify against (story + criteria).
        diff: The code changes to audit (git diff or similar).
        prompt_path: Path to the auditor prompt template.
        timeout: Maximum time in seconds for the audit (default 180).
        working_dir: Optional working directory for the subprocess.

    Returns:
        AuditResult with verdict (PASS, RETRY, or ESCALATE) and any feedback/reason.

    Note:
        The Claude process is killed immediately after returning the verdict.
        ESCALATE should only be returned for genuine design ambiguity (high bar).
    """
    _log("Starting semantic audit")

    # Load the auditor prompt template
    try:
        template = _load_auditor_prompt(prompt_path)
    except FileNotFoundError as e:
        _log(f"Error: {e}")
        raise AuditorError(str(e)) from e

    # Format the prompt with spec and diff
    prompt = _format_auditor_prompt(template, spec, diff)

    # Invoke Claude auditor - fresh instance with only spec + diff
    _log("Invoking auditor...")
    stdout, stderr, exit_code = invoke_claude(
        prompt=prompt,
        timeout=timeout,
        working_dir=working_dir,
    )

    if exit_code != 0:
        _log(f"Auditor invocation failed (exit code {exit_code})")
        error_msg = stderr if stderr else "Claude invocation failed"
        _log(f"Error: {error_msg}")
        # On invocation failure, return RETRY to let the system try again
        return AuditResult(
            verdict=AuditVerdict.RETRY,
            feedback=f"Auditor invocation failed: {error_msg}",
        )

    _log("Auditor completed, parsing verdict...")

    # Parse the verdict from Claude's output
    result = _parse_verdict(stdout)

    _log(f"Verdict: {result.verdict.value}")
    if result.feedback:
        _log(f"Feedback: {result.feedback[:200]}...")
    if result.reason:
        _log(f"Reason: {result.reason[:200]}...")

    return result
