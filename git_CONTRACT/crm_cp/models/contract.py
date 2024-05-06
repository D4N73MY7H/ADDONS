from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class CompanyContractDocuments(models.Model):
    _name = "cp.company_contract_document"
    _description = "Company Contract Document"

    name = fields.Char(string="Filename")
    document = fields.Binary(string="Document", attachment=True)
    company_contract_id = fields.Many2one(string="Company Contract", comodel_name="cp.company_contract")


class CompanyContractObject(models.Model):
    _name = "cp.company_contract_object"
    _description = "Company Contract Object"

    name = fields.Char(string="Name")
    component_ids = fields.One2many(string="Components", comodel_name="cp.company_contract_component", inverse_name="contract_object_id")


class CompanyContractComponent(models.Model):
    _name = "cp.company_contract_component"
    _description = "Company Contract Component"

    name = fields.Char(string="Name")
    contract_object_id = fields.Many2one(string="Object", comodel_name="cp.company_contract_object",
                                         on_delete="cascade")


class CompanyContractState(models.Model):
    _name = "cp.company_contract_state"
    _description = "Company Contract State"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")


class CompanyContractCP(models.Model):
    _name = "cp.company_contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Company Contract"

    name = fields.Char(string="Description", required=True, tracking=True)
    state = fields.Selection(string="Status", required=True, default="draft", tracking=True, selection=[('draft', 'DRAFT'),
                                                                                                        ('active', 'ACTIVE'),
                                                                                                        ('maintenance', 'MAINTENANCE'),
                                                                                                        ('warranty', 'WARRANTY'),
                                                                                                        ('suspended', 'SUSPENDED'),
                                                                                                        ('discontinued', 'DISCONTINUED'),
                                                                                                        ('finished', 'FINISHED')])
    state_id = fields.Many2one(string="State",
                               comodel_name="cp.company_contract_state",
                               default=lambda self: self.env['cp.company_contract_state'].search([('name', '=', 'Draft')]),
                               tracking=True)
    parent_contract_id = fields.Many2one(string="Parent Contract", comodel_name="cp.company_contract", tracking=True)
    contract_appendix_id = fields.Many2one(string="Appendix", comodel_name="cp.company_contract", tracking=True)
    type = fields.Selection(string="Type", selection=[('sales', 'Sales Contract'),
                                                       ('purchase', 'Purchase Contract'),
                                                       ('sponsored', ' Sponsored')])
    subtype = fields.Selection(string="Subtype", selection=[('business', 'Business'),
                                                           ('government_institution', 'Government Institution'),
                                                           ('local_institution', 'Local Institution'),
                                                           ('organisations', ' Organisation')])
    object_ids = fields.Many2many(string="Objects", comodel_name="cp.company_contract_object")  # Gerald Perditesim
    component_ids = fields.Many2many(string="Components", comodel_name="cp.company_contract_component", domain="[('contract_object_id', 'in', object_ids)]")  # Gerald Perditesim
    category_ids = fields.Many2many(string="Categories", comodel_name="helpdesk.tag")  # need to add dependency
    has_maintenance_category = fields.Char(string="Maintenance Category", compute="_compute_has_maintenance_category", store=True)
    sla_id = fields.Many2one(string="SLA", comodel_name="helpdesk.sla", ondelete="set null")  # need to add dependency
    contract_hours = fields.Float(string="Contract Hours")
    currency_id = fields.Many2one(string="Currency", comodel_name="res.currency")  # need to add dependency
    rate = fields.Float(string="Rate", compute="_compute_contract_rate", store=True)
    currency_symbol = fields.Char(string="Currency Symbol", related="currency_id.symbol", store=True)
    amount_no_tvsh_currency = fields.Monetary(string="Value excluding TVSH (valute)")
    amount_with_tvsh_currency = fields.Monetary(string="Value including TVSH (valute)", compute="_compute_amount_with_tvsh_currency", inverse="_inverse_amount_with_tvsh_currency", store=True)
    total_maintenance_amount_no_tvsh = fields.Monetary(string="Maintenance total excluding TVSH")
    periodic_maintenance_amount_no_tvsh = fields.Monetary(string="Periodic maintenance value excluding TVSH")
    amount_no_tvsh_lek = fields.Float(string="Value excluding TVSH (lek)")
    amount_with_tvsh_lek = fields.Float(string="Value including TVSH (lek)")
    ref_no = fields.Char(string="Ref No")
    ref_no_cp = fields.Char(string="Ref No CP")
    timeframe = fields.Selection(string="Duration", selection=[('renewable_fixed_term', 'Automatically Renewable'),
                                                                                 ('unlimited_form', 'Indefinite Term'),
                                                                                 ('fixed_term', 'Fixed Term')])
    start_date = fields.Date(string="Start Date", tracking=True)
    sign_date = fields.Date(string="Sign Date", tracking=True)
    renewal_date = fields.Date(string="Last Renewal Date", tracking=True)
    renewal_timeframe = fields.Integer(string="Renovation Time", tracking=True)
    renewal_unit = fields.Selection(string="Renovation Unit", tracking=True, selection=[('day', 'Dite'),
                                                                                           ('month', 'Muaj'),
                                                                                           ('year', 'Vite')])
    notification_timeframe = fields.Integer(string="Notification Time", tracking=True)
    notification_unit = fields.Selection(string="Notification Unit", tracking=True, selection=[('day', 'Dite'),
                                                                                                 ('month', 'Muaj'),
                                                                                                 ('year', 'Vite')])
    end_date = fields.Date(string="End Date", tracking=True)
    responsible_persona = fields.Many2one(string="Responsible Person", comodel_name="hr.employee")  # need to add dependency
    partner_penalty = fields.Float(string="Partner's Penalty")
    partner_id = fields.Many2one(string="Partner", comodel_name="res.partner")  # need to add dependency
    project_ids = fields.One2many(string="Project", comodel_name="project.project", inverse_name="company_contract_id")  # need to add dependency
    opportunity = fields.Many2one(string="Opportunity", comodel_name="crm.lead")  # need to add dependency
    sales_order_id = fields.Many2one(string="Sales Order", comodel_name="sale.order")  # need to add dependency
    responsible_client = fields.Char(string="Responsible Partner")
    client_id_email = fields.Char(string="Email")
    client_id_phone = fields.Char(string="Phone")
    contract_manager_id = fields.Many2one(string="Contract's Manager", comodel_name="hr.employee")
    company_penalty = fields.Float(string="Company's penalty")
    contract_performance_id = fields.Many2one(string="Contract's Performance",
                                              comodel_name="cp.company_contract_performance",
                                              default=lambda self: self.env['cp.company_contract_performance'].search(
                                                  [('name', '=', 'proceset zhvillohen ne perputhje me termat dhe afatet kontraktuale')], limit=1)
                                              )
    implementation_start_date = fields.Date(string="Implementation Start Date", tracking=True)
    implementation_end_date = fields.Date(string="Implementation End Date", tracking=True)
    maintenance_start_date = fields.Date(string="Maintenance Start Date", tracking=True)
    maintenance_end_date = fields.Date(string="Maintenance End Date", tracking=True)
    warranty_start_date = fields.Date(string="Warranty Start Date", tracking=True)
    warranty_end_date = fields.Date(string="Warranty End Date", tracking=True)
    # deliveries = fields.One2many(string="Dorezimet", comodel_name="")  # ???????????????????????? Nga ku do merren
    contract_user_ids = fields.Many2many(string="Users", comodel_name="hr.employee.public")
    sales_order_ids = fields.One2many(string="Sales Orders", comodel_name="sale.order", inverse_name="company_contract_id")
    comments = fields.Char(string="Comments")
    projects_total = fields.Integer(string="Total Projects", compute="_compute_projects_total")
    sales_order_total = fields.Integer(string="Sale Order Total", compute="_compute_sales_order_total")
    contract_users_total = fields.Integer(string="Users total", compute="_compute_contract_users_total")
    # deliveries_total =
    # total_amount = fields.Float(string="Total Amount", compute="_compute_total_amount", store=True, readonly=True)
    active = fields.Boolean(string="Active", default=True)
    document_ids = fields.One2many(string="Contract Documents", comodel_name="cp.company_contract_document", inverse_name="company_contract_id")
    state_id_code = fields.Char(strings="State Code", related="state_id.code")

    @api.constrains('start_date', 'end_date')
    def _check_start_end_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError("Data e fillimit te kontrates nuk mund te jete me vone se ajo e mbarimit")

    @api.constrains('implementation_start_date', 'implementation_end_date')
    def _check_implementation_dates(self):
        for rec in self:
            if rec.implementation_start_date > rec.implementation_end_date:
                raise ValidationError("Data e fillimit te implementimit nuk mund te jete me vone se ajo e mbarimit")

    @api.constrains('maintenance_start_date', 'maintenance_end_date')
    def _check_maintenance_dates(self):
        for rec in self:
            if rec.maintenance_start_date > rec.maintenance_end_date:
                raise ValidationError("Data e fillimit te mirembajtjes nuk mund te jete me vone se ajo e mbarimit")

    @api.constrains('warranty_start_date', 'warranty_end_date')
    def _check_warranty_dates(self):
        for rec in self:
            if rec.warranty_start_date > rec.warranty_end_date:
                raise ValidationError("Data e fillimit te garancise nuk mund te jete me vone se ajo e mbarimit")

    # @api.depends('amount_no_tvsh_currency')
    # def _compute_total_amount(self):
    #     for record in self:
    #         record.total_amount = sum(record.amount_no_tvsh_currency for record in self)

    @api.onchange('state_id')
    def _onchange_state_id_update_state(self):
        current_state = self.state_id.code
        mapping = {"draft": "draft",
                   "active": "active",
                   "maintenance": "maintenance",
                   "warranty": "warranty",
                   "suspended": "suspended",
                   "discontinued": "discontinued",
                   "finished": "finished",
                   }
        new_state = mapping.get(current_state)
        if new_state:
            self.state = new_state
        else:
            self.state = "draft"

    # ---------------- On Change functions  -----------------
    @api.onchange('start_date')
    def _onchange_start_date(self):

        for rec in self:
            if rec.start_date:
                active_state = self.env["cp.company_contract_state"].search([("code", "=", "active")])
                rec.state_id = active_state.id

    """ # Gerald Update """
    # @api.onchange('contract_user_ids')
    # def _onchange_user_ids(self):
    #     group_id = self.env.ref('crm_cp.group_cp_company_contract_users_from_panel')
    #     contract_admin_group = self.env.ref('crm_cp.group_cp_company_contract_admin')
    #     contract_user_group = self.env.ref('crm_cp.group_cp_company_contract_user')
    #     contract_users = self.env["res.users"].browse(self.contract_user_ids.user_id.ids)
    #     in_groups = []
    #     in_groups.extend(group_id.users.ids)
    #     in_groups.extend(contract_admin_group.users.ids)
    #     in_groups.extend(contract_user_group.users.ids)
    #     users_to_add = contract_users.filtered(lambda user: user.id not in in_groups)
    #     if users_to_add and len(users_to_add) > 0:
    #         group_id.users |= users_to_add

    # ------------ Compute & Inverse functions  -------------

    @api.depends('start_date', 'currency_id', 'currency_id.rate_ids')
    def _compute_contract_rate(self):
        for rec in self:
            if rec.start_date and rec.currency_id:
                rate_ids = rec.currency_id.rate_ids.filtered(
                    lambda r: r.name <= rec.start_date
                ).sorted(key=lambda r: r.name, reverse=True)

                if rate_ids:
                    rec.rate = rate_ids[0].inverse_company_rate

    @api.depends('amount_no_tvsh_currency', 'amount_with_tvsh_currency', 'rate')
    def _compute_amount_with_tvsh_currency(self):
        for rec in self:
            if rec.currency_symbol == "ALL":
                if rec.amount_no_tvsh_currency:
                    rec.amount_with_tvsh_currency = rec.amount_no_tvsh_currency * 1.2
                    rec.amount_with_tvsh_lek = rec.amount_no_tvsh_currency * 1.2
                    rec.amount_no_tvsh_lek = rec.amount_no_tvsh_currency
            else:
                if rec.amount_no_tvsh_currency:
                    rec.amount_with_tvsh_currency = rec.amount_no_tvsh_currency * 1.2
                    rec.amount_with_tvsh_lek = rec.amount_no_tvsh_currency * rec.rate * 1.2
                    rec.amount_no_tvsh_lek = rec.amount_no_tvsh_currency * rec.rate

    def _inverse_amount_with_tvsh_currency(self):
        for rec in self:
            if rec.currency_symbol == "ALL":
                if rec.amount_no_tvsh_currency:
                    rec.amount_no_tvsh_currency = rec.amount_with_tvsh_currency / 1.2
                    rec.amount_no_tvsh_lek = rec.amount_with_tvsh_currency / 1.2
                    rec.amount_with_tvsh_lek = rec.amount_with_tvsh_currency
            else:
                if rec.amount_with_tvsh_currency:
                    rec.amount_no_tvsh_currency = rec.amount_with_tvsh_currency / 1.2
                    rec.amount_no_tvsh_lek = rec.amount_with_tvsh_currency * rec.rate / 1.2
                    rec.amount_with_tvsh_lek = rec.amount_with_tvsh_currency * rec.rate

    @api.depends('category_ids')
    def _compute_has_maintenance_category(self):
        for rec in self:
            if rec.category_ids.filtered(lambda x: x.name == "maintenance"):
                rec.has_maintenance_category = "maintenance"
            else:
                rec.has_maintenance_category = ""

    @api.depends('project_ids')
    def _compute_projects_total(self):
        for rec in self:
            rec.projects_total = len(rec.project_ids) if rec.project_ids else 0

    @api.depends('sales_order_ids')
    def _compute_sales_order_total(self):
        for rec in self:
            rec.sales_order_total = len(rec.sales_order_ids) if rec.sales_order_ids else 0

    @api.depends('contract_user_ids')
    def _compute_contract_users_total(self):
        for rec in self:
            rec.contract_users_total = len(rec.contract_user_ids.ids) if rec.contract_user_ids.ids else 0

    # ------------ Create contract appendix  -------------
    def action_create_contract_appendix(self):
        for rec in self:
            values = {
                'name': rec.name + " (Aneks)",
                'parent_contract_id': rec.id,
                'type': rec.type,
                'ref_no': rec.ref_no,
                'ref_no_cp': rec.ref_no_cp,
                'contract_object': rec.contract_object,
                'component': rec.component,
                'contract_hours': rec.contract_hours,
                'timeframe': rec.timeframe
            }

            contract_copy = self.env["cp.company_contract"].create(values)
            contract_copy.write({"project_ids": [(6, 0, rec.project_ids.ids)],
                                 "contract_user_ids": [(6, 0, rec.contract_user_ids.ids)],
                                 "category_ids": [(6, 0, rec.category_ids.ids)]})

            discontinued_state = self.env["cp.company_contract_state"].search([("code", "=", "discontinued")])
            rec.state_id = discontinued_state.id
            rec.contract_appendix_id = contract_copy.id

            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'cp.company_contract',
                'res_id': contract_copy.id,
                'target': 'current',
                'context': request.env.context,
                'flags': {'form': {'action_buttons': True}},
            }

    # ------------ Projects view button  -------------
    @api.model
    def cron_check_renewal_date(self):
        today = datetime.now().date()
        recs = self.env['cp.company_contract'].search([('timeframe', '=', 'renewable_fixed_term'),
                                                       ('end_date', '=', today),
                                                       ('state_id.code', 'in', ['active', 'maintenance', 'warranty'])])
        for rec in recs:
            renewal_date = rec.renewal_date
            renewal_time = rec.renewal_timeframe
            renewal_unit = rec.renewal_unit

            new_renewal_date, new_end_date = None, None
            if renewal_unit == 'day':
                new_renewal_date = renewal_date + timedelta(days=renewal_time)
                new_end_date = rec.end_date + timedelta(days=renewal_time)
            elif renewal_unit == 'month':
                new_renewal_date = renewal_date + relativedelta(months=renewal_time)
                new_end_date = rec.end_date + relativedelta(months=renewal_time)
            elif renewal_unit == 'year':
                new_renewal_date = renewal_date + relativedelta(years=renewal_time)
                new_end_date = rec.end_date + relativedelta(years=renewal_time)

            if new_renewal_date and new_end_date:
                rec.write({
                    'end_date': new_end_date,
                    'renewal_date': new_renewal_date,
                })

    @api.model
    def cron_contract_phase_status_update(self):
        today = datetime.now().date()
        recs = self.env['cp.company_contract'].search([('state_id.code', 'in', ['active', 'maintenance', 'warranty']),
                                                       "|", ('maintenance_start_date', '=', today),
                                                       ('warranty_start_date', '=', today)])

        m_updates = recs.filtered(lambda x: x.maintenance_start_date == today)
        w_updates = recs.filtered(lambda x: x.warranty_start_date == today)

        for m in m_updates:
            maintenance_state = self.env["cp.company_contract_state"].search([("code", "=", "maintenance")])
            m.write({"state_id": maintenance_state.id})
        for w in w_updates:
            warranty_state = self.env["cp.company_contract_state"].search([("code", "=", "warranty")])
            w.write({"state_id": warranty_state.id})

    def cron_company_contract_archive(self):
        # recs = self.env['cp.company_contract'].search([("active", "=", True)])
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        recs = self.env['cp.company_contract'].search([("active", "=", True), ('end_date', '<', seven_days_ago)])
        for rec in recs:
            rec.active = False


    # ------------ Projects view button  -------------
    def action_get_projects_view(self):
        return {
            'name': ('Projektet'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'view_mode': 'tree,form',
            'domain': [('company_contract_id', '=', self.id)],
            'context': {
                'default_company_contract_id': self.id,
                'default_date_start': self.start_date if self.start_date else False,
                'default_date': self.end_date if self.end_date else False,
            },
            'target': 'current',
        }

    # ------------ Sales Orders view button  -------------
    def action_get_sale_orders_view(self):
        return {
            'name': ('Sale Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('company_contract_id', '=', self.id)],
            'context': {'default_company_contract_id': self.id},
            'target': 'current',
        }

    # def action_get_documents_view(self):
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'cp.company_contract',
        #     'res_id': self.id,
        #     'view_mode': 'form',
        #     'view_id': self.env.ref('crm_cp.company_contract_cp_documents_form_view').id,
        #     'target': 'new'
        # }

    # ------------ Users view buttons  -------------
    def action_dummy_get_contract_users(self):
        pass
