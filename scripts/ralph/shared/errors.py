"""Error classes with actionable suggestions for Ralph CLI.

Each error class includes a suggestion property that provides users with
actionable steps to resolve the issue.
"""


class RalphError(Exception):
    """Base class for all Ralph errors."""

    def __init__(self, message: str, suggestion: str = ""):
        super().__init__(message)
        self._suggestion = suggestion

    @property
    def suggestion(self) -> str:
        """Return an actionable suggestion to fix this error."""
        return self._suggestion


class PRDNotFoundError(RalphError):
    """Raised when the PRD file cannot be found."""

    def __init__(self, path: str = ""):
        message = f"PRD file not found: {path}" if path else "PRD file not found"
        suggestion = (
            f"Create a prd.json file at '{path}' with your project configuration. "
            "Use 'ralph init' to create a template, or see the quick-start guide."
            if path else
            "Specify the PRD file path with --prd or create a prd.json in the current directory."
        )
        super().__init__(message, suggestion)
        self.path = path


class ClaudeNotFoundError(RalphError):
    """Raised when the Claude CLI is not found or not accessible."""

    def __init__(self, path: str = "claude"):
        message = f"Claude CLI not found: {path}"
        suggestion = (
            "Install Claude Code by following the instructions at "
            "https://docs.anthropic.com/en/docs/claude-code. "
            "Ensure 'claude' is available in your PATH."
        )
        super().__init__(message, suggestion)
        self.path = path


class GitNotInitializedError(RalphError):
    """Raised when git is not initialized in the project directory."""

    def __init__(self, path: str = ""):
        message = f"Git repository not initialized in: {path}" if path else "Git repository not initialized"
        suggestion = (
            f"Initialize a git repository by running 'git init' in {path}. "
            "Ralph requires git to track changes and create commits."
            if path else
            "Initialize a git repository by running 'git init'. "
            "Ralph requires git to track changes and create commits."
        )
        super().__init__(message, suggestion)
        self.path = path


class ValidationFailedError(RalphError):
    """Raised when validation commands fail."""

    def __init__(self, command: str = "", output: str = ""):
        message = f"Validation failed for command: {command}" if command else "Validation failed"
        self.command = command
        self.output = output

        if output:
            suggestion = (
                f"Review the validation output for errors:\n{output}\n\n"
                "Fix the issues and retry the story, or use --skip-validation to bypass."
            )
        else:
            suggestion = (
                "Check that your validation commands are correct in the PRD file. "
                "Review the output above for specific errors."
            )
        super().__init__(message, suggestion)


class StoryNotFoundError(RalphError):
    """Raised when a specified story ID is not found in the PRD."""

    def __init__(self, story_id: str = "", available_ids: list[str] | None = None):
        message = f"Story not found: {story_id}" if story_id else "Story not found"
        self.story_id = story_id
        self.available_ids = available_ids or []

        if available_ids:
            ids_list = ", ".join(available_ids[:10])
            if len(available_ids) > 10:
                ids_list += f" ... ({len(available_ids) - 10} more)"
            suggestion = (
                f"Story '{story_id}' does not exist in the PRD. "
                f"Available story IDs: {ids_list}"
            )
        else:
            suggestion = (
                f"Story '{story_id}' does not exist in the PRD. "
                "Use 'ralph status' to see available stories."
                if story_id else
                "Use 'ralph status' to see available stories."
            )
        super().__init__(message, suggestion)
