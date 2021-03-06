"""
Common functions for the bak_to_*.py modules.
"""

from datetime import datetime
from typing import List


def ask_to_continue(prompt, choices):
    assert 0 < len(choices)
    assert all([x == x.lower() for x in choices])
    while True:
        answer = input(prompt).lower()
        if answer in choices:
            break
        print("Please select from the list of valid choices.")
    return answer


def datetime_fromisoformat(dts):
    """
    Take an ISO format datetime string and return a datetime type.
    The datetime.fromisoformat method was new in Python 3.7. This replacement
    works on 3.6.9, which the author is still has on some machines.
    It may work on older versions, but that is not the target.
    """
    #  ISO format: yyyy-mm-ddThh:nn:ss
    #              0....:....1....:....2
    try:
        assert len(dts) == 19
        y = int(dts[0:4])
        assert dts[4] == "-"
        m = int(dts[5:7])
        assert dts[7] == "-"
        d = int(dts[8:10])
        h = int(dts[11:13])
        assert dts[13] == ":"
        n = int(dts[14:16])
        assert dts[16] == ":"
        s = int(dts[17:19])
        dt = datetime(y, m, d, h, n, s)
    except Exception:
        raise ValueError(f"Invalid date string: '{dts}'")
    return dt


def log_fmt(a_list):
    s = ""
    for item in a_list:
        if " " in item:
            s += f'"{item}" '
        else:
            s += f"{item} "
    return s.strip()


def plain_quotes(text):
    """
    There may be a setting in Libre Office Calc, which I'm using to edit the
    CSV file, that will stop it from using the fancy left and right quotes
    (so this is probably dumb). Nonetheless, this function replaces left and
    right, single and double quotes, with apostrophe and quotation mark
    respectively.
    """
    #  https://en.wikipedia.org/wiki/Quotation_mark#Unicode_code_point_table

    s = ""
    for a in text:
        if ord(a) in [8216, 8217]:
            a = "'"
        elif ord(a) in [8220, 8221]:
            a = '"'
        s += a
    return s


def split_quoted(text: str) -> List[str]:
    """
    Split a string into a list of words, but keep words inside double quotes
    as a single list item (with the quotes removed).  Handles right and left
    quote characters as saved by LibreOffice Calc.
    Does not handle nested quotes.
    """

    #  There are multiple double quote characters with different
    #  ordinal values:
    #    Quotation Mark is 34 (0x0022).
    #    Apostrophe (single quote) is 39 (0x0027).
    #    Left Double Quotation Mark is 8220 (0x201c).
    #    Right Double Quotation Mark is 8221 (0x201d).

    #  Use for grouping the first type of quotation mark found.
    marks_double = [34, 8220, 8221]
    marks_single = [39]
    marks = None

    s = text.strip()
    result = []
    t = ""
    for a in s:
        if ord(a) in marks_double:
            marks = marks_double
            break
        elif ord(a) in marks_single:
            marks = marks_single
            break

    if marks is None:
        #  No quotation marks, so do default split().
        return s.split()

    in_quote = False
    for a in s:
        if ord(a) in marks:
            in_quote = not in_quote
        elif a == " ":
            if in_quote:
                t += a
            else:
                result.append(t)
                t = ""
        else:
            t += a
    if 0 < len(t):
        result.append(t)
    return result


def strip_outer_quotes(text: str) -> str:
    s = text.strip()
    if len(s) == 0:
        return s
    if s[0] == '"':
        return s.strip('"')
    if s[0] == "'":
        return s.strip("'")
    return s
