# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models


def uninstall_hook(env):
    env.cr.execute(
        "DELETE FROM ir_model_data WHERE module = 'l10n_al'"
    )
