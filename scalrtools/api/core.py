__author__ = 'Dmytro Korsakov'


def xml_to_dict(root, row_xpath, columns, upper_level, dynamic_attrs=None):
    '''
    schema = None #JSON
    columns = schema['descr']
    row_xpath = schema['row_xpath']
    format = schema['format']
    upper_level = schema['upper_level']
    '''
    data = dict()
    rows = []

    for row in root.findall(row_xpath):
        d = dict()

        for attr in columns:
            obj = row.find(attr)
            if hasattr(obj,'text') and obj.text is not None:
                d[attr] = obj.text.strip()
            else:
                d[attr] = None

        if dynamic_attrs:
            for dattr in dynamic_attrs:
                objects = row.findall(dattr)
                d[dattr] = [(object.tag, object.text.strip()) for object in objects]

        rows.append(d)

    data['upper_level'] = dict()
    for path in upper_level:
        data['upper_level'][path] = root.find(path).text.strip()

    data['table'] = rows
    return data
