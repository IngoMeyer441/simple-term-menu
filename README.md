# Simple Terminal Menu

## Overview

`simple-term-menu` creates simple menus for interactive command line programs. It can be used to offer a choice of
different options to the user. Menu entries can be selected with the arrow or j/k keys. The module uses the terminfo
database to detect terminal features automatically and disables styles that are not available.
Currently, Linux and macOS are supported.

## Installation

`simple-term-menu` is available on PyPI for Python 3.3+ and can be installed with `pip`:

```bash
python3 -m pip install simple-term-menu
```

If you use Arch Linux or one of its derivatives, you can also install `simple-term-menu` from the
[AUR](https://aur.archlinux.org/packages/python-simple-term-menu/):

```bash
yay -S python-simple-term-menu
```

## Usage

### Create a menu with the default style

Create an instance of the class `TerminalMenu` and pass the menu entries as a list of strings to the constructor. Call
the `show` method to output the menu and wait for keyboard input:

```python
#!/usr/bin/env python3

from simple_term_menu import TerminalMenu


def main():
    terminal_menu = TerminalMenu(["entry 1", "entry 2", "entry 3"])
    terminal_menu.show()


if __name__ == "__main__":
    main()
```

You will get an output like:

![screenshot_basic](https://raw.githubusercontent.com/IngoHeimbach/simple-term-menu/master/basic.png)

You can now select a menu entry with the arrow keys or `j`/`k` (vim motions) and accept your choice by hitting enter or
cancel the menu with escape, `q` or `<Ctrl>-C`. `show` returns the selected menu entry index or `None` if the menu was
canceled.

You can pass an optional `title` to the `TerminalMenu` constructor which will be placed above the menu.

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

- `menu_highlight_style`: The style of the selected menu entry. The default style is `("standout",)`

By setting `menu_cursor` you can define another cursor or disable it (`None`). The default cursor is `"> "`.

### Command line program

`simple-term-menu` can be used as a terminal program in shell scripts. The exit code of the script is the 1-based index
of the selected menu entry. The exit code 0 reports the cancel action. The following command line arguments are
supported:

```
usage: simple-term-menu [-h] [-c CURSOR] [-s CURSOR_STYLE]
                        [-m HIGHLIGHT_STYLE] [-C] [-V]
                        entries [entries ...]

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
  -C, --no-cycle        do not cycle the menu selection
  -V, --version         print the version number and exit
```

### More advanced example

A more advanced example with sub menus (thanks to [pageauc](https://github.com/pageauc)):

```python
#!/usr/bin/env python3
'''
Demonstration example for GitHub Project at
https://github.com/IngoHeimbach/simple-term-menu

This code only works in python3. Install per

    sudo pip3 install simple-term-menu

'''
import time
import os
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
                             cycle_cursor=True)

    edit_menu_title = "  Edit Menu\n"
    edit_menu_items = ["Edit Config", "Save Settings", "Back to Main Menu"]
    edit_menu_back = False
    edit_menu = TerminalMenu(edit_menu_items,
                             edit_menu_title,
                             main_menu_cursor,
                             main_menu_cursor_style,
                             main_menu_style)

    while not main_menu_exit:
        os.system('clear')
        main_sel = main_menu.show()

        if main_sel == 0:
            while not edit_menu_back:
                os.system('clear')
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
