__author__ = 'Dmitriy Korsakov'
__doc__ = 'Cost Centrer management'


from scalrctl import commands


name = "cost-center"
enabled = True


def callback(*args, **kwargs):
    """
    print('in cost-center module')
    print(args)
    print(kwargs)
    """
    pass


class CostCenterList(commands.SubCommand):
    name = "list"
    route = "/{envId}/cost-centers/"
    method = "get"
    enabled = True


class CostCenterRetrieve(commands.SubCommand):
    name = "retrieve"
    route = "/{envId}/cost-centers/{costCenterId}/"
    method = "get"
    enabled = True
