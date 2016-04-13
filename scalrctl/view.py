__author__ = 'Dmitriy Korsakov'

import json
import yaml
import prettytable
import settings


def build_table(field_names, rows, pre=None, post=None):
    table = prettytable.PrettyTable()
    table.align = "l"
    table.right_padding_width = 4
    table.left_padding_width = 1
    table.set_style(prettytable.PLAIN_COLUMNS)

    template = '\x1b[1m%s\x1b[0m' if settings.colored_output else "%s"
    table.field_names = [template % field.upper().replace("_", " ") for field in field_names]

    for row in rows:
        table.add_row(row)

    body = table.get_string()

    if pre:
        body = "%s\n\n%s" % (pre, body)
    if post:
        body = "%s\n\n%s" % (body, post)

    return "\n%s\n" % body


def build_tree(data):
    if isinstance(data, str):
        data = json.loads(data)

    yaml_text = yaml.safe_dump(data, encoding='utf-8', allow_unicode=True, default_flow_style=False)

    # yaml_text = yaml_text.decode('unicode_escape').encode('ascii','ignore')  # [ST-63]
    yaml_text = yaml_text.decode("ascii", "ignore").encode("ascii")  # [ST-63]

    if not settings.colored_output:
        return yaml_text

    pairs = []
    in_key = False

    for token in yaml.scan(yaml_text):
        if token.__class__ == yaml.tokens.KeyToken:
            in_key = True
            continue
        if in_key and yaml.tokens.ScalarToken == token.__class__:
            pairs.append((token.start_mark.index, token.end_mark.index))
            in_key = False

    if not pairs:
        return yaml_text

    last_pos = pairs[0][0]
    result = yaml_text[:last_pos]

    for start, end in pairs:
        result += yaml_text[last_pos:start] + "\x1b[31;1m" + yaml_text[start:end] + "\x1b[0m"
        last_pos = end

    result += yaml_text[last_pos:]

    return result
