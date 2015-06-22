__author__ = 'Dmitriy Korsakov'

from scalrtools import settings, spec


specs_dict = {}
count = 0
for path in settings.spec["paths"].keys():
    methods = settings.spec["paths"][path].keys()
    for method in methods:
        if "parameters" != method:
            if method not in specs_dict:
                specs_dict[method] = []
            s = spec.Spec(settings.spec, path, method)
            specs_dict[method].append(s)
            count += 1
print "Total methods available in yaml spec:", count

all_specs = specs_dict["get"]+specs_dict["post"]+specs_dict["delete"]+specs_dict["patch"]
post_spec = spec.Spec(settings.spec, "/{envId}/images/{imageId}/", "patch")
get_spec = spec.Spec(settings.spec, "/{envId}/images/{imageId}/", "get")
list_spec = spec.Spec(settings.spec, "/{envId}/images/", "get")


def test_description():
    assert 'Change image attributes. Only the name be can changed!' ==  post_spec.description
    assert 'Retrieve an Image.' == get_spec.description

    """
    empty = []
    for s in all_specs:
        if not s.description:
            empty.append(s)
        else:
            print s.route, s.method, s.description

    for e in empty:
        print e.route, e.method
    """


def test_method_params():
    assert 1 == len(post_spec.method_params)
    assert 5 == len(post_spec.method_params[0])
    assert 'The updated definition' == post_spec.method_params[0]['description']
    assert [] == get_spec.method_params


def test_route_params():
    assert 2 == len(post_spec.route_params)
    assert 2 == len(get_spec.route_params)


def test_returns_iterable():
    assert not post_spec.returns_iterable()
    assert not get_spec.returns_iterable()
    assert list_spec.returns_iterable()

def test_filters():
    assert 11 == len(list_spec.filters)
    assert "id" in list_spec.filters
    assert not get_spec.filters
    assert not post_spec.filters

