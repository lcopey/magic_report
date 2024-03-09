import json
import math
from dataclasses import dataclass
from typing import Any

import plotly.graph_objects as go
from pandas.io.clipboard import clipboard_set

__all__ = ["Report"]


def quantize_json(value, float_offset: int = 1):
    if isinstance(value, float):
        if value == 0:
            return value
        power = math.floor(math.log10(abs(value)))
        if power < 0:
            formatter = "{{:.{}f}}".format(abs(power) + float_offset)
            value = float(formatter.format(value))
        elif power == 0:
            formatter = "{{:.{}f}}".format(1 + float_offset)
            value = float(formatter.format(value))
        else:
            value = int(f"{value:.0f}")

        return value

    elif isinstance(value, (list, tuple)):
        for n in range(len(value)):
            value[n] = quantize_json(value[n], float_offset)

    elif isinstance(value, dict):
        for key in value.keys():
            value[key] = quantize_json(value[key], float_offset)

    return value


def as_string(x, float_offset: int = 1) -> str:
    if hasattr(x, "to_json"):
        new_x = json.loads(x.to_json())
        if "layout" in new_x and "template" in new_x["layout"]:
            new_x["layout"].pop("template")
        return json.dumps(quantize_json(new_x, float_offset))
    elif hasattr(x, "_repr_html_"):
        return x._repr_html_()


def to_clipboard(x, float_offset: int = 1):
    clipboard_set(as_string(x, float_offset))


@dataclass
class Template:
    start: str
    end: str

    def format(self, section: str, text: str):
        return f"{self.start_id(section)}\n{text}\n{self.end_id(section)}"

    def start_id(self, section: str):
        return self.start.format(section)

    def end_id(self, section: str):
        return self.end.format(section)


PLOTLY_FIGURE = Template("```plotly <!-- id={} -->", "```\n")
HTML = Template(
    '<div id={} style="display: flex; align-items: center; justify-content: center">',
    "<!-- id={} --></div>\n",
)


@dataclass
class Section:
    lines: list[str]
    start: int = None
    end: int = None

    @classmethod
    def from_file_path(cls, file_path: str):
        with open(file_path, mode="r") as f:
            lines = f.readlines()
        return cls(lines=lines)

    @property
    def defined(self):
        return self.start is not None and self.end is not None

    def insert(self, text):
        if self.defined:
            for _ in range(self.start, self.end + 1):
                self.lines.pop(self.start)

            for line in text.splitlines(keepends=True)[::-1]:
                self.lines.insert(self.start, line)
        else:
            new_lines = text.splitlines(keepends=True)
            if self.lines[-1].strip() != "":
                new_lines.insert(0, "\n")
            self.lines.extend(new_lines)

    def find(self, start_id: str, end_id: str):
        self.start = None
        self.end = None
        for n, line in enumerate(self.lines):
            if line.strip() == start_id.strip():
                self.start = n
            if line.strip() == end_id.strip():
                self.end = n
            if self.defined:
                break

    def write(self, file_path: str):
        with open(file_path, mode="w") as f:
            f.writelines(self.lines)


class Report:
    def __init__(self, file_path):
        self.file_path = file_path

    def write(self, section_id: str, item: Any, float_offset: int = 1) -> str:
        if isinstance(item, go.Figure):
            template = PLOTLY_FIGURE
        elif hasattr(item, "_repr_html_"):
            template = HTML
        else:
            raise TypeError

        section = Section.from_file_path(self.file_path)
        section.find(template.start_id(section_id), template.end_id(section_id))

        text = as_string(item, float_offset=float_offset)
        text = template.format(section_id, text)

        section.insert(text)
        section.write(self.file_path)


def in_ipython():
    try:
        return __IPYTHON__
    except NameError:
        return False
