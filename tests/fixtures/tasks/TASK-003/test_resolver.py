from resolver import URLPattern, URLResolver

def view_home():
    return "home"

def view_item(item_id: int):
    return f"item_{item_id}"

def test_resolve_root():
    patterns = [URLPattern("/", view_home, name="home")]
    r = URLResolver(patterns)
    res = r.resolve("/")
    assert res is not None
    cb, kwargs = res
    assert cb() == "home"
    assert kwargs == {}

def test_resolve_int_param():
    patterns = [URLPattern("/items/<int:item_id>/", view_item, name="item")]
    r = URLResolver(patterns)
    res = r.resolve("/items/42/")
    assert res is not None
    cb, kwargs = res
    assert kwargs == {"item_id": 42}
    assert cb(**kwargs) == "item_42"

def test_resolve_not_found():
    patterns = [URLPattern("/home/", view_home)]
    r = URLResolver(patterns)
    assert r.resolve("/missing/") is None
