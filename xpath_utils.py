def xpath_repr(string):
    string_with_escaped_quotes = string.replace('"', '\\"')
    return f'"{string_with_escaped_quotes}"'
