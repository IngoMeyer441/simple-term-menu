# Simple Terminal Menu

## Overview

`simple-term-menu` creates simple menus for interactive command line programs. It can be used to offer a choice of
different options to the user. Menu entries can be selected with the arrow or j/k keys. The module uses the terminfo
database to detect terminal features automatically and disables styles that are not available.
Currently, Linux and macOS are supported.

## Installation

`simple-term-menu` is available on PyPI for Python 3.5+ and can be installed with `pip`:

```bash
python3 -m pip install simple-term-menu
```

If you use Arch Linux or one of its derivatives, you can also install `simple-term-menu` from the
[AUR](https://aur.archlinux.org/packages/python-simple-term-menu/):

```bash
yay -S python-simple-term-menu
```

You also find self-contained executables for 64-bit Linux distributions and macOS High Sierra and newer on the
[releases page](https://github.com/IngoMeyer441/simple-term-menu/releases/latest). They are created with
[PyInstaller](http://www.pyinstaller.org) and only require glibc >= 2.17 on Linux (should be fine on any recent
Linux system).

## Usage

### Create a menu with the default style

Create an instance of the class `TerminalMenu` and pass the menu entries as a list of strings to the constructor. Call
the `show` method to output the menu and wait for keyboard input:

```python
#!/usr/bin/env python3

from simple_term_menu import TerminalMenu


def main():
    terminal_menu = TerminalMenu(["entry 1", "entry 2", "entry 3"])
    menu_entry_index = terminal_menu.show()


if __name__ == "__main__":
    main()
```

You will get an output like:

![screenshot_basic](https://raw.githubusercontent.com/IngoMeyer441/simple-term-menu/master/basic.png)

You can now select a menu entry with the arrow keys or `j`/`k` (vim motions) and accept your choice by hitting enter or
cancel the menu with escape, `q` or `<Ctrl>-C`. `show` returns the selected menu entry index or `None` if the menu was
canceled.

You can pass an optional `title` to the `TerminalMenu` constructor which will be placed above the menu. `title` can be a
simple string, a multiline string (with `\n` newlines) or a list of strings.

### Styling

You can pass styling arguments to the `TerminalMenu` constructor. Each style is a tuple of keyword strings. Currently
the following keywords are accepted:

- `bg_black`
- `bg_blue`
- `bg_cyan`
- `bg_gray`
- `bg_green`
- `bg_purple`
- `bg_red`
- `bg_yellow`
- `fg_black`
- `fg_blue`
- `fg_cyan`
- `fg_gray`
- `fg_green`
- `fg_purple`
- `fg_red`
- `fg_yellow`
- `bold`
- `italics`
- `standout`
- `underline`

You can alter the following styles:

- `menu_cursor_style`: The style of the shown cursor. The default style is `("fg_red", "bold")`.

- `menu_highlight_style`: The style of the selected menu entry. The default style is `("standout",)`.

- `search_highlight_style`: The style of matched search strings. The default style is `("fg_black", "bg_yellow",
  "bold")`.

- `shortcut_key_highlight_style`: The style of shortcut keys. The default style is `("fg_blue",)`.

- `shortcut_parentheses_highlight_style`: The style of parentheses enclosing shortcut keys. The default style is
  `("fg_gray",)`.

By setting `menu_cursor` you can define another cursor or disable it (`None`). The default cursor is `"> "`.

### Searching

`simple_term_menu` has a built-in search feature to filter shown menu entries. The default key to activate search mode
is `/` (like in Vim, less and other terminal programs). If you prefer another search key, pass a `search_key` parameter
to the `TerminalMenu` constructor. `None` can be passed to activate the search on every letter key. Obviously, `j` and
`k` cannot be used for cursor motions in that mode. Use `<Ctrl-j>` and `<Ctrl-k>` instead.

The search mode supports Python regex syntax. Visit the
[Python re documentation](https://docs.python.org/3/library/re.html#regular-expression-syntax) for more details.

String parts of the menu entries which match the given search pattern are highlighted. Use the `search_highlight_style`
parameter to adjust the highlight style to your liking.

By default, the search is case insensitive. Set `search_case_sensitive` to `True` if you prefer a case sensitive search
line.

Pass `show_search_hint=True` to the `TerminalMenu` constructor to activate a search hint in the search line (like
`(Press "/" to search)`).

### Shortcuts

You can define shortcuts for selected menu entries by prepending a single character enclosed in square brackets (like
`[a]`). Pass `shortcut_key_highlight_style` and/or `shortcut_parentheses_highlight_style` to the `TerminalMenu`
constructor to change the default highlight style of the shortcuts.

By default, the `show` method returns when a shortcut key is pressed. If you only want the selection to jump the
shortcut target, pass `exit_on_shortcut=False` to the `TerminalMenu` constructor.

If you configured the search to be activated on every letter key, the shortcut feature will be disabled.

Pass `show_shortcut_hints=True` to the `TerminalMenu` constructor to display shortcut hints in the menu title (useful
for very long menus which need scrolling).

#### Shortcuts example

Create a menu of some fruits and use the first letter as shortcut key:

```python
#!/usr/bin/env python3

import os
from simple_term_menu import TerminalMenu


def main():
    fruits = ["[a] apple", "[b] banana", "[o] orange"]
    terminal_menu = TerminalMenu(fruits, title="Fruits")
    menu_entry_index = terminal_menu.show()


if __name__ == "__main__":
    main()
```

![screenshot_shortcuts](https://raw.githubusercontent.com/IngoMeyer441/simple-term-menu/master/shortcuts.png)

### Custom accept keys

The default key to accept a menu item is `enter`. Pass the `accept_keys` parameter with a tuple of keys (as strings) to
the `TerminalMenu` constructor to use a different set of accept keys. Custom accept keys can be plain ascii letters or
ascii letters with a modifier key (prepend `ctrl-` or `alt-` to an ascii letter). Use the `chosen_accept_key` property
of the `TerminalMenu` instance to query which accept key was pressed by the user.

Be aware that not all combinations of modifier and ascii keys will work depending on your terminal emulator and
graphical user interface. In addition, some combinations generate other existing keys (e.g. `ctrl-m` is `enter` /
carriage return).

#### Custom accept keys example

```python
#!/usr/bin/env python3

import os
from simple_term_menu import TerminalMenu


def main():
    terminal_menu = TerminalMenu(["entry 1", "entry 2", "entry 3"], accept_keys=("enter", "alt-d", "ctrl-i"))
    menu_entry_index = terminal_menu.show()
    print(terminal_menu.chosen_accept_key)


if __name__ == "__main__":
    main()
```


### Preview window

`simple-term-menu` can show a preview for each menu entry. Pass a `preview_command` to the `TerminalMenu` constructor to
activate this optional feature. `preview_command` either takes a command string which will be executed as a subprocess
or a Python callable which converts a given menu entry string into the preview output. If a command string is given, the
pattern `{}` is replaced with the current menu entry string. If a menu entry has an additional data component (separated
by `|`), it is passed instead to the preview command. `\|` can be used for a literal `|`. If you simply append a `|`
(without a data component), the preview window will be disabled for this entry.

The additional keyword argument `preview_size` can be used to control the height of the preview window. It is given as
fraction of the complete terminal height (default: `0.25`). The width cannot be set, it is always the complete width of
the terminal window.

Preview commands are allowed to generate [ANSI escape color codes](https://en.wikipedia.org/wiki/ANSI_escape_code#SGR).

#### Preview examples

- Create a menu for all files in the current directory and preview their contents with the
  [`bat`](https://github.com/sharkdp/bat) command:

  ```python
  #!/usr/bin/env python3

  import os
  from simple_term_menu import TerminalMenu


  def list_files(directory="."):
      return (file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file)))


  def main():
      terminal_menu = TerminalMenu(list_files(), preview_command="bat --color=always {}", preview_size=0.75)
      menu_entry_index = terminal_menu.show()


  if __name__ == "__main__":
      main()
  ```

  ![screenshot_preview_bat](https://raw.githubusercontent.com/IngoMeyer441/simple-term-menu/master/preview_bat.png)

- Another file preview example using the [Pygments](https://pygments.org) api:

  ```python
  #!/usr/bin/env python3

  import os
  from pygments import formatters, highlight, lexers
  from pygments.util import ClassNotFound
  from simple_term_menu import TerminalMenu


  def highlight_file(filepath):
      with open(filepath, "r") as f:
          file_content = f.read()
      try:
          lexer = lexers.get_lexer_for_filename(filepath, stripnl=False, stripall=False)
      except ClassNotFound:
          lexer = lexers.get_lexer_by_name("text", stripnl=False, stripall=False)
      formatter = formatters.TerminalFormatter(bg="dark")  # dark or light
      highlighted_file_content = highlight(file_content, lexer, formatter)
      return highlighted_file_content


  def list_files(directory="."):
      return (file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file)))


  def main():
      terminal_menu = TerminalMenu(list_files(), preview_command=highlight_file, preview_size=0.75)
      menu_entry_index = terminal_menu.show()


  if __name__ == "__main__":
      main()
  ```

  ![screenshot_preview_pygments](https://raw.githubusercontent.com/IngoMeyer441/simple-term-menu/master/preview_pygments.png)

- Preview the active pane of each running tmux session (the session ids are appended to the menu entries with the `|`
  separator):

  ```python
  #!/usr/bin/env python3

  import subprocess
  from simple_term_menu import TerminalMenu


  def list_tmux_sessions():
      tmux_command_output = subprocess.check_output(
          ["tmux", "list-sessions", "-F#{session_id}:#{session_name}"], universal_newlines=True
      )
      tmux_sessions = []
      for line in tmux_command_output.split("\n"):
          line = line.strip()
          if not line:
              continue
          session_id, session_name = tuple(line.split(":"))
          tmux_sessions.append((session_name, session_id))
      return tmux_sessions


  def main():
      terminal_menu = TerminalMenu(
          ("|".join(session) for session in list_tmux_sessions()),
          preview_command="tmux capture-pane -e -p -t {}",
          preview_size=0.75,
      )
      menu_entry_index = terminal_menu.show()


  if __name__ == "__main__":
      main()
  ```

  ![screenshot_preview_tmux_sessions](https://raw.githubusercontent.com/IngoMeyer441/simple-term-menu/master/preview_tmux_sessions.png)

### Additional settings

Furthermore, the `TerminalMenu` constructor takes these additional parameters to change the menu behavior:

- `cycle_cursor`: A bool value which indicates if the menu cursor cycles when the end of the menu is reached. Defaults
  to `True`.
- `clear_screen`: A bool value which indicates if the screen will be cleared before the menu is shown. Defaults to
  `False`.
- `clear_menu_on_exit`: A bool value which indicates if the menu will be cleared after the `show` method. Defaults to
  `True`.
- `cursor_index`: The initially selected item index.

### Command line program

`simple-term-menu` can be used as a terminal program in shell scripts. The exit code of the script is the 1-based index
of the selected menu entry. The exit code 0 reports the cancel action. The following command line arguments are
supported:

```
usage: simple-term-menu [-h] [-t TITLE] [-c CURSOR] [-s CURSOR_STYLE]
                        [-m HIGHLIGHT_STYLE] [-n SEARCH_HIGHLIGHT_STYLE]
                        [-o SHORTCUT_KEY_HIGHLIGHT_STYLE]
                        [-q SHORTCUT_PARENTHESES_HIGHLIGHT_STYLE] [-C]
                        [-i CURSOR_INDEX] [-l] [-X] [-p PREVIEW_COMMAND]
                        [--preview-size PREVIEW_SIZE] [-k SEARCH_KEY] [-a]
                        [-E] [-u] [-v] [-V]
                        [entries [entries ...]]

simple-term-menu creates simple interactive menus in the terminal and returns the selected entry as exit code.

positional arguments:
  entries               the menu entries to show

optional arguments:
  -h, --help            show this help message and exit
  -t TITLE, --title TITLE
                        menu title
  -c CURSOR, --cursor CURSOR
                        menu cursor (default: > )
  -s CURSOR_STYLE, --cursor_style CURSOR_STYLE
                        style for the menu cursor as comma separated list
                        (default: fg_red,bold)
  -m HIGHLIGHT_STYLE, --highlight_style HIGHLIGHT_STYLE
                        style for the selected menu entry as comma separated
                        list (default: standout)
  -n SEARCH_HIGHLIGHT_STYLE, --search_highlight_style SEARCH_HIGHLIGHT_STYLE
                        style of matched search patterns (default:
                        fg_black,bg_yellow,bold)
  -o SHORTCUT_KEY_HIGHLIGHT_STYLE, --shortcut_key_highlight_style SHORTCUT_KEY_HIGHLIGHT_STYLE
                        style of shortcut keys (default: fg_blue)
  -q SHORTCUT_PARENTHESES_HIGHLIGHT_STYLE, --shortcut_parentheses_highlight_style SHORTCUT_PARENTHESES_HIGHLIGHT_STYLE
                        style of parentheses enclosing shortcut keys (default:
                        fg_gray)
  -C, --no-cycle        do not cycle the menu selection
  -i CURSOR_INDEX, --cursor-index CURSOR_INDEX
                        initially selected item index
  -l, --clear-screen    clear the screen before the menu is shown
  -X, --no-clear-menu-on-exit
                        do not clear the menu on exit
  -p PREVIEW_COMMAND, --preview PREVIEW_COMMAND
                        Command to generate a preview for the selected menu
                        entry. "{}" can be used as placeholder for the menu
                        text. If the menu entry has a data component
                        (separated by "|"), this is used instead.
  --preview-size PREVIEW_SIZE
                        maximum height of the preview window in fractions of
                        the terminal height (default: 0.25)
  -k SEARCH_KEY, --search_key SEARCH_KEY
                        key to start a search (default: "/", "none" is treated
                        a special value which activates the search on any
                        letter key)
  -a, --case_sensitive  searches are case sensitive
  -E, --no-exit-on-shortcut
                        do not exit on shortcut keys
  -u, --show-search_hint
                        show a search hint in the search line
  -v, --show-shortcut_hints
                        show shortcut hints in the menu title
  -V, --version         print the version number and exit
```

#### Example with preview option

Instead of using the Python api as in the [previous examples](#preview-examples), a file menu with `bat` preview can
also be created from the command line:

```bash
simple-term-menu -p "bat --color=always {}" \
                 --preview-size 0.75 \
                 $(find . -maxdepth 1  -type f | awk '{ print substr($0, 3) }')
```

### More advanced example

A more advanced example with sub menus (thanks to [pageauc](https://github.com/pageauc)):

```python
#!/usr/bin/env python3
"""
Demonstration example for GitHub Project at
https://github.com/IngoMeyer441/simple-term-menu

This code only works in python3. Install per

    sudo pip3 install simple-term-menu

"""
import time
from simple_term_menu import TerminalMenu


def main():
    main_menu_title = "  Main Menu\n"
    main_menu_items = ["Edit Menu", "Second Item", "Third Item", "Quit"]
    main_menu_cursor = "> "
    main_menu_cursor_style = ("fg_red", "bold")
    main_menu_style = ("bg_red", "fg_yellow")
    main_menu_exit = False

    main_menu = TerminalMenu(menu_entries=main_menu_items,
                             title=main_menu_title,
                             menu_cursor=main_menu_cursor,
                             menu_cursor_style=main_menu_cursor_style,
                             menu_highlight_style=main_menu_style,
                             cycle_cursor=True,
                             clear_screen=True)

    edit_menu_title = "  Edit Menu\n"
    edit_menu_items = ["Edit Config", "Save Settings", "Back to Main Menu"]
    edit_menu_back = False
    edit_menu = TerminalMenu(edit_menu_items,
                             edit_menu_title,
                             main_menu_cursor,
                             main_menu_cursor_style,
                             main_menu_style,
                             cycle_cursor=True,
                             clear_screen=True)

    while not main_menu_exit:
        main_sel = main_menu.show()

        if main_sel == 0:
            while not edit_menu_back:
                edit_sel = edit_menu.show()
                if edit_sel == 0:
                    print("Edit Config Selected")
                    time.sleep(5)
                elif edit_sel == 1:
                    print("Save Selected")
                    time.sleep(5)
                elif edit_sel == 2:
                    edit_menu_back = True
                    print("Back Selected")
            edit_menu_back = False
        elif main_sel == 1:
            print("option 2 selected")
            time.sleep(5)
        elif main_sel == 2:
            print("option 3 selected")
            time.sleep(5)
        elif main_sel == 3:
            main_menu_exit = True
            print("Quit Selected")


if __name__ == "__main__":
    main()
```

## Similar projects

- [`bullet`](https://github.com/Mckinsey666/bullet): Creates bullet-lists with multi-selection support.
