#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess
import termios
from typing import cast, Any, Dict, List, Optional, Tuple, Union

__author__ = "Ingo Heimbach"
__email__ = "i.heimbach@fz-juelich.de"
__copyright__ = "Copyright © 2019 Forschungszentrum Jülich GmbH. All rights reserved."
__license__ = "MIT"
__version_info__ = (0, 2, 0)
__version__ = ".".join(map(str, __version_info__))


DEFAULT_MENU_CURSOR = "> "
DEFAULT_MENU_CURSOR_STYLE = ("fg_red", "bold")
DEFAULT_MENU_HIGHLIGHT_STYLE = ("standout",)
DEFAULT_CYCLE_CURSOR = True


class TerminalMenu:
    _codename_to_capname = {
        "bg_black": None,
        "bg_blue": None,
        "bg_cyan": None,
        "bg_gray": None,
        "bg_green": None,
        "bg_purple": None,
        "bg_red": None,
        "bg_yellow": None,
        "bold": "bold",
        "cursor_down": "cud1",
        "cursor_invisible": "civis",
        "cursor_up": "cuu1",
        "cursor_visible": "cnorm",
        "delete_line": "dl1",
        "down": "kcud1",
        "enter": None,
        "enter_application_mode": "smkx",
        "escape": None,
        "exit_application_mode": "rmkx",
        "fg_black": None,
        "fg_blue": None,
        "fg_cyan": None,
        "fg_gray": None,
        "fg_green": None,
        "fg_purple": None,
        "fg_red": None,
        "fg_yellow": None,
        "italics": "sitm",
        "reset": None,
        "standout": "smso",
        "underline": "smul",
        "up": "kcuu1",
    }
    _terminfo_extensions = {
        "enter": "\012",
        "escape": "\033",
        "bg_black": "\033[40m",
        "bg_blue": "\033[44m",
        "bg_cyan": "\033[46m",
        "bg_gray": "\033[47m",
        "bg_green": "\033[42m",
        "bg_purple": "\033[45m",
        "bg_red": "\033[41m",
        "bg_yellow": "\033[43m",
        "fg_black": "\033[30m",
        "fg_blue": "\033[34m",
        "fg_cyan": "\033[36m",
        "fg_gray": "\033[37m",
        "fg_green": "\033[32m",
        "fg_purple": "\033[35m",
        "fg_red": "\033[31m",
        "fg_yellow": "\033[33m",
        "reset": "\033[0m",
    }
    _terminal_codes = None  # type: Optional[Dict[str, str]]
    _code_to_codename = None  # type: Optional[Dict[str, str]]

    def __init__(
        self,
        menu_entries: List[str],
        menu_cursor: Optional[str] = DEFAULT_MENU_CURSOR,
        menu_cursor_style: Optional[Tuple[str, ...]] = DEFAULT_MENU_CURSOR_STYLE,
        menu_highlight_style: Optional[Tuple[str, ...]] = DEFAULT_MENU_HIGHLIGHT_STYLE,
        cycle_cursor: bool = DEFAULT_CYCLE_CURSOR,
    ):
        self._fd = sys.stdin.fileno()
        self._menu_entries = menu_entries
        self._menu_cursor = menu_cursor if menu_cursor is not None else ""
        self._menu_cursor_style = menu_cursor_style if menu_cursor_style is not None else ()
        self._menu_highlight_style = menu_highlight_style if menu_highlight_style is not None else ()
        self._cycle_cursor = cycle_cursor
        self._old_term = None  # type: Optional[List[Union[int, List[bytes]]]]
        self._new_term = None  # type: Optional[List[Union[int, List[bytes]]]]
        self._init_terminal_codes()

    @classmethod
    def _init_terminal_codes(cls) -> None:
        if cls._terminal_codes is not None:
            return
        if int(cls._query_terminfo_database("colors")) < 8:
            for name in list(cls._terminfo_extensions.keys()):
                if name.startswith("fg_"):
                    cls._terminfo_extensions[name] = ""
        cls._codenames = tuple(cls._codename_to_capname.keys())
        cls._terminal_codes = {codename: cls._query_terminfo_database(codename) for codename in cls._codenames}
        cls._code_to_codename = {code: codename for codename, code in cls._terminal_codes.items()}

    @classmethod
    def _query_terminfo_database(cls, codename: str) -> str:
        if codename in cls._codename_to_capname:
            capname = cls._codename_to_capname[codename]
        else:
            capname = codename
        if capname is not None:
            return str(subprocess.check_output(["tput", capname], universal_newlines=True))
        else:
            return cls._terminfo_extensions[codename]

    def _init_term(self) -> None:
        assert self._terminal_codes is not None
        self._old_term = termios.tcgetattr(self._fd)
        self._new_term = termios.tcgetattr(self._fd)
        self._new_term[3] = cast(int, self._new_term[3]) & ~termios.ICANON & ~termios.ECHO  # unbuffered and no echo
        termios.tcsetattr(self._fd, termios.TCSAFLUSH, self._new_term)
        # Enter terminal application mode to get expected escape codes for arrow keys
        sys.stdout.write(self._terminal_codes["enter_application_mode"])
        sys.stdout.write(self._terminal_codes["cursor_invisible"])

    def _reset_term(self) -> None:
        assert self._terminal_codes is not None
        assert self._old_term is not None
        termios.tcsetattr(self._fd, termios.TCSAFLUSH, self._old_term)
        sys.stdout.write(self._terminal_codes["cursor_visible"])
        sys.stdout.write(self._terminal_codes["exit_application_mode"])

    def _read_next_key(self, ignore_case=True):
        code = os.read(self._fd, 80).decode("ascii")  # blocks until any amount of bytes is available
        if code in self._code_to_codename:
            return self._code_to_codename[code]
        elif ignore_case:
            return code.lower()
        else:
            return code

    def show(self) -> Optional[int]:
        def print_menu(selected_index: int) -> None:
            for i, menu_entry in enumerate(self._menu_entries):
                sys.stdout.write(len(self._menu_cursor) * " ")
                if i == selected_index:
                    for style in self._menu_highlight_style:
                        sys.stdout.write(self._terminal_codes[style])
                sys.stdout.write(menu_entry)
                if i == selected_index:
                    sys.stdout.write(self._terminal_codes["reset"])
                if i < len(self._menu_entries) - 1:
                    sys.stdout.write("\n")
            sys.stdout.write("\r" + (len(self._menu_entries) - 1) * self._terminal_codes["cursor_up"])

        def clear_menu() -> None:
            sys.stdout.write(len(self._menu_entries) * self._terminal_codes["delete_line"])

        def position_cursor(selected_index: int) -> None:
            # delete the first column
            sys.stdout.write(
                (len(self._menu_entries) - 1)
                * (len(self._menu_cursor) * " " + "\r" + self._terminal_codes["cursor_down"])
                + len(self._menu_cursor) * " "
                + "\r"
            )
            sys.stdout.write((len(self._menu_entries) - 1) * self._terminal_codes["cursor_up"])
            # position cursor and print menu selection character
            sys.stdout.write(selected_index * self._terminal_codes["cursor_down"])
            for style in self._menu_cursor_style:
                sys.stdout.write(self._terminal_codes[style])
            sys.stdout.write(self._menu_cursor)
            sys.stdout.write(self._terminal_codes["reset"] + "\r")
            sys.stdout.write(selected_index * self._terminal_codes["cursor_up"])

        assert self._terminal_codes is not None
        selected_index = 0  # type: Optional[int]
        self._init_term()
        try:
            while True:
                print_menu(selected_index)
                position_cursor(selected_index)
                next_key = self._read_next_key(ignore_case=True)
                if next_key in ("up", "k"):
                    selected_index -= 1
                    if selected_index < 0:
                        if self._cycle_cursor:
                            selected_index = len(self._menu_entries) - 1
                        else:
                            selected_index = 0
                elif next_key in ("down", "j"):
                    selected_index += 1
                    if selected_index >= len(self._menu_entries):
                        if self._cycle_cursor:
                            selected_index = 0
                        else:
                            selected_index = len(self._menu_entries) - 1
                elif next_key in ("enter",):
                    break
                elif next_key in ("escape",):
                    selected_index = None
                    break
        except KeyboardInterrupt:
            selected_index = None
        finally:
            clear_menu()
            self._reset_term()
        return selected_index


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
        "-V", "--version", action="store_true", dest="print_version", help="print the version number and exit"
    )
    parser.add_argument("entries", action="store", nargs="+", help="the menu entries to show")
    return parser


def parse_arguments() -> AttributeDict:
    parser = get_argumentparser()
    args = AttributeDict({key: value for key, value in vars(parser.parse_args()).items()})
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
    terminal_menu = TerminalMenu(
        menu_entries=args.entries,
        menu_cursor=args.cursor,
        menu_cursor_style=args.cursor_style,
        menu_highlight_style=args.highlight_style,
        cycle_cursor=args.cycle,
    )
    chosen_entry = terminal_menu.show()
    if chosen_entry is None:
        sys.exit(0)
    else:
        sys.exit(chosen_entry + 1)


if __name__ == "__main__":
    main()
