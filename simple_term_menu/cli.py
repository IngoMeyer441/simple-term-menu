import argparse
import sys
from typing import Any, Iterable

from .terminal_menu import (
    DEFAULT_MENU_CURSOR,
    DEFAULT_MENU_CURSOR_STYLE,
    DEFAULT_MENU_HIGHLIGHT_STYLE,
    DEFAULT_MULTI_SELECT_CURSOR,
    DEFAULT_MULTI_SELECT_CURSOR_BRACKETS_STYLE,
    DEFAULT_MULTI_SELECT_CURSOR_STYLE,
    DEFAULT_MULTI_SELECT_KEYS,
    DEFAULT_PREVIEW_SIZE,
    DEFAULT_PREVIEW_TITLE,
    DEFAULT_SEARCH_HIGHLIGHT_STYLE,
    DEFAULT_SEARCH_KEY,
    DEFAULT_SHORTCUT_BRACKETS_HIGHLIGHT_STYLE,
    DEFAULT_SHORTCUT_KEY_HIGHLIGHT_STYLE,
    DEFAULT_STATUS_BAR_STYLE,
    TerminalMenu,
)


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
        "-s", "--case-sensitive", action="store_true", dest="case_sensitive", help="searches are case sensitive"
    )
    parser.add_argument(
        "-X",
        "--no-clear-menu-on-exit",
        action="store_false",
        dest="clear_menu_on_exit",
        help="do not clear the menu on exit",
    )
    parser.add_argument(
        "-l",
        "--clear-screen",
        action="store_true",
        dest="clear_screen",
        help="clear the screen before the menu is shown",
    )
    parser.add_argument(
        "--cursor",
        action="store",
        dest="cursor",
        default=DEFAULT_MENU_CURSOR,
        help='menu cursor (default: "%(default)s")',
    )
    parser.add_argument(
        "-i",
        "--cursor-index",
        action="store",
        dest="cursor_index",
        type=int,
        default=0,
        help="initially selected item index",
    )
    parser.add_argument(
        "--cursor-style",
        action="store",
        dest="cursor_style",
        default=",".join(DEFAULT_MENU_CURSOR_STYLE),
        help='style for the menu cursor as comma separated list (default: "%(default)s")',
    )
    parser.add_argument("-C", "--no-cycle", action="store_false", dest="cycle", help="do not cycle the menu selection")
    parser.add_argument(
        "-E",
        "--no-exit-on-shortcut",
        action="store_false",
        dest="exit_on_shortcut",
        help="do not exit on shortcut keys",
    )
    parser.add_argument(
        "--highlight-style",
        action="store",
        dest="highlight_style",
        default=",".join(DEFAULT_MENU_HIGHLIGHT_STYLE),
        help='style for the selected menu entry as comma separated list (default: "%(default)s")',
    )
    parser.add_argument(
        "-m",
        "--multi-select",
        action="store_true",
        dest="multi_select",
        help="Allow the selection of multiple entries (implies `--stdout`)",
    )
    parser.add_argument(
        "--multi-select-cursor",
        action="store",
        dest="multi_select_cursor",
        default=DEFAULT_MULTI_SELECT_CURSOR,
        help='multi-select menu cursor (default: "%(default)s")',
    )
    parser.add_argument(
        "--multi-select-cursor-brackets-style",
        action="store",
        dest="multi_select_cursor_brackets_style",
        default=",".join(DEFAULT_MULTI_SELECT_CURSOR_BRACKETS_STYLE),
        help='style for brackets of the multi-select menu cursor as comma separated list (default: "%(default)s")',
    )
    parser.add_argument(
        "--multi-select-cursor-style",
        action="store",
        dest="multi_select_cursor_style",
        default=",".join(DEFAULT_MULTI_SELECT_CURSOR_STYLE),
        help='style for the multi-select menu cursor as comma separated list (default: "%(default)s")',
    )
    parser.add_argument(
        "--multi-select-keys",
        action="store",
        dest="multi_select_keys",
        default=",".join(DEFAULT_MULTI_SELECT_KEYS),
        help=('key for toggling a selected item in a multi-selection (default: "%(default)s", '),
    )
    parser.add_argument(
        "--multi-select-no-select-on-accept",
        action="store_false",
        dest="multi_select_select_on_accept",
        help=(
            "do not select the currently highlighted menu item when the accept key is pressed "
            "(it is still selected if no other item was selected before)"
        ),
    )
    parser.add_argument(
        "--multi-select-empty-ok",
        action="store_true",
        dest="multi_select_empty_ok",
        help=("when used together with --multi-select-no-select-on-accept allows returning no selection at all"),
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
        "--no-preview-border",
        action="store_false",
        dest="preview_border",
        help="do not draw a border around the preview window",
    )
    parser.add_argument(
        "--preview-size",
        action="store",
        dest="preview_size",
        type=float,
        default=DEFAULT_PREVIEW_SIZE,
        help='maximum height of the preview window in fractions of the terminal height (default: "%(default)s")',
    )
    parser.add_argument(
        "--preview-title",
        action="store",
        dest="preview_title",
        default=DEFAULT_PREVIEW_TITLE,
        help='title of the preview window (default: "%(default)s")',
    )
    parser.add_argument(
        "--search-highlight-style",
        action="store",
        dest="search_highlight_style",
        default=",".join(DEFAULT_SEARCH_HIGHLIGHT_STYLE),
        help='style of matched search patterns (default: "%(default)s")',
    )
    parser.add_argument(
        "--search-key",
        action="store",
        dest="search_key",
        default=DEFAULT_SEARCH_KEY,
        help=(
            'key to start a search (default: "%(default)s", '
            '"none" is treated a special value which activates the search on any letter key)'
        ),
    )
    parser.add_argument(
        "--shortcut-brackets-highlight-style",
        action="store",
        dest="shortcut_brackets_highlight_style",
        default=",".join(DEFAULT_SHORTCUT_BRACKETS_HIGHLIGHT_STYLE),
        help='style of brackets enclosing shortcut keys (default: "%(default)s")',
    )
    parser.add_argument(
        "--shortcut-key-highlight-style",
        action="store",
        dest="shortcut_key_highlight_style",
        default=",".join(DEFAULT_SHORTCUT_KEY_HIGHLIGHT_STYLE),
        help='style of shortcut keys (default: "%(default)s")',
    )
    parser.add_argument(
        "--show-multi-select-hint",
        action="store_true",
        dest="show_multi_select_hint",
        help="show a multi-select hint in the status bar",
    )
    parser.add_argument(
        "--show-multi-select-hint-text",
        action="store",
        dest="show_multi_select_hint_text",
        help=(
            "Custom text which will be shown as multi-select hint. Use the placeholders {multi_select_keys} and "
            "{accept_keys} if appropriately."
        ),
    )
    parser.add_argument(
        "--show-search-hint",
        action="store_true",
        dest="show_search_hint",
        help="show a search hint in the search line",
    )
    parser.add_argument(
        "--show-search-hint-text",
        action="store",
        dest="show_search_hint_text",
        help=(
            "Custom text which will be shown as search hint. Use the placeholders {key} for the search key "
            "if appropriately."
        ),
    )
    parser.add_argument(
        "--show-shortcut-hints",
        action="store_true",
        dest="show_shortcut_hints",
        help="show shortcut hints in the status bar",
    )
    parser.add_argument(
        "--show-shortcut-hints-in-title",
        action="store_false",
        dest="show_shortcut_hints_in_status_bar",
        default=True,
        help="show shortcut hints in the menu title",
    )
    parser.add_argument(
        "-b",
        "--status-bar",
        action="store",
        dest="status_bar",
        help="status bar text",
    )
    parser.add_argument(
        "-d",
        "--status-bar-below-preview",
        action="store_true",
        dest="status_bar_below_preview",
        help="show the status bar below the preview window if any",
    )
    parser.add_argument(
        "--status-bar-style",
        action="store",
        dest="status_bar_style",
        default=",".join(DEFAULT_STATUS_BAR_STYLE),
        help='style of the status bar lines (default: "%(default)s")',
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        dest="stdout",
        help=(
            "Print the selected menu index or indices to stdout (in addition to the exit status). "
            'Multiple indices are separated by ";".'
        ),
    )
    parser.add_argument("-t", "--title", action="store", dest="title", help="menu title")
    parser.add_argument(
        "-V", "--version", action="store_true", dest="print_version", help="print the version number and exit"
    )
    parser.add_argument("entries", action="store", nargs="*", help="the menu entries to show")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-r",
        "--preselected_entries",
        action="store",
        dest="preselected_entries",
        help="Comma separated list of strings matching menu items to start pre-selected in a multi-select menu.",
    )
    group.add_argument(
        "-R",
        "--preselected_indices",
        action="store",
        dest="preselected_indices",
        help="Comma separated list of numeric indexes of menu items to start pre-selected in a multi-select menu.",
    )
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
    if args.search_highlight_style != "":
        args.search_highlight_style = tuple(args.search_highlight_style.split(","))
    else:
        args.search_highlight_style = None
    if args.shortcut_key_highlight_style != "":
        args.shortcut_key_highlight_style = tuple(args.shortcut_key_highlight_style.split(","))
    else:
        args.shortcut_key_highlight_style = None
    if args.shortcut_brackets_highlight_style != "":
        args.shortcut_brackets_highlight_style = tuple(args.shortcut_brackets_highlight_style.split(","))
    else:
        args.shortcut_brackets_highlight_style = None
    if args.status_bar_style != "":
        args.status_bar_style = tuple(args.status_bar_style.split(","))
    else:
        args.status_bar_style = None
    if args.multi_select_cursor_brackets_style != "":
        args.multi_select_cursor_brackets_style = tuple(args.multi_select_cursor_brackets_style.split(","))
    else:
        args.multi_select_cursor_brackets_style = None
    if args.multi_select_cursor_style != "":
        args.multi_select_cursor_style = tuple(args.multi_select_cursor_style.split(","))
    else:
        args.multi_select_cursor_style = None
    if args.multi_select_keys != "":
        args.multi_select_keys = tuple(args.multi_select_keys.split(","))
    else:
        args.multi_select_keys = None
    if args.search_key.lower() == "none":
        args.search_key = None
    if args.show_shortcut_hints_in_status_bar:
        args.show_shortcut_hints = True
    if args.multi_select:
        args.stdout = True
    if args.preselected_entries is not None:
        args.preselected = list(args.preselected_entries.split(","))
    elif args.preselected_indices is not None:
        args.preselected = list(map(int, args.preselected_indices.split(",")))
    else:
        args.preselected = None
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
            clear_menu_on_exit=args.clear_menu_on_exit,
            clear_screen=args.clear_screen,
            cursor_index=args.cursor_index,
            cycle_cursor=args.cycle,
            exit_on_shortcut=args.exit_on_shortcut,
            menu_cursor=args.cursor,
            menu_cursor_style=args.cursor_style,
            menu_highlight_style=args.highlight_style,
            multi_select=args.multi_select,
            multi_select_cursor=args.multi_select_cursor,
            multi_select_cursor_brackets_style=args.multi_select_cursor_brackets_style,
            multi_select_cursor_style=args.multi_select_cursor_style,
            multi_select_empty_ok=args.multi_select_empty_ok,
            multi_select_keys=args.multi_select_keys,
            multi_select_select_on_accept=args.multi_select_select_on_accept,
            preselected_entries=args.preselected,
            preview_border=args.preview_border,
            preview_command=args.preview_command,
            preview_size=args.preview_size,
            preview_title=args.preview_title,
            search_case_sensitive=args.case_sensitive,
            search_highlight_style=args.search_highlight_style,
            search_key=args.search_key,
            shortcut_brackets_highlight_style=args.shortcut_brackets_highlight_style,
            shortcut_key_highlight_style=args.shortcut_key_highlight_style,
            show_multi_select_hint=args.show_multi_select_hint,
            show_multi_select_hint_text=args.show_multi_select_hint_text,
            show_search_hint=args.show_search_hint,
            show_search_hint_text=args.show_search_hint_text,
            show_shortcut_hints=args.show_shortcut_hints,
            show_shortcut_hints_in_status_bar=args.show_shortcut_hints_in_status_bar,
            status_bar=args.status_bar,
            status_bar_below_preview=args.status_bar_below_preview,
            status_bar_style=args.status_bar_style,
            title=args.title,
        )
    except (InvalidParameterCombinationError, InvalidStyleError, UnknownMenuEntryError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(0)
    chosen_entries = terminal_menu.show()
    if chosen_entries is None:
        sys.exit(0)
    else:
        if isinstance(chosen_entries, Iterable):
            if args.stdout:
                print(",".join(str(entry + 1) for entry in chosen_entries))
            sys.exit(chosen_entries[0] + 1)
        else:
            chosen_entry = chosen_entries
            if args.stdout:
                print(chosen_entry + 1)
            sys.exit(chosen_entry + 1)


if __name__ == "__main__":
    main()
