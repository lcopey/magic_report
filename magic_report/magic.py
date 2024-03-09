from ipykernel.zmqshell import ZMQInteractiveShell
from IPython.core.magic import Magics, cell_magic, line_magic, magics_class

from .report import Report, to_clipboard


class MissingFileError(BaseException):
    ...


class MissingIdError(BaseException):
    ...


def _get_shell() -> ZMQInteractiveShell:
    shell: ZMQInteractiveShell = get_ipython()
    return shell


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

        shell = _get_shell()
        results = shell.ev(cell)
        self.report.write(line, results)
        return results

    @cell_magic
    def to_clipboard(self, line, cell):
        shell = _get_shell()
        results = shell.ev(cell)
        to_clipboard(results)
        return results


def load_ipython_extension(ipython: ZMQInteractiveShell):
    ipython.register_magics(ReportMagic)
