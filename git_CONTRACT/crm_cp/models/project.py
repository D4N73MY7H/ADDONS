import datetime

from odoo import models, fields, api


class Project(models.Model):
    _inherit = "project.project"

    company_contract_id = fields.Many2one(string="Contract", comodel_name="cp.company_contract")
    contract_start = fields.Date(string="Contract Date", related="company_contract_id.start_date")
    contract_end = fields.Date(string="Contract Expiry", related="company_contract_id.end_date")
    contract_state = fields.Boolean(string="Statusi i kontrates", compute="_compute_company_contract_state")
    implementation_start = fields.Date(string="Implementation Start Date", related="company_contract_id.implementation_start_date")
    implementation_end = fields.Date(string="Implementation End Date", related="company_contract_id.implementation_end_date")
    maintenance_start = fields.Date(string="Maintenance Start Date", related="company_contract_id.maintenance_start_date")
    maintenance_end = fields.Date(string="Maintenance End Date", related="company_contract_id.maintenance_end_date")
    sla_id = fields.Many2one(string="SLA", comodel_name="helpdesk.sla", related="company_contract_id.sla_id")
    feedback_ids = fields.One2many(string="Feedbacks", comodel_name="cp.project_feedback", inverse_name="project_id")
    document_ids = fields.One2many(string="Documents", comodel_name="cp.project_document", inverse_name="project_id")
    doc_count = fields.Integer(string="Document's Count", compute="_compute_doc_count")
    task_count = fields.Integer(compute='_compute_task_ticket_count', string="Task Count")
    project_ticket_count = fields.Integer(compute='_compute_task_ticket_count', string="Ticket Count")

    @api.depends('company_contract_id', 'company_contract_id.end_date')
    def _compute_company_contract_state(self):
        for rec in self:
            if rec.company_contract_id.state_id.code == 'finished':
                rec.contract_state = True
            else:
                rec.contract_state = False

    @api.depends('document_ids')
    def _compute_doc_count(self):
        for rec in self:
            if rec.document_ids:
                rec.doc_count = len(rec.document_ids)
            else:
                rec.doc_count = 0

    def _compute_task_ticket_count(self):
        for rec in self:
            tasks = rec.tasks.filtered(lambda x: x.type == 'task')
            tickets = rec.tasks.filtered(lambda x: x.type == 'ticket')
            rec.task_count = len(tasks) if tasks else 0
            rec.project_ticket_count = len(tickets) if tickets else 0

    @api.model
    def cron_check_contract_expired(self):

        today_date = datetime.datetime.now().date()

        c = self.env["cp.company_contract"].browse(14)
        p = self.env["project.project"].browse(19)

        projects = self.env['project.project'].search([('contract_state', '=', False),
                                                       ('company_contract_id.end_date', '<', today_date)])

        if projects:
            projects.write(
                {'contract_state': True}
            )

    def toggle_active(self):
        # self.env.cr.execute("""
        #     UPDATE project_milestone
        #     SET active = TRUE
        #     WHERE project_id = %s;
        #
        #     UPDATE project_task
        #     SET active = TRUE
        #     WHERE project_id = %s;
        #
        #     UPDATE helpdesk_ticket
        #     SET active = TRUE
        #     WHERE project_id = %s;
        # """, (self.id, self.id, self.id))
        #
        milestones = self.env["project.milestone"].search([("project_id", "=", self.id)])
        tasks = self.env["project.task"].search([("project_id", "=", self.id)])
        tickets = self.env["helpdesk.ticket"].search([("project_id", "=", self.id)])
        milestones.write({"active": True})
        tasks.write({"active": True})
        tickets.write({"active": True})
        self.active = True

    def toggle_inactive(self):
        """ Gerald Update """
        # self.env.cr.execute("""
        #     UPDATE project_milestone
        #     SET active = FALSE
        #     WHERE project_id = %s;
        #
        #     UPDATE project_task
        #     SET active = FALSE
        #     WHERE project_id = %s;
        #
        #     UPDATE helpdesk_ticket
        #     SET active = FALSE
        #     WHERE project_id = %s;
        # """, (self.id, self.id, self.id))
        #
        milestones = self.env["project.milestone"].search([("project_id", "=", self.id)])
        tasks = self.env["project.task"].search([("project_id", "=", self.id)])
        tickets = self.env["helpdesk.ticket"].search([("project_id", "=", self.id)])
        milestones.write({"active": False})
        tasks.write({"active": False})
        tickets.write({"active": False})
        self.active = False

    def open_attachments_view(self):
        self.ensure_one()
        return {
            'name': ('Attachments'),
            'res_model': 'cp.project_document',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('project_cp.cp_project_documents_tree_view').id,
            'view_mode': 'tree',
            'target': 'new',
            'context': {'default_project_id': self.id}
        }
