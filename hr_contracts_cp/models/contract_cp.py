from datetime import datetime, date
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError,UserError
from odoo.tools.translate import _


class HRContractCP(models.Model):
    _inherit = "hr.contract"

    paga_per_llog_sig_shoq = fields.Float(compute='_compute_paga_sigurime_shoq',
                                          string=_('Salary for social insurance calculation'))
    paga_per_llog_sig_shendet = fields.Float(compute='_compute_paga_sigurime_shendet',
                                             string=_('Salary for health insurance calculation'))
    tatim_mbi_te_ardhurat = fields.Float( compute='_compute_tatim_mbi_te_ardhurat',
                                          string=_('Income tax', ))
    sig_shendetesore_punonjesi = fields.Float(compute = '_compute_sigurime_shendetesore_punonjesi',
                                              string=_('Health insurance employee', ))
    sig_shoqerore_punonjesi = fields.Float(compute='_compute_sigurime_shoqerore_punonjesi'
                                                   ,string=_('Social insurance employee',))
    sig_shendetesore_punedhenesi = fields.Float(compute='_compute_sigurime_shendetesore_punedhenesi',
                                                string=_('Health insurance employer', ))
    sig_shoqerore_punedhenesi = fields.Float(compute ='_compute_sigurime_shoqerore_punedhenesi',
                                             string=_('Social insurance employer', ))
    nr_mesatar_oreve = fields.Float(string=_("Average working hours"),default=155)
    net = fields.Float(compute="_compute_paga_neto", string='Net' )
    pagesa_kompanie = fields.Float(string=_('Other company payments'))
    kosto_totale_page_per_punonjesin = fields.Float(compute="_compute_kosto_totale_page_per_punonjesin",string=_('Total salary  cost for employee' ))
    kosto_orare = fields.Monetary(compute="_kosto_orare",string=_('Hourly cost'))


    def _compute_paga_sigurime_shoq(self):
        for rec in self:
            payslips = rec.structure_type_id.default_struct_id
            paga_max , paga_min = payslips.max_wage , payslips.min_wage

            if paga_max == 0 or paga_min == 0:
                raise UserError("Max wage or min wage are 0")
            if rec.wage > paga_max:
                rec.paga_per_llog_sig_shoq = paga_max
            elif paga_max > rec.wage > paga_min:
                rec.paga_per_llog_sig_shoq = rec.wage
            else:
                rec.paga_per_llog_sig_shoq = paga_min
            rec.paga_per_llog_sig_shoq = fields.Float.round(rec.paga_per_llog_sig_shoq ,0)


    def _compute_paga_sigurime_shendet(self):
        for rec in self:
            payslip = rec.structure_type_id.default_struct_id
            paga_max , paga_min = payslip.max_wage , payslip.min_wage
            if rec.wage < paga_min:
                rec.paga_per_llog_sig_shendet = paga_min
            else:
                rec.paga_per_llog_sig_shendet = rec.wage
            rec.paga_per_llog_sig_shendet = fields.Float.round(rec.paga_per_llog_sig_shendet, 0)

    def _compute_tatim_mbi_te_ardhurat(self):
        for rec in self:
            if rec.date_start < date(2022, 4, 1):
                payslips = rec.structure_type_id.default_struct_id
                paga_min, paga_max = payslips.min_wage, payslips.max_wage
                if rec.wage < paga_min:
                    rec.tatim_mbi_te_ardhurat = 0
                elif paga_max >= rec.wage >= paga_min:
                    rec.tatim_mbi_te_ardhurat = (rec.wage - paga_min) * 0.13
                else:
                    rec.tatim_mbi_te_ardhurat = (rec.wage - paga_max) * 0.23 + 15600
            else:
                #nivelet e pagave
                paga_1 = 50000
                paga_2 = 60000
                paga_3 = 200000
                paga_taksim_1 = 35000
                paga_taksim_2 = 30000
                # taksimi sipas ligjit te ri
                if rec.wage <= paga_1:
                    rec.tatim_mbi_te_ardhurat = 0
                elif paga_1 < rec.wage <= paga_2:
                    rec.tatim_mbi_te_ardhurat = (rec.wage - paga_taksim_1) * 0.13
                elif paga_2 < rec.wage <= paga_3:
                    rec.tatim_mbi_te_ardhurat = (rec.wage - paga_taksim_2) * 0.13
                elif rec.wage > paga_3:
                    rec.tatim_mbi_te_ardhurat = (rec.wage - paga_3) * 0.23 + 22100
            rec.tatim_mbi_te_ardhurat = fields.Float.round(rec.tatim_mbi_te_ardhurat, 0)


    def _compute_sigurime_shoqerore_punonjesi(self):
        for rec in self:
            rec.sig_shoqerore_punonjesi = rec.paga_per_llog_sig_shoq * 0.095
            rec.sig_shoqerore_punonjesi = fields.Float.round(rec.sig_shoqerore_punonjesi, 0)

    def _compute_sigurime_shendetesore_punonjesi(self):
        for rec in self:
            rec.sig_shendetesore_punonjesi = rec.paga_per_llog_sig_shendet * 0.017
            rec.sig_shendetesore_punonjesi = fields.Float.round(rec.sig_shendetesore_punonjesi, 0)

    def _compute_sigurime_shendetesore_punedhenesi(self):
        for rec in self:
            if rec.wage == 0:
                result = 0
            elif rec.wage >= 26000:
                result = round(rec.wage * 0.034) - round(rec.wage * 0.017)
            else:
                result = round(26000 * 0.034) - round(rec.wage * 0.017)
            rec.sig_shendetesore_punedhenesi = result
            rec.sig_shendetesore_punedhenesi = fields.Float.round(rec.sig_shendetesore_punedhenesi, 0)

    def _compute_sigurime_shoqerore_punedhenesi(self):
        for rec in self:
            rec.sig_shoqerore_punedhenesi = rec.paga_per_llog_sig_shoq * 0.15
            rec.sig_shoqerore_punedhenesi = fields.Float.round(rec.sig_shoqerore_punedhenesi, 0)

    def _compute_paga_neto(self):
        for rec in self:
            rec.net = rec.wage - rec.sig_shendetesore_punonjesi - rec.sig_shoqerore_punonjesi - rec.tatim_mbi_te_ardhurat
            rec.net = fields.Float.round(rec.net, 0)

    def _compute_kosto_totale_page_per_punonjesin(self):
        for rec in self:
            rec.kosto_totale_page_per_punonjesin = rec.wage + rec.sig_shoqerore_punedhenesi + rec.sig_shendetesore_punedhenesi
            rec.kosto_totale_page_per_punonjesin = fields.Float.round(rec.kosto_totale_page_per_punonjesin, 0)

    def _kosto_orare(self):
        for rec in self:
            if rec.nr_mesatar_oreve==0:
                raise UserError("The average working hours is 0")
            rec.kosto_orare = rec.kosto_totale_page_per_punonjesin / rec.nr_mesatar_oreve
            rec.kosto_orare = fields.Float.round(rec.kosto_orare, 0)



