__author__ = 'Dmitriy Korsakov'


def _test_crud(runner):
    print runner.invoke("roles", "list")

