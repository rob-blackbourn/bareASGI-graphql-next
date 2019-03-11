from typing import Tuple, Mapping, MutableMapping, Iterator


def _parseparam(s: bytes) -> Iterator[bytes]:
    while s[:1] == b';':
        s = s[1:]
        end = s.find(b';')
        while end > 0 and (s.count(b'"', 0, end) - s.count(b'\\"', 0, end)) % 2:
            end = s.find(b';', end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        yield f.strip()
        s = s[end:]


def parse_header(line: bytes) -> Tuple[bytes, Mapping[bytes, bytes]]:
    """Parse a Content-type like header.

    Return the main content-type and a dictionary of options.

    """
    parts = _parseparam(b';' + line)
    key = parts.__next__()
    params: MutableMapping[bytes, bytes] = {}
    for p in parts:
        i = p.find(b'=')
        if i >= 0:
            name = p[:i].strip().lower()
            value = p[i + 1:].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
                value = value.replace(b'\\\\', b'\\').replace(b'\\"', b'"')
            params[name] = value
    return key, params
