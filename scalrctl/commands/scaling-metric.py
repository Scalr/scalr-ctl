__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage scaling metrics'

from scalrctl import commands


name = "scaling-metric"
enabled = True


def callback(*args, **kwargs):
    """
    print('in scaling_metric module')
    print(args)
    print(kwargs)
    """
    pass


class ScalingMetric(commands.SubCommand):
    enabled = True


class ScalingMetricList(ScalingMetric):
    name = "list"
    route = "/{envId}/scaling-metrics/"
    method = "get"


class ScalingMetricCreate(ScalingMetric):
    name = "create"
    route = "/{envId}/scaling-metrics/"
    method = "post"


class ScalingMetricRetrieve(ScalingMetric):
    name = "retrieve"
    route = "/{envId}/scaling-metrics/{metricName}/"
    method = "get"


class ScalingMetricDelete(ScalingMetric):
    name = "delete"
    route = "/{envId}/scaling-metrics/{metricName}/"
    method = "delete"


class ScalingMetricUpdate(ScalingMetric):
    name = "update"
    route = "/{envId}/scaling-metrics/{metricName}/"
    method = "patch"
