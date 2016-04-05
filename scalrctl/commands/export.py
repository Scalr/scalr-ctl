__author__ = 'Dmitriy Korsakov'
__doc__ = 'Export Scalr Objects'

import json
import datetime

from scalrctl import settings
from scalrctl import commands
from scalrctl import click

import yaml

NAME = "export"
enabled = True


def callback(*args, **kwargs):
    """
    print('in export module')
    print(args)
    print(kwargs)
    """
    pass


class Export(commands.SubCommand):
    enabled = True
    method = "get"

    def run(self, *args, **kwargs):
        kv = kwargs.copy()
        kv['hide_output'] = True
        response = super(Export, self).run(*args, **kv)

        kwargs["envId"] = settings.envId

        uri = self._request_template.format(**kwargs)
        d = {
            "API_VERSION": settings.API_VERSION,
            "envId": settings.envId,
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "API_HOST": settings.API_HOST,
            "METHOD": self.method,
            "URI": uri,
            "command": NAME,
            "action": self.name,
            "arguments": (args, kwargs)
             }

        try:
            response_json = json.loads(response)
        except ValueError, e:
            if settings.debug_mode:
                raise
            raise click.ClickException(str(e))

        response_json["meta"]["scalrctl"] = d
        dump = yaml.safe_dump(response_json, encoding='utf-8', allow_unicode=True, default_flow_style=False)
        click.echo(dump)


class RetrieveImage(Export):
    name = "image"
    route = "/{envId}/images/{imageId}/"
    enabled = True
    prompt_for = ["imageId"]


class RetrieveCloudCredentials(Export):
    name = "cloud-credentials"
    route = "/{envId}/cloud-credentials/{cloudCredentialsId}/"


class RetrieveCostCenter(Export):
    name = "cost-center"
    route = "/{envId}/cost-centers/{costCenterId}/"


class RetrieveEvent(Export):
    name = "event"
    route = "/{envId}/events/{eventId}/"


class RetrieveFarm(Export):
    name = "farm"
    route = "/{envId}/farms/{farmId}/"


class RetrieveFarmGlobalVariable(Export):
    name = "farm-global-variable"
    route = "/{envId}/farms/{farmId}/global-variables/{globalVariableName}/"


class RetrieveFarmRole(Export):
    name = "farm-role"
    route = "/{envId}/farm-roles/{farmRoleId}/"


class RetrievePlacementConfiguration(Export):
    name = "farm-role-placement-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/placement/"


class RetrieveInstanceConfiguration(Export):
    name = "farm-role-instance-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/instance/"


class RetrieveScalingConfiguration(Export):
    name = "farm-role-scaling-configuration"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/"


class RetrieveFarmRoleGlobalVariable(Export):
    route = "/{envId}/farm-roles/{farmRoleId}/global-variables/{globalVariableName}/"
    name = "farm-role-global-variable"


class RetrieveOrchestrationRule(Export):
    name = "farm-role-orchestration-rule"
    route = "/{envId}/farm-roles/{farmRoleId}/orchestration-rules/{orchestrationRuleId}/"


class RetrieveFarmRoleScaling(Export):
    name = "farm-role-scaling"
    route = "/{envId}/farm-roles/{farmRoleId}/scaling/{metricName}/"


class RetrieveProject(Export):
    name = "project"
    route = "/{envId}/projects/{projectId}/"


class RetrieveRole(Export):
    name = "role"
    route = "/{envId}/roles/{roleId}/"


class RetrieveRoleCategory(Export):
    name = "role-category"
    route = "/{envId}/role-categories/{roleCategoryId}/"


class RetrieveRoleGlobalVariable(Export):
    route = "/{envId}/roles/{roleId}/global-variables/{globalVariableName}/"
    name = "role-global-variable"


class RerrieveRoleImage(Export):
    name = "role-image"
    route = "/{envId}/roles/{roleId}/images/{imageId}/"


class RetrieveOrchestrationRule(Export):
    name = "orchestration-rule"
    route = "/{envId}/roles/{roleId}/orchestration-rules/{orchestrationRuleId}/"


class RetrieveScalingMetric(Export):
    name = "scaling-metric"
    route = "/{envId}/scaling-metrics/{metricName}/"


class RetrieveScript(Export):
    name = "script"
    route = "/{envId}/scripts/{scriptId}/"


class RetrieveScriptVersion(Export):
    name = "script-version"
    route = "/{envId}/scripts/{scriptId}/script-versions/{scriptVersionNumber}/"


class OSRetrieve(Export):
    name = "os"
    route = "/{envId}/os/{osId}/"
