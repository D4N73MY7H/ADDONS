import json
import logging
import time
from datetime import datetime, date
from lxml import etree

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError

class Employee(models.Model):
    _inherit = "hr.employee"


    llogarit_kontabel = fields.Many2one('account.account', string='Llogarite')  #Sherben per pagesen e pagave