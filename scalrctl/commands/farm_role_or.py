__author__ = 'Dmitriy Korsakov'
__doc__ = 'Orchestration Rule management'


from scalrctl import commands


name = "farm-role-orchestration-rule"
enabled = True


def callback(*args, **kwargs):
    """
    print('in farm-role-orchestration-rule module')
    print(args)
    print(kwargs)
    """
    pass


class OrchestrationRule(commands.SubCommand):
    pass


class ListOrchestrationRules(OrchestrationRule):
    name = "list"
    route = "/{envId}/farm-roles/{farmRoleId}/orchestration-rules/"
    method = "get"
    enabled = True


class RetrieveOrchestrationRule(OrchestrationRule):
    name = "retrieve"
    route = "/{envId}/farm-roles/{farmRoleId}/orchestration-rules/{orchestrationRuleId}/"
    method = "get"
    enabled = True


class CreateOrchestrationRule(OrchestrationRule):
    name = "create"
    route = "/{envId}/farm-roles/{farmRoleId}/orchestration-rules/"
    method = "post"
    enabled = True


class ChangeOrchestrationRuleAttrs(OrchestrationRule):
    name = "change-attributes"
    route = "/{envId}/farm-roles/{farmRoleId}/orchestration-rules/{orchestrationRuleId}/"
    method = "patch"
    enabled = True


class DeleteOrchestrationRule(OrchestrationRule):
    name = "delete"
    route = "/{envId}/farm-roles/{farmRoleId}/orchestration-rules/{orchestrationRuleId}/"
    method = "delete"
    enabled = True
