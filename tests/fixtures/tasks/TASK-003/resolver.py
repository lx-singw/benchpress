import re
from typing import Dict, Any, Optional, Callable

class URLPattern:
    def __init__(self, pattern: str, callback: Callable, name: Optional[str] = None):
        self.pattern = pattern
        self.regex = re.compile("^" + re.sub(r"<int:(\w+)>", r"(?P<\1>\\d+)", pattern) + "$")
        self.callback = callback
        self.name = name

    def match(self, path: str) -> Optional[Dict[str, Any]]:
        m = self.regex.match(path)
        if not m:
            return None
        kwargs = m.groupdict()
        # Convert integer groups
        for k, v in kwargs.items():
            if v.isdigit():
                kwargs[k] = int(v)
        return kwargs

class URLResolver:
    def __init__(self, patterns: list[URLPattern]):
        self.patterns = patterns

    def resolve(self, path: str) -> Optional[tuple[Callable, Dict[str, Any]]]:
        for p in self.patterns:
            kwargs = p.match(path)
            if kwargs is not None:
                return (p.callback, kwargs)
        return None
