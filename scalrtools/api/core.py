__author__ = 'Dmytro Korsakov'


def xml_to_dict(root, row_path, attributes, format='base', dynamic_attrs=None):
    '''
    schema = None #JSON
    attributes = schema['descr']
    row_path = schema['row_path']
    format = schema['format']
    '''
    upper_level = ['TransactionID',]
    data = dict()
    rows = []

    if format in ('base', 'paged'):
        for row in root.findall(row_path):
            d = dict()

            for attr in attributes:
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

    if format == 'paged':
        upper_level += ('TotalRecords', 'StartFrom', 'RecordsLimit')

    data['upper_level'] = dict()
    for path in upper_level:
        data['upper_level'][path] = root.find(path).text.strip()

    data['table'] = rows
    return data
