# Copyright (C) 2009 PreludeIDS Technologies. All Rights Reserved.
# Author: Sebastien Tricaud <stricaud@inl.fr>
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
#
# This file is part of the Prelude-Correlator program.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.

from pycor.utils import flatten
from pycor.plugins import Plugin
from pycor.context import Context


class OpenSSHMultipleAuthTypesPlugin(Plugin):
    def run(self, idmef):
        if idmef.Get("alert.analyzer(-1).manufacturer") != "OpenSSH":
                return

        if idmef.Get("alert.assessment.impact.completion") != "succeeded":
                return

        users = flatten(idmef.Get("alert.target(*).user.user_id(*).name"))
        addr  = flatten(idmef.Get("alert.target(*).node.address(*).address"))
        if len(users) == 0 or len(addr) == 0:
                return

        meaning = idmef.Get("alert.additional_data(*).meaning")
        if not meaning:
                return

        try:
                i = meaning.index("Authentication method")
        except:
                return

        data = idmef.Get("alert.additional_data(%d).data" % i)

        for username in users:
            for target in addr:
                ctx = Context("SSH_MAT_" + target + username, {"threshold": 1}, update = True)
                ctx.Set("alert.source(>>)", idmef.Get("alert.source"))
                ctx.Set("alert.target(>>)", idmef.Get("alert.target"))
                ctx.Set("alert.correlation_alert.alertident(>>).alertident", idmef.Get("alert.messageid"))
                ctx.Set("alert.correlation_alert.alertident(-1).analyzerid", idmef.Get("alert.analyzer(*).analyzerid")[-1])

                if not ctx.has_attr("authtype"):
                    ctx.authtype = data
                elif ctx.authtype != data:
                    ctx.Set("alert.classification.text", "Multiple authentication methods")
                    ctx.Set("alert.correlation_alert.name", "Multiple authentication methods")
                    ctx.Set("alert.assessment.impact.severity", "medium")
                    ctx.Set("alert.assessment.impact.description", "Multiple ways of authenticating a single user have been found over SSH. If passphrase is the only allowed method, make sure you disable passwords.")
                    ctx.alert()
                    ctx.destroy()
