from odoo import models, fields, api


class CpContractSLA(models.Model):
    _inherit = "helpdesk.sla"

    lp_response_time = fields.Integer(string="Response Time")
    lp_response_unit = fields.Selection(string="Response Unit", selection=[("minute", "Minutes"),
                                                                           ("hour", "Hours"),
                                                                           ("working_day", "Working Days"),
                                                                           ("calendar_day", "Calendar Days")])
    lp_resolve_time = fields.Integer(string="Resolve Time")
    lp_resolve_unit = fields.Selection(string="Resolve Unit", selection=[("minute", "Minutes"),
                                                                       ("hour", "Hours"),
                                                                       ("working_day", "Working Days"),
                                                                       ("calendar_day", "Calendar Days")])


    mp_response_time = fields.Integer(string="Response Time")
    mp_response_unit = fields.Selection(string="Response Unit", selection=[("minute", "Minutes"),
                                                                         ("hour", "Hours"),
                                                                         ("working_day", "Working Days"),
                                                                         ("calendar_day", "Calendar Days")])
    mp_resolve_time = fields.Integer(string="Resolve Time")
    mp_resolve_unit = fields.Selection(string="Resolve Unit", selection=[("minute", "Minutes"),
                                                                       ("hour", "Hours"),
                                                                       ("working_day", "Working Days"),
                                                                       ("calendar_day", "Calendar Days")])


    hp_response_time = fields.Integer(string="Response Time")
    hp_response_unit = fields.Selection(string="Response Unit", selection=[("minute", "Minutes"),
                                                                         ("hour", "Hours"),
                                                                         ("working_day", "Working Days"),
                                                                         ("calendar_day", "Calendar Days")])
    hp_resolve_time = fields.Integer(string="Resolve Time")
    hp_resolve_unit = fields.Selection(string="Resolve Unit", selection=[("minute", "Minutes"),
                                                                       ("hour", "Hours"),
                                                                       ("working_day", "Working Days"),
                                                                       ("calendar_day", "Calendar Days")])

    team_id = fields.Many2one('helpdesk.team', 'Helpdesk Team', required=False)
    # stage_id = fields.Many2one(
    #     'helpdesk.stage', 'Target Stage',
    #     help='Minimum stage a ticket needs to reach in order to satisfy this SLA.')
    time = fields.Float('In', help='Time to reach given stage based on ticket creation date', default=0, required=False)
