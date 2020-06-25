#!/usr/bin/env python3

import argparse
import os
import re
import shlex
import signal
import subprocess
import sys
from locale import getlocale
from types import FrameType
from typing import cast, Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

try:
    import termios
except ImportError:
    import platform

    raise NotImplementedError('"{}" is currently not supported.'.format(platform.system()))


__author__ = "Ingo Heimbach"
__email__ = "i.heimbach@fz-juelich.de"
__copyright__ = "Copyright © 2019 Forschungszentrum Jülich GmbH. All rights reserved."
__license__ = "MIT"
__version_info__ = (0, 6, 7)
__version__ = ".".join(map(str, __version_info__))


DEFAULT_MENU_CURSOR = "> "
DEFAULT_MENU_CURSOR_STYLE = ("fg_red", "bold")
DEFAULT_MENU_HIGHLIGHT_STYLE = ("standout",)
DEFAULT_CYCLE_CURSOR = True
DEFAULT_CLEAR_SCREEN = False
DEFAULT_PREVIEW_SIZE = 0.25
MIN_VISIBLE_MENU_ENTRIES_COUNT = 3


class InvalidStyleError(Exception):
    pass


class NoMenuEntriesError(Exception):
    pass


class PreviewCommandFailedError(Exception):
    pass


def static_variables(**variables: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        for key, value in variables.items():
            setattr(f, key, value)
        return f

    return decorator


class BoxDrawingCharacters:
    if getlocale()[1] == "UTF-8":
        # Unicode box characters
        horizontal = "─"
        vertical = "│"
        upper_left = "┌"
        upper_right = "┐"
        lower_left = "└"
        lower_right = "┘"
    else:
        # ASCII box characters
        horizontal = "-"
        vertical = "|"
        upper_left = "+"
        upper_right = "+"
        lower_left = "+"
        lower_right = "+"


class TerminalMenu:
    class Viewport:
        def __init__(
            self,
            num_menu_entries: int,
            title_lines_count: int,
            preview_lines_count: int,
            initial_cursor_position: int = 0,
        ):
            self._num_menu_entries = num_menu_entries
            self._title_lines_count = title_lines_count
            # Use the property setter since it has some more logic
            self.preview_lines_count = preview_lines_count
            self._num_lines = TerminalMenu._num_lines() - self._title_lines_count - self._preview_lines_count
            self._viewport = (0, min(self._num_menu_entries, self._num_lines) - 1)
            self.keep_visible(initial_cursor_position, refresh_terminal_size=False)

        def keep_visible(self, cursor_position: int, refresh_terminal_size: bool = True) -> None:
            if refresh_terminal_size:
                self.update_terminal_size()
            if self._viewport[0] <= cursor_position <= self._viewport[1]:
                # Cursor is already visible
                return
            if cursor_position < self._viewport[0]:
                scroll_num = cursor_position - self._viewport[0]
            else:
                scroll_num = cursor_position - self._viewport[1]
            self._viewport = (self._viewport[0] + scroll_num, self._viewport[1] + scroll_num)

        def update_terminal_size(self) -> None:
            num_lines = TerminalMenu._num_lines() - self._title_lines_count - self._preview_lines_count
            if num_lines != self._num_lines:
                # First let the upper index grow or shrink
                upper_index = min(num_lines, self._num_menu_entries) - 1
                # Then, use as much space as possible for the `lower_index`
                lower_index = max(0, upper_index - num_lines)
                self._viewport = (lower_index, upper_index)
                self._num_lines = num_lines

        @property
        def lower_index(self) -> int:
            return self._viewport[0]

        @property
        def upper_index(self) -> int:
            return self._viewport[1]

        @property
        def viewport(self) -> Tuple[int, int]:
            return self._viewport

        @property
        def size(self) -> int:
            return self._viewport[1] - self._viewport[0] + 1

        @property
        def num_menu_entries(self) -> int:
            return self._num_menu_entries

        @property
        def title_lines_count(self) -> int:
            return self._title_lines_count

        @property
        def preview_lines_count(self) -> int:
            return self._preview_lines_count

        @preview_lines_count.setter
        def preview_lines_count(self, value: int) -> None:
            self._preview_lines_count = min(
                value if value >= 3 else 0,
                TerminalMenu._num_lines() - self._title_lines_count - MIN_VISIBLE_MENU_ENTRIES_COUNT,
            )

    _codename_to_capname = {
        "bg_black": "setab 0",
        "bg_blue": "setab 4",
        "bg_cyan": "setab 6",
        "bg_gray": "setab 7",
        "bg_green": "setab 2",
        "bg_purple": "setab 5",
        "bg_red": "setab 1",
        "bg_yellow": "setab 3",
        "bold": "bold",
        "clear": "clear",
        "colors": "colors",
        "cursor_down": "cud1",
        "cursor_invisible": "civis",
        "cursor_up": "cuu1",
        "cursor_visible": "cnorm",
        "delete_line": "dl1",
        "down": "kcud1",
        "enter_application_mode": "smkx",
        "exit_application_mode": "rmkx",
        "fg_black": "setaf 0",
        "fg_blue": "setaf 4",
        "fg_cyan": "setaf 6",
        "fg_gray": "setaf 7",
        "fg_green": "setaf 2",
        "fg_purple": "setaf 5",
        "fg_red": "setaf 1",
        "fg_yellow": "setaf 3",
        "italics": "sitm",
        "reset_attributes": "sgr0",
        "standout": "smso",
        "underline": "smul",
        "up": "kcuu1",
    }
    _name_to_control_character = {"enter": "\012", "escape": "\033"}
    _codenames = tuple(_codename_to_capname.keys())
    _codename_to_terminal_code = None  # type: Optional[Dict[str, str]]
    _terminal_code_to_codename = None  # type: Optional[Dict[str, str]]

    def __init__(
        self,
        menu_entries: Iterable[str],
        title: Optional[Union[str, Iterable[str]]] = None,
        menu_cursor: Optional[str] = DEFAULT_MENU_CURSOR,
        menu_cursor_style: Optional[Iterable[str]] = DEFAULT_MENU_CURSOR_STYLE,
        menu_highlight_style: Optional[Iterable[str]] = DEFAULT_MENU_HIGHLIGHT_STYLE,
        cycle_cursor: bool = DEFAULT_CYCLE_CURSOR,
        clear_screen: bool = DEFAULT_CLEAR_SCREEN,
        preview_command: Optional[Union[str, Callable[[str], str]]] = None,
        preview_size: float = DEFAULT_PREVIEW_SIZE,
    ):
        def extract_menu_entries_and_preview_arguments(entries: Iterable[str]) -> Tuple[List[str], List[str]]:
            separator_pattern = re.compile(r"([^\\])\|")
            escaped_separator_pattern = re.compile(r"\\\|")
            menu_entry_pattern = re.compile(r"^([^\x1F]+)(\x1F([^\x1F]*))?")
            menu_entries = []
            preview_arguments = []
            for entry in entries:
                unit_separated_entry = escaped_separator_pattern.sub("|", separator_pattern.sub("\\1\x1F", entry))
                match_obj = menu_entry_pattern.match(unit_separated_entry)
                assert match_obj is not None
                display_text = match_obj.group(1)
                preview_argument = match_obj.group(3)
                menu_entries.append(display_text)
                preview_arguments.append(preview_argument)
            return menu_entries, preview_arguments

        self._fd = sys.stdin.fileno()
        self._menu_entries, self._preview_arguments = extract_menu_entries_and_preview_arguments(menu_entries)
        if title is None:
            self._title_lines = ()  # type: Tuple[str, ...]
        elif isinstance(title, str):
            self._title_lines = tuple(title.split("\n"))
        else:
            self._title_lines = tuple(title)
        self._menu_cursor = menu_cursor if menu_cursor is not None else ""
        self._menu_cursor_style = tuple(menu_cursor_style) if menu_cursor_style is not None else ()
        self._menu_highlight_style = tuple(menu_highlight_style) if menu_highlight_style is not None else ()
        self._cycle_cursor = cycle_cursor
        self._clear_screen = clear_screen
        self._preview_command = preview_command
        self._preview_size = preview_size
        self._selected_index = None  # type: Optional[int]
        self._viewport = self.Viewport(len(self._menu_entries), len(self._title_lines), 0)
        self._previous_preview_num_lines = None  # type: Optional[int]
        self._reading_next_key = False
        self._paint_before_next_read = False
        self._old_term = None  # type: Optional[List[Union[int, List[bytes]]]]
        self._new_term = None  # type: Optional[List[Union[int, List[bytes]]]]
        self._check_for_valid_styles()
        self._init_terminal_codes()

    @classmethod
    def _init_terminal_codes(cls) -> None:
        if cls._codename_to_terminal_code is not None:
            return
        supported_colors = int(cls._query_terminfo_database("colors"))
        cls._codename_to_terminal_code = {
            codename: cls._query_terminfo_database(codename)
            if not (codename.startswith("bg_") or codename.startswith("fg_")) or supported_colors >= 8
            else ""
            for codename in cls._codenames
        }
        cls._codename_to_terminal_code.update(cls._name_to_control_character)
        cls._terminal_code_to_codename = {
            terminal_code: codename for codename, terminal_code in cls._codename_to_terminal_code.items()
        }

    @classmethod
    def _query_terminfo_database(cls, codename: str) -> str:
        if codename in cls._codename_to_capname:
            capname = cls._codename_to_capname[codename]
        else:
            capname = codename
        try:
            return str(subprocess.check_output(["tput"] + capname.split(), universal_newlines=True))
        except subprocess.CalledProcessError as e:
            # The return code 1 indicates a missing terminal capability
            if e.returncode == 1:
                return ""
            raise e

    @classmethod
    def _num_lines(self) -> int:
        return int(self._query_terminfo_database("lines"))

    @classmethod
    def _num_cols(self) -> int:
        return int(self._query_terminfo_database("cols"))

    def _check_for_valid_styles(self) -> None:
        invalid_styles = []
        for style_tuple in (self._menu_cursor_style, self._menu_highlight_style):
            for style in style_tuple:
                if style not in self._codename_to_capname:
                    invalid_styles.append(style)
        if invalid_styles:
            if len(invalid_styles) == 1:
                raise InvalidStyleError('The style "{}" does not exist.'.format(invalid_styles[0]))
            else:
                raise InvalidStyleError('The styles ("{}") do not exist.'.format('", "'.join(invalid_styles)))

    def _init_term(self) -> None:
        # pylint: disable=unsubscriptable-object
        assert self._codename_to_terminal_code is not None
        self._old_term = termios.tcgetattr(self._fd)
        self._new_term = termios.tcgetattr(self._fd)
        self._new_term[3] = cast(int, self._new_term[3]) & ~termios.ICANON & ~termios.ECHO  # unbuffered and no echo
        termios.tcsetattr(self._fd, termios.TCSAFLUSH, self._new_term)
        # Enter terminal application mode to get expected escape codes for arrow keys
        sys.stdout.write(self._codename_to_terminal_code["enter_application_mode"])
        sys.stdout.write(self._codename_to_terminal_code["cursor_invisible"])
        if self._clear_screen:
            sys.stdout.write(self._codename_to_terminal_code["clear"])

    def _reset_term(self) -> None:
        # pylint: disable=unsubscriptable-object
        assert self._codename_to_terminal_code is not None
        assert self._old_term is not None
        termios.tcsetattr(self._fd, termios.TCSAFLUSH, self._old_term)
        sys.stdout.write(self._codename_to_terminal_code["cursor_visible"])
        sys.stdout.write(self._codename_to_terminal_code["exit_application_mode"])
        if self._clear_screen:
            sys.stdout.write(self._codename_to_terminal_code["clear"])

    def _paint_menu(self) -> None:
        def print_menu_entries() -> None:
            # pylint: disable=unsubscriptable-object
            assert self._codename_to_terminal_code is not None
            num_cols = self._num_cols()
            if self._title_lines:
                sys.stdout.write(
                    len(self._title_lines) * self._codename_to_terminal_code["cursor_up"]
                    + "\r"
                    + "\n".join(
                        (title_line[:num_cols] + (num_cols - len(title_line)) * " ") for title_line in self._title_lines
                    )
                    + "\n"
                )
            for i, menu_entry in enumerate(
                self._menu_entries[self._viewport.lower_index :], self._viewport.lower_index
            ):
                sys.stdout.write(len(self._menu_cursor) * " ")
                if i == self._selected_index:
                    for style in self._menu_highlight_style:
                        sys.stdout.write(self._codename_to_terminal_code[style])
                sys.stdout.write(menu_entry[: num_cols - len(self._menu_cursor)])
                if i == self._selected_index:
                    sys.stdout.write(self._codename_to_terminal_code["reset_attributes"])
                sys.stdout.write((num_cols - len(menu_entry) - len(self._menu_cursor)) * " ")
                if i >= self._viewport.upper_index:
                    break
                if i < len(self._menu_entries) - 1:
                    sys.stdout.write("\n")
            sys.stdout.write("\r" + (self._viewport.size - 1) * self._codename_to_terminal_code["cursor_up"])

        def print_preview(preview_max_num_lines: int) -> None:
            # pylint: disable=unsubscriptable-object
            assert self._codename_to_terminal_code is not None
            if self._preview_command is None or preview_max_num_lines < 3:
                return

            def get_preview_string() -> Optional[str]:
                assert self._preview_command is not None
                assert self._selected_index is not None
                preview_argument = (
                    self._preview_arguments[self._selected_index]
                    if self._preview_arguments[self._selected_index] is not None
                    else self._menu_entries[self._selected_index]
                )
                if preview_argument == "":
                    return None
                if isinstance(self._preview_command, str):
                    try:
                        preview_string = subprocess.check_output(
                            [cmd_part.format(preview_argument) for cmd_part in shlex.split(self._preview_command)],
                            stderr=subprocess.PIPE,
                            universal_newlines=True,
                        ).strip()
                    except subprocess.CalledProcessError as e:
                        raise PreviewCommandFailedError(e.stderr.strip())
                else:
                    preview_string = self._preview_command(preview_argument)
                return preview_string

            @static_variables(
                # Regex taken from https://stackoverflow.com/a/14693789/5958465
                ansi_escape_regex=re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"),
                # Modified version of https://stackoverflow.com/a/2188410/5958465
                ansi_sgr_regex=re.compile(r"\x1B\[[;\d]*m"),
            )
            def strip_ansi_codes_except_styling(string: str) -> str:
                stripped_string = strip_ansi_codes_except_styling.ansi_escape_regex.sub(  # type: ignore
                    lambda match_obj: match_obj.group(0)
                    if strip_ansi_codes_except_styling.ansi_sgr_regex.match(match_obj.group(0))  # type: ignore
                    else "",
                    string,
                )
                return cast(str, stripped_string)

            @static_variables(
                regular_text_regex=re.compile(r"([^\x1B]+)(.*)"),
                ansi_escape_regex=re.compile(r"(\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]))(.*)"),
            )
            def limit_string_with_escape_codes(string: str, max_len: int) -> Tuple[str, int]:
                if max_len <= 0:
                    return "", 0
                string_parts = []
                string_len = 0
                while string:
                    regular_text_match = limit_string_with_escape_codes.regular_text_regex.match(string)  # type: ignore
                    if regular_text_match is not None:
                        regular_text = regular_text_match.group(1)
                        regular_text_len = len(regular_text)
                        if string_len + regular_text_len > max_len:
                            string_parts.append(regular_text[: max_len - string_len])
                            string_len = max_len
                            break
                        string_parts.append(regular_text)
                        string_len += regular_text_len
                        string = regular_text_match.group(2)
                    else:
                        ansi_escape_match = limit_string_with_escape_codes.ansi_escape_regex.match(  # type: ignore
                            string
                        )
                        if ansi_escape_match is not None:
                            # Adopt the ansi escape code but do not count its length
                            ansi_escape_code_text = ansi_escape_match.group(1)
                            string_parts.append(ansi_escape_code_text)
                            string = ansi_escape_match.group(2)
                        else:
                            # It looks like an escape code (starts with escape), but it is something else
                            # -> skip the escape character and continue the loop
                            string_parts.append("\x1B")
                            string = string[1:]
                return "".join(string_parts), string_len

            num_cols = self._num_cols()
            try:
                preview_string = get_preview_string()
                if preview_string is not None:
                    preview_string = strip_ansi_codes_except_styling(preview_string)
            except PreviewCommandFailedError as e:
                preview_string = "The preview command failed with error message:\n\n" + str(e)
            sys.stdout.write((self._viewport.size - 1) * self._codename_to_terminal_code["cursor_down"])
            if preview_string is not None:
                sys.stdout.write(
                    self._codename_to_terminal_code["cursor_down"]
                    + "\r"
                    + (
                        BoxDrawingCharacters.upper_left
                        + (2 * BoxDrawingCharacters.horizontal + " preview")[: num_cols - 3]
                        + " "
                        + (num_cols - 13) * BoxDrawingCharacters.horizontal
                        + BoxDrawingCharacters.upper_right
                    )[:num_cols]
                    + "\n"
                )
                # `finditer` can be used as a generator version of `str.join`
                for i, line in enumerate(
                    match.group(0) for match in re.finditer(r"^.*$", preview_string, re.MULTILINE)
                ):
                    if i >= preview_max_num_lines - 2:
                        preview_num_lines = preview_max_num_lines
                        break
                    limited_line, limited_line_len = limit_string_with_escape_codes(line, num_cols - 3)
                    sys.stdout.write(
                        (
                            BoxDrawingCharacters.vertical
                            + (
                                " "
                                + limited_line
                                + self._codename_to_terminal_code["reset_attributes"]
                                + max(num_cols - limited_line_len - 3, 0) * " "
                            )
                            + BoxDrawingCharacters.vertical
                        )
                        + "\n"
                    )
                else:
                    preview_num_lines = i + 3
                sys.stdout.write(
                    (
                        BoxDrawingCharacters.lower_left
                        + (num_cols - 2) * BoxDrawingCharacters.horizontal
                        + BoxDrawingCharacters.lower_right
                    )[:num_cols]
                    + "\r"
                )
            else:
                preview_num_lines = 0
            if self._previous_preview_num_lines is not None and self._previous_preview_num_lines > preview_num_lines:
                sys.stdout.write(self._codename_to_terminal_code["cursor_down"])
                sys.stdout.write(
                    (self._previous_preview_num_lines - preview_num_lines)
                    * self._codename_to_terminal_code["delete_line"]
                )
                sys.stdout.write(self._codename_to_terminal_code["cursor_up"])
            sys.stdout.write(
                (self._viewport.size + preview_num_lines - 1) * self._codename_to_terminal_code["cursor_up"]
            )
            self._previous_preview_num_lines = preview_num_lines

        def position_cursor() -> None:
            # pylint: disable=unsubscriptable-object
            assert self._codename_to_terminal_code is not None
            assert self._selected_index is not None
            # delete the first column
            sys.stdout.write(
                (self._viewport.size - 1)
                * (len(self._menu_cursor) * " " + "\r" + self._codename_to_terminal_code["cursor_down"])
                + len(self._menu_cursor) * " "
                + "\r"
            )
            sys.stdout.write((self._viewport.size - 1) * self._codename_to_terminal_code["cursor_up"])
            # position cursor and print menu selection character
            sys.stdout.write(
                (self._selected_index - self._viewport.lower_index) * self._codename_to_terminal_code["cursor_down"]
            )
            for style in self._menu_cursor_style:
                sys.stdout.write(self._codename_to_terminal_code[style])
            sys.stdout.write(self._menu_cursor)
            sys.stdout.write(self._codename_to_terminal_code["reset_attributes"] + "\r")
            sys.stdout.write(
                (self._selected_index - self._viewport.lower_index) * self._codename_to_terminal_code["cursor_up"]
            )

        # pylint: disable=unsubscriptable-object
        assert self._codename_to_terminal_code is not None
        if self._selected_index is None:
            self._selected_index = 0
        if self._preview_command is not None:
            self._viewport.preview_lines_count = int(self._preview_size * self._num_lines())
            preview_max_num_lines = self._viewport.preview_lines_count
        self._viewport.keep_visible(self._selected_index)
        print_menu_entries()
        if self._preview_command is not None:
            print_preview(preview_max_num_lines)
        position_cursor()

    def _clear_menu(self) -> None:
        # pylint: disable=unsubscriptable-object
        assert self._codename_to_terminal_code is not None
        if self._title_lines:
            sys.stdout.write(len(self._title_lines) * self._codename_to_terminal_code["cursor_up"])
            sys.stdout.write(len(self._title_lines) * self._codename_to_terminal_code["delete_line"])
        preview_num_lines = self._previous_preview_num_lines if self._previous_preview_num_lines is not None else 0
        sys.stdout.write((self._viewport.size + preview_num_lines) * self._codename_to_terminal_code["delete_line"])
        sys.stdout.flush()

    def _read_next_key(self, ignore_case: bool = True) -> str:
        # pylint: disable=unsubscriptable-object,unsupported-membership-test
        assert self._terminal_code_to_codename is not None
        # Needed for asynchronous handling of terminal resize events
        self._reading_next_key = True
        if self._paint_before_next_read:
            self._paint_menu()
            self._paint_before_next_read = False
        code = os.read(self._fd, 80).decode("ascii")  # blocks until any amount of bytes is available
        self._reading_next_key = False
        if code in self._terminal_code_to_codename:
            return self._terminal_code_to_codename[code]
        elif ignore_case:
            return code.lower()
        else:
            return code

    def show(self) -> Optional[int]:
        def init_signal_handling() -> None:
            # `SIGWINCH` is send on terminal resizes
            def handle_sigwinch(signum: signal.Signals, frame: FrameType) -> None:
                # pylint: disable=unused-argument
                if self._reading_next_key:
                    self._paint_menu()
                else:
                    self._paint_before_next_read = True

            signal.signal(signal.SIGWINCH, handle_sigwinch)

        def reset_signal_handling() -> None:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)

        # pylint: disable=unsubscriptable-object
        assert self._codename_to_terminal_code is not None
        self._init_term()
        self._selected_index = 0
        if self._title_lines:
            # `print_menu` expects the cursor on the first menu item -> reserve one line for the title
            sys.stdout.write(len(self._title_lines) * self._codename_to_terminal_code["cursor_down"])
        try:
            init_signal_handling()
            while True:
                self._paint_menu()
                next_key = self._read_next_key(ignore_case=True)
                if next_key in ("up", "k"):
                    self._selected_index -= 1
                    if self._selected_index < 0:
                        if self._cycle_cursor:
                            self._selected_index = len(self._menu_entries) - 1
                        else:
                            self._selected_index = 0
                elif next_key in ("down", "j"):
                    self._selected_index += 1
                    if self._selected_index >= len(self._menu_entries):
                        if self._cycle_cursor:
                            self._selected_index = 0
                        else:
                            self._selected_index = len(self._menu_entries) - 1
                elif next_key in ("enter",):
                    break
                elif next_key in ("escape", "q"):
                    self._selected_index = None
                    break
        except KeyboardInterrupt:
            self._selected_index = None
        finally:
            reset_signal_handling()
            self._clear_menu()
            self._reset_term()
        return self._selected_index


