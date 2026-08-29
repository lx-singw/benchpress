from parser import parse_regex_tokens

def test_parse_simple():
    tokens = parse_regex_tokens("abc")
    assert tokens == ["a", "b", "c"]

def test_parse_escaped():
    tokens = parse_regex_tokens(r"a\d+b")
    assert tokens == ["a", r"\d", "+", "b"]

def test_parse_brackets():
    tokens = parse_regex_tokens("[a-z]*")
    assert tokens == ["[", "a", "-", "z", "]", "*"]
