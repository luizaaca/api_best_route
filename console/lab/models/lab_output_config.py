"""Session-level output configuration for the console lab mode."""

from pydantic import BaseModel


class LabOutputConfig(BaseModel):
    """Represent how one lab session should expose its output.

    Attributes:
        plot: Whether plotting is enabled for the benchmark session.
        verbose: Whether optimizer console output is shown during execution.
        show_best_run_details: Whether the rendered report should include the
            detailed best-run section.
    """

    plot: bool = False
    verbose: bool = False
    show_best_run_details: bool = True