class AttributeDict(dict):  # type: ignore
    def __getattr__(self, attr: str) -> Any:
        return self[attr]

    def __setattr__(self, attr: str, value: Any) -> None:
        self[attr] = value


def get_argumentparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
%(prog)s creates simple interactive menus in the terminal and returns the selected entry as exit code.
""",
    )
    parser.add_argument("-t", "--title", action="store", dest="title", help="menu title")
    parser.add_argument(
        "-c",
        "--cursor",
        action="store",
        dest="cursor",
        default=DEFAULT_MENU_CURSOR,
        help="menu cursor (default: %(default)s)",
    )
    parser.add_argument(
        "-s",
        "--cursor_style",
        action="store",
        dest="cursor_style",
        default=",".join(DEFAULT_MENU_CURSOR_STYLE),
        help="style for the menu cursor as comma separated list (default: %(default)s)",
    )
    parser.add_argument(
        "-m",
        "--highlight_style",
        action="store",
        dest="highlight_style",
        default=",".join(DEFAULT_MENU_HIGHLIGHT_STYLE),
        help="style for the selected menu entry as comma separated list (default: %(default)s)",
    )
    parser.add_argument("-C", "--no-cycle", action="store_false", dest="cycle", help="do not cycle the menu selection")
    parser.add_argument(
        "-l",
        "--clear-screen",
        action="store_true",
        dest="clear_screen",
        help="clear the screen before the menu is shown",
    )
    parser.add_argument(
        "-p",
        "--preview",
        action="store",
        dest="preview_command",
        help=(
            "Command to generate a preview for the selected menu entry. "
            '"{}" can be used as placeholder for the menu text. '
            'If the menu entry has a data component (separated by "|"), this is used instead.'
        ),
    )
    parser.add_argument(
        "--preview-size",
        action="store",
        dest="preview_size",
        type=float,
        default=DEFAULT_PREVIEW_SIZE,
        help="maximum height of the preview window in fractions of the terminal height (default: %(default)s)",
    )
    parser.add_argument(
        "-V", "--version", action="store_true", dest="print_version", help="print the version number and exit"
    )
    parser.add_argument("entries", action="store", nargs="*", help="the menu entries to show")
    return parser


def parse_arguments() -> AttributeDict:
    parser = get_argumentparser()
    args = AttributeDict({key: value for key, value in vars(parser.parse_args()).items()})
    if not args.print_version and not args.entries:
        raise NoMenuEntriesError("No menu entries given!")
    if args.cursor_style != "":
        args.cursor_style = tuple(args.cursor_style.split(","))
    else:
        args.cursor_style = None
    if args.highlight_style != "":
        args.highlight_style = tuple(args.highlight_style.split(","))
    else:
        args.highlight_style = None
    return args


def main() -> None:
    try:
        args = parse_arguments()
    except SystemExit:
        sys.exit(0)  # Error code 0 is the error case in this program
    except NoMenuEntriesError as e:
        print(str(e), file=sys.stderr)
        sys.exit(0)
    if args.print_version:
        print("{}, version {}".format(os.path.basename(sys.argv[0]), __version__))
        sys.exit(0)
    try:
        terminal_menu = TerminalMenu(
            menu_entries=args.entries,
            title=args.title,
            menu_cursor=args.cursor,
            menu_cursor_style=args.cursor_style,
            menu_highlight_style=args.highlight_style,
            cycle_cursor=args.cycle,
            clear_screen=args.clear_screen,
            preview_command=args.preview_command,
            preview_size=args.preview_size,
        )
    except InvalidStyleError as e:
        print(str(e), file=sys.stderr)
        sys.exit(0)
    chosen_entry = terminal_menu.show()
    if chosen_entry is None:
        sys.exit(0)
    else:
        sys.exit(chosen_entry + 1)


if __name__ == "__main__":
    main()
