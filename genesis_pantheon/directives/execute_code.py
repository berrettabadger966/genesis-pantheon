"""ExecuteCode directive: runs Python code in a subprocess."""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path
from typing import Any

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import (
    DirectiveOutput,
    RunCodeContext,
    RunCodeResult,
)


class ExecuteCode(Directive):
    """Executes Python code or a test suite in a subprocess.

    Returns a RunCodeResult embedded in the DirectiveOutput.
    """

    name: str = "ExecuteCode"
    desc: str = "Execute Python code and capture output"

    async def run(  # type: ignore[override]
        self, context: Any = None, **kwargs: object
    ) -> DirectiveOutput:
        """Execute the code described in *context*.

        Args:
            context: RunCodeContext or code string.
            **kwargs: Ignored.

        Returns:
            DirectiveOutput with execution result.
        """
        if isinstance(context, RunCodeContext):
            result = await self._run_context(context)
        else:
            code = str(context) if context else ""
            result = await self._run_code_str(code)

        summary = (
            f"Exit code: {result.returncode}\n"
            f"Output:\n{result.stdout}"
        )
        return DirectiveOutput(
            content=summary, structured_content=result
        )

    async def _run_code_str(self, code: str) -> RunCodeResult:
        """Write *code* to a temp file and execute it.

        Args:
            code: Python source code string.

        Returns:
            RunCodeResult with stdout, stderr, and returncode.
        """
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            return await self._execute_file(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    async def _run_context(
        self, ctx: RunCodeContext
    ) -> RunCodeResult:
        """Execute code described by a RunCodeContext.

        Args:
            ctx: Full execution context.

        Returns:
            RunCodeResult.
        """
        if ctx.command:
            return await self._run_command(
                ctx.command, ctx.working_directory
            )
        if ctx.code:
            return await self._run_code_str(ctx.code)
        if ctx.code_filename:
            return await self._execute_file(
                ctx.code_filename, ctx.working_directory
            )
        return RunCodeResult(
            summary="No executable code provided.",
            stdout="",
            returncode=1,
        )

    async def _execute_file(
        self,
        filepath: str,
        cwd: str = "",
    ) -> RunCodeResult:
        """Run a Python file in a subprocess.

        Args:
            filepath: Path to the .py file.
            cwd: Working directory for the subprocess.

        Returns:
            RunCodeResult with captured output.
        """
        cmd = [sys.executable, filepath]
        return await self._run_command(cmd, cwd)

    async def _run_command(
        self,
        command: list,
        cwd: str = "",
    ) -> RunCodeResult:
        """Run an arbitrary command and capture its output.

        Args:
            command: Command and arguments list.
            cwd: Working directory.

        Returns:
            RunCodeResult with captured output.
        """
        kwargs: dict = {
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.STDOUT,
        }
        if cwd:
            kwargs["cwd"] = cwd
        try:
            proc = await asyncio.create_subprocess_exec(
                *command, **kwargs
            )
            stdout_bytes, _ = await asyncio.wait_for(
                proc.communicate(), timeout=120
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            returncode = proc.returncode or 0
        except asyncio.TimeoutError:
            stdout = "Execution timed out after 120 seconds."
            returncode = 124
        except Exception as exc:
            stdout = f"Failed to execute: {exc}"
            returncode = 1

        summary = (
            "Success" if returncode == 0 else "Failed"
        ) + f" (exit {returncode})"
        return RunCodeResult(
            summary=summary, stdout=stdout, returncode=returncode
        )


__all__ = ["ExecuteCode"]
