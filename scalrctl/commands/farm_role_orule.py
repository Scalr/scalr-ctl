__author__ = 'Dmitriy Korsakov'
__doc__ = 'Manage orchestration rules for farm roles'


from scalrctl import commands


class DeleteFarmRoleOrchestrationRule(commands.Action):
    delete_target = 'orchestrationRuleId'