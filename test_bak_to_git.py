
from bak_to_git_3 import split_quoted


def test_split_quoted():
    #  Text with no quotes should be split on spaces.
    s = "a b c  d"
    assert ['a', 'b', 'c', 'd'] == split_quoted(s)

    #  Text in double-quotes should be grouped, including any
    #  single-quoted text inside.
    s = "a \"b 'c d'\""
    assert ["a", "b 'c d'"] == split_quoted(s)

    #  Text in single-quotes should be grouped, including any
    #  double-quoted text inside.
    s = "a 'b \"c d\"'"
    assert ['a', 'b "c d"'] == split_quoted(s)
