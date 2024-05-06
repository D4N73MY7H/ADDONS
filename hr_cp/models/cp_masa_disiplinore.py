import json
import logging
import time
from datetime import datetime, date
from lxml import etree

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MasatDisiplinore(models.Model):
    _name = 'masat.disiplinore'
    _description = 'MasatDisiplinore'

    name = fields.Char()
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employees', required=True)
    measures_type_id = fields.Many2one(comodel_name='disciplin.measures.type', string='Discipline Measure Type',
                                       required=True)
    measure_start_date = fields.Date(string=' Measure Start Date', required=False)
    measure_end_date = fields.Date(string=' Measure End Date', required=False)
    measure_offense_type_id = fields.Many2one(comodel_name='offense.type', string='Type of offense', required=True)
    measure_duration = fields.Float(string='Duration(In months)', required=False)
    violation_description = fields.Text(string="Description of Infraction", required=False)
    plan_for_improvment = fields.Text(string="Plan for Improvement", required=False)
    decision_made = fields.Text(string="Decision Taken", required=False)
    consequences_further_violations = fields.Text(string="Consequences of Further Infractions", required=False)


class DisciplinMeasuresType(models.Model):
    _name = "disciplin.measures.type"
    _description = "Disciplinary Measure Types"

    name = fields.Char(string="Disciplinary Measure Type", required=True)
    measures_category = fields.Selection([
        ('shkrim', 'Written remark '),  # verejtje me shkrim
        ('verbale', 'Verbal Remark'),  # verejtje verbale
        ('tjera', 'Other'),
    ], string='Measure Category', required=True)


class OffenseType(models.Model):
    _name = "offense.type"
    _description = "Offense Type"
    name = fields.Char('Offense Type', required=True)
