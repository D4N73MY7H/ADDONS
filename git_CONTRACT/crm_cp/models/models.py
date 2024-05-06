from odoo import models, fields, api
from odoo.http import request
from datetime import timedelta, datetime
from odoo.exceptions import UserError,  ValidationError


class Stage(models.Model):
    _inherit = "crm.stage"

    code = fields.Char(string="Code")


class CRMCP(models.Model):
    _inherit = 'crm.lead'

    # Fields needed in the opportunities
    opportunity_object  = fields.Many2one(
        comodel_name='helpdesk.object',
        string='Object',
        required=False)
    # object_description = fields.Text(string="Object Description")

    helpdesk_tag_ids = fields.Many2many('helpdesk.tag', 'crm_lead_helpdesk_tag_rel', 'crm_lead_id', 'helpdesk_tag_id', string="Kategorite")

    # Tender Fields
    tender_field = fields.Boolean(string="Tender")
    publication_date = fields.Date(string="Publication Date")
    submission_date = fields.Date(string="Submission Date")
    appeal_date = fields.Date(string="Appeal Date")
    clarification_date = fields.Date(string="Clarification Date")

    # Second Currency Conversion Fields
    selected_currency_id = fields.Many2one('res.currency', string='Second Currency', required=True,
                                           default=lambda self: self.env['res.currency'].search([('name', '=', 'EUR')]).id)
    second_expected_revenue = fields.Monetary('Second Currency Expected Revenue',
                                              currency_field='selected_currency_id',
                                              compute='_compute_second_currency_expected_revenue')
    second_recurring_revenue = fields.Monetary('Second Currency Recurring Revenues',
                                               currency_field='selected_currency_id',
                                               groups="crm.group_use_recurring_revenues",
                                               compute='_compute_second_currency_expected_revenue')
    second_currency_rate = fields.Float(string='Rate', readonly=False, default=lambda self: self.env['res.currency'].search([('name', '=', 'EUR')]).inverse_rate)

    # PO related to CRM
    related_po_count = fields.Integer(compute="_compute_related_po_count")
    # Project related to CRM
    related_project_count = fields.Integer(compute="_compute_related_project_count")
    stage_id_code = fields.Char(string="Stage Code", related="stage_id.code", store=True)
    # Calculate Total cost for all related Sale Orders
    sale_order_ids = fields.One2many(string="Sale Orders", comodel_name="sale.order", inverse_name="opportunity_id")
    albanian_curr_id = fields.Many2one(string='Albanian Currency', comodel_name='res.currency',
                                       default=lambda self: self.env['res.currency'].search([('name', '=', 'ALL')]).id)
    total_so_cost_currency_lek = fields.Monetary('Total Sale Order Costs',
                                                 currency_field='albanian_curr_id',
                                                 compute='_compute_total_so_cost_currency_lek')

    # Compute related Project count
    def _compute_related_project_count(self):
        self.related_project_count = len(self.order_ids.project_id)
        self.related_project_count = len(self.order_ids.project_id)

    # Compute related PO count
    def _compute_related_po_count(self):
        po_related_to_so = self.env['purchase.order.line'].search([('sale_reference_line', 'in', self.order_ids.ids)])
        self.related_po_count = len(po_related_to_so.order_id.ids)

    # Show related POs
    def show_related_po(self):
        self.ensure_one()
        if len(self.order_ids) == 0:
            raise ValidationError("There are no PO available for this CRM")
        po_related_to_crm = self.env['purchase.order.line'].search([('sale_reference_line', 'in', self.order_ids.ids)])
        action_window = {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'name': 'Purchase Order',
            'views': [[False, 'tree'],
                      [False, 'form']],
            'context': {'create': False},
            'domain': [["id", "in", po_related_to_crm.order_id.ids]],
        }
        return action_window

    # Show related POs
    def show_related_project(self):
        self.ensure_one()
        if len(self.order_ids.project_id) == 0:
            raise ValidationError("There are no Project available for this CRM")
        action_window = {
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'name': 'Projects',
            'views': [[False, "form"]],
            'context': {'create': False},
            'res_id': self.order_ids.project_id.id,
        }
        return action_window

    def action_create_project_from_crm(self):
        for rec in self:

            date_start = False
            if rec.create_date:
                date_start = fields.Date.to_string(fields.Datetime.from_string(rec.create_date))

            values = {
                'name': rec.name,
                'date_start': date_start,
                'date': rec.date_deadline,
                'partner_id': rec.partner_id.id,
            }

            project = self.env["project.project"].create(values)

            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'project.project',
                'res_id': project.id,
                'target': 'current',
                'context': request.env.context,
                'flags': {'form': {'action_buttons': True}},
            }

    @api.onchange('selected_currency_id')
    def _get_currency_rate(self):
        if not self.selected_currency_id.active:
            raise ValidationError("Please select an active currency !")
        else:
            self.second_currency_rate = self.selected_currency_id.inverse_rate

    @api.onchange('publication_date')
    def _onchange_appeal_date(self):
        if self.publication_date:
            self.appeal_date = self.publication_date + timedelta(days=6)

    @api.onchange('submission_date')
    def _onchange_clarification_date(self):
        if self.submission_date:
            self.clarification_date = self.submission_date - timedelta(days=6)

    @api.onchange('stage_id')
    def _onchange_won_opportunity_create_contract(self):
        for rec in self:
            if rec.stage_id.code == "won":
                contracts = rec.env['cp.company_contract'].search([('opportunity', '=', self.id)])
                if not contracts or len(contracts) == 0:
                    values = {
                        "name": f"{rec.name} CONTRACT",
                        "type": False,
                        "opportunity": rec.id.origin,
                        "partner_id": self.partner_id.id,
                        "client_id_email": rec.email_from,
                        "client_id_phone": rec.phone
                    }

                    new_contract = self.env['cp.company_contract'].create(values)
                    new_contract.write({"category_ids": [(6, 0, self.helpdesk_tag_ids.ids)]})
            else:
                contract = self.env['cp.company_contract'].search([('opportunity', '=', rec.id)])
                if contract.state_id.code == 'draft':
                    contract.unlink()

    @api.depends('sale_order_ids', 'sale_order_ids.total_cost', 'sale_order_ids.calculation_line', 'sale_order_ids.calculation_line.purchase_price')
    def _compute_total_so_cost_currency_lek(self):
        for rec in self:
            recs = rec.sale_order_ids.filtered(lambda x: x.state == 'sale')
            cost = sum(r.total_cost * r.second_currency_rate for r in recs)
            rec.total_so_cost_currency_lek = cost

    def action_share_whatsapp(self):
        self.ensure_one()
        whatsapp_url = f'https://wa.me/{self.partner_id.mobile}'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': whatsapp_url
        }

    def cron_archive_opportunity_in_crm(self):
        leads = self.env['crm.lead'].search([("active", "=", True)])
        pass

    def action_get_company_contract(self):
        return {
            'name': ('Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'cp.company_contract',
            'view_mode': 'tree,form',
            'domain': [('opportunity', '=', self.id)],
            'context': {
                'default_opportunity': self.id,
                'create': False
            },
            'target': 'current',
        }

    @api.depends('expected_revenue', 'recurring_revenue', 'second_currency_rate')
    def _compute_second_currency_expected_revenue(self):
        if self.second_currency_rate > 0:
            self.second_expected_revenue = self.expected_revenue / self.second_currency_rate
            self.second_recurring_revenue = self.recurring_revenue / self.second_currency_rate

    def _merge_data(self, fnames=None):
        """ Prepare lead/opp data into a dictionary for merging. Different types
            of fields are processed in different ways:
                - text: all the values are concatenated
                - m2m and o2m: those fields aren't processed
                - m2o: the first not null value prevails (the other are dropped)
                - any other type of field: same as m2o

            :param fields: list of fields to process
            :return dict data: contains the merged values of the new opportunity
        """
        if fnames is None:
            fnames = self._merge_get_fields()
        fcallables = self._merge_get_fields_specific()

        # helpers
        def _get_first_not_null(attr, opportunities):
            value = False
            total_revenue = False
            for opp in opportunities:
                if opp[attr] and attr != 'expected_revenue' and attr != 'recurring_revenue':
                    value = opp[attr].id if isinstance(opp[attr], models.BaseModel) else opp[attr]
                    break
                elif opp[attr]:
                    value = opp[attr].id if isinstance(opp[attr], models.BaseModel) else opp[attr]
                    total_revenue += value
                    value = total_revenue
            return value

        # process the field's values
        data = {}
        for field_name in fnames:
            field = self._fields.get(field_name)
            if field is None:
                continue

            fcallable = fcallables.get(field_name)
            if fcallable and callable(fcallable):
                data[field_name] = fcallable(field_name, self)
            elif not fcallable and field.type in ('many2many', 'one2many'):
                continue
            else:
                data[field_name] = _get_first_not_null(field_name, self)  # take the first not null
        data['recurring_revenue'] = _get_first_not_null('recurring_revenue', self)
        return data

    @api.model
    def _check_leads_to_archive(self):
        lead_ids = self.env['crm.lead'].search([('type', '=', 'lead'), ('active', '=', 'True')])
        for lead in lead_ids:
            if lead.date_deadline:
                today_date = datetime.now().strftime('%Y-%m-%d')
                archive_planed_date = (lead.date_deadline + timedelta(days=30)).strftime('%Y-%m-%d')
                if today_date > archive_planed_date:
                    lead.active = False
            else:
                raise ValidationError("Something is not quite right, please contact the system manager. (1)")

    class CpSaleOrder(models.Model):
        _inherit = 'sale.order'

        state = fields.Selection(selection_add=[('invoiced', 'Invoiced'), ('posted', 'Posted')])

        @api.onchange('state')
        def _onchange_sale_order_state_is_sale(self):
            if self.state == 'sale':
                if self.opportunity_id:
                    won_stage = self.env['crm.stage'].search([('code', '=', 'Won')])
                    self.opportunity_id.state_id = won_stage
