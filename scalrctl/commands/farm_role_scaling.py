__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage FarmRole Scaling'


from scalrctl import commands


class DeleteFarmRoleScaling(commands.Action):
    delete_target = 'metricName'