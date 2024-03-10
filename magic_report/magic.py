from ipykernel.zmqshell import ZMQInteractiveShell
from IPython.core.magic import Magics, cell_magic, line_magic, magics_class

from .report import Report, to_clipboard, to_markdown_table


class MissingFileError(BaseException):
    ...


class MissingIdError(BaseException):
    ...


@magics_class
class ReportMagic(Magics):
    def __init__(self, shell):
        super().__init__(shell)
        self.report = None

    @line_magic
    def report_file(self, file_path: str):
        self.report = Report(file_path)

    @cell_magic
    def to_report(self, line, cell):
        if self.report is None:
            raise MissingFileError(
                "missing file_path, have you called report_file magic ?"
            )
        if line is None:
            raise MissingIdError("missing id in the magic")

        shell_results = self.shell.run_cell(cell)
        if shell_results.result is not None:
            self.report.write(line, shell_results.result)

    @cell_magic
    def to_clipboard(self, line, cell):
        shell_results = self.shell.run_cell(cell)
        if shell_results.result is not None:
            if line is None:
                to_clipboard(shell_results.result)
            elif line == "markdown":
                to_clipboard(to_markdown_table(shell_results.result))


def load_ipython_extension(ipython: ZMQInteractiveShell):
    ipython.register_magics(ReportMagic)
