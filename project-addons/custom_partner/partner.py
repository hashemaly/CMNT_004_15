# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pcomunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, exceptions, osv, _
from openerp.addons.account_followup.report import account_followup_print
from openerp.osv import osv, fields as fields2
from collections import defaultdict
import time
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import dateutil.relativedelta
from openerp.exceptions import ValidationError
from calendar import monthrange


class ResPartnerInvoiceType(models.Model):
    _name = 'res.partner.invoice.type'

    name = fields.Char('Name', required=True)


class ResPartner(models.Model):
    _inherit = "res.partner"

    annual_invoiced = fields.Float('Annual invoiced', readonly=True, store=True)
    past_year_invoiced = fields.Float('Past year invoiced', readonly=True, store=True)
    monthly_invoiced = fields.Float('Monthly invoiced', readonly=True, store=True)
    past_month_invoiced = fields.Float('Past Month invoiced', readonly=True, store=True)

    @api.model
    def _calculate_annual_invoiced(self):
        partner_obj = self.env['res.partner']
        invoice_obj = self.env['account.invoice']
        picking_obj = self.env['stock.picking']
        partner_ids = partner_obj.search([('is_company', '=', True),
                                          ('child_ids', '!=', False),
                                          ('customer', '=', True)])
        actual_year = datetime.now().year
        actual_month = datetime.now().month
        past_month = actual_month - 1
        actual_day = datetime.now().day
        start_year = str(actual_year) + '-01-01'
        start_past_year = str(actual_year - 1) + '-01-01'
        start_month = str(actual_year) + '-' + str(actual_month) + '-01'
        start_past_month = str(actual_year) + '-' + str(past_month) + '-01'
        end_year = str(actual_year) + '-12-31'
        end_past_year = str(actual_year - 1) + '-12-31'
        end_month = str(actual_year) + '-' + str(actual_month) + '-' + str(actual_day)
        end_day_past_month = monthrange(actual_year, past_month)
        end_past_month = str(actual_year) + '-' + str(past_month) + '-' + str(end_day_past_month[1])
        for partner in partner_ids:
            invoice_ids_year = invoice_obj.search([('date_invoice', '>=', start_year),
                                                   ('date_invoice', '<=', end_year),
                                                   ('partner_id', 'child_of', [partner.id]),
                                                   ('type', 'in', ['out_invoice', 'out_refund']),
                                                   ('number', 'not like', '%_ef%'),
                                                   '|',
                                                   ('state', '=', 'open'),
                                                   ('state', '=', 'paid')])

            invoice_ids_past_year = invoice_obj.search([('date_invoice', '>=', start_past_year),
                                                        ('date_invoice', '<=', end_past_year),
                                                        ('partner_id', 'child_of', [partner.id]),
                                                        ('type', 'in', ['out_invoice', 'out_refund']),
                                                        ('number', 'not like', '%_ef%'),
                                                        '|',
                                                        '|',
                                                        ('state', '=', 'open'),
                                                        ('state', '=', 'paid'),
                                                        ('state', '=', 'history')])

            invoice_ids_month = invoice_obj.search([('date_invoice', '>=', start_month),
                                                    ('date_invoice', '<=', end_month),
                                                    ('partner_id', 'child_of', [partner.id]),
                                                    ('type', 'in', ['out_invoice', 'out_refund']),
                                                    ('number', 'not like', '%_ef%'),
                                                    '|',
                                                    ('state', '=', 'open'),
                                                    ('state', '=', 'paid')])

            invoice_ids_past_month = invoice_obj.search([('date_invoice', '>=', start_past_month),
                                                         ('date_invoice', '<=', end_past_month),
                                                         ('partner_id', 'child_of', [partner.id]),
                                                         ('type', 'in', ['out_invoice', 'out_refund']),
                                                         ('number', 'not like', '%_ef%'),
                                                         '|',
                                                         ('state', '=', 'open'),
                                                         ('state', '=', 'paid')])

            picking_ids_year = picking_obj.search([('date_done', '>=', start_year),
                                                   ('date_done', '<=', end_year),
                                                   ('state', '=', 'done'),
                                                   ('invoice_state', '=', '2binvoiced'),
                                                   ('partner_id', 'child_of', [partner.id])])

            picking_ids_past_year = picking_obj.search([('date_done', '>=', start_past_year),
                                                        ('date_done', '<=', end_past_year),
                                                        ('invoice_state', '=', '2binvoiced'),
                                                        ('partner_id', 'child_of', [partner.id]),
                                                        ('state', '=', 'done')])

            picking_ids_month = picking_obj.search([('date_done', '>=', start_month),
                                                    ('date_done', '<=', end_month),
                                                    ('state', '=', 'done'),
                                                    ('invoice_state', '=', '2binvoiced'),
                                                    ('partner_id', 'child_of', [partner.id])])

            picking_ids_past_month = picking_obj.search([('date_done', '>=', start_past_month),
                                                         ('date_done', '<=', end_past_month),
                                                         ('state', '=', 'done'),
                                                         ('invoice_state', '=', '2binvoiced'),
                                                         ('partner_id', 'child_of', [partner.id])])

            annual_invoiced = 0.0
            past_year_invoiced = 0.0
            monthly_invoiced = 0.0
            past_month_invoiced = 0.0
            for invoice in invoice_ids_year:
                if invoice.type == 'out_refund':
                    annual_invoiced -= invoice.amount_untaxed
                else:
                    annual_invoiced += invoice.amount_untaxed

            for invoice in invoice_ids_month:
                if invoice.type == 'out_refund':
                    monthly_invoiced -= invoice.amount_untaxed
                else:
                    monthly_invoiced += invoice.amount_untaxed

            for invoice in invoice_ids_past_year:
                if invoice.type == 'out_refund':
                    past_year_invoiced -= invoice.amount_untaxed
                else:
                    past_year_invoiced += invoice.amount_untaxed

            for invoice in invoice_ids_past_month:
                if invoice.type == 'out_refund':
                    past_month_invoiced -= invoice.amount_untaxed
                else:
                    past_month_invoiced += invoice.amount_untaxed

            for picking in picking_ids_year:
                annual_invoiced += picking.amount_untaxed

            for picking in picking_ids_month:
                monthly_invoiced += picking.amount_untaxed

            for picking in picking_ids_past_year:
                past_year_invoiced += picking.amount_untaxed

            for picking in picking_ids_past_month:
                past_month_invoiced += picking.amount_untaxed

            vals = {'annual_invoiced': annual_invoiced, 'past_year_invoiced': past_year_invoiced,
                    'monthly_invoiced': monthly_invoiced, 'past_month_invoiced': past_month_invoiced}
            partner.write(vals)

    def _purchase_invoice_count(self, cr, uid, ids, field_name, arg, context=None):
        invoice = self.pool.get('account.invoice')
        res = {}
        for partner_id in ids:
            res[partner_id] = invoice.search_count(cr, uid, [
                ('partner_id', 'child_of', partner_id),
                '|', ('type', '=', 'in_invoice'), ('type', '=', 'in_refund')], context=context)
        return res

    def _invoice_total_real(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        if context is None:
            context = {}
        account_invoice_report = self.pool.get('account.invoice.report')
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        user_currency_id = user.company_id.currency_id.id
        for partner_id in ids:
            all_partner_ids = self.pool['res.partner'].search(
                cr, uid, [('id', 'child_of', partner_id)], context=context)

            # searching account.invoice.report via the orm is comparatively expensive
            # (generates queries "id in []" forcing to build the full table).
            # In simple cases where all invoices are in the same currency than the user's company
            # access directly these elements
            domain = [('partner_id', 'in', all_partner_ids),
                      ('state', 'not in', ['draft', 'cancel']),
                      ('number', 'not like', '%_ef%')]
            if context.get('date_from', False):
                domain.append(('date', '>=', context['date_from']))
            # generate where clause to include multicompany rules
            where_query = account_invoice_report._where_calc(cr, uid, domain,
                                                             context=context)
            account_invoice_report._apply_ir_rules(cr, uid, where_query, 'read', context=context)
            from_clause, where_clause, where_clause_params = where_query.get_sql()

            query = """ WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                                SELECT r.currency_id, r.rate, r.name AS date_start,
                                    (SELECT name FROM res_currency_rate r2
                                     WHERE r2.name > r.name AND
                                           r2.currency_id = r.currency_id
                                     ORDER BY r2.name ASC
                                     LIMIT 1) AS date_end
                                FROM res_currency_rate r
                                )
                      SELECT SUM(price_total * cr.rate) as total
                        FROM account_invoice_report account_invoice_report, currency_rate cr
                       WHERE %s
                         AND cr.currency_id = %%s
                         AND (COALESCE(account_invoice_report.date, NOW()) >= cr.date_start)
                         AND (COALESCE(account_invoice_report.date, NOW()) < cr.date_end OR cr.date_end IS NULL)
                    """ % where_clause

            # price_total is in the currency with rate = 1
            # total_invoice should be displayed in the current user's currency
            cr.execute(query, where_clause_params + [user_currency_id])
            result[partner_id] = cr.fetchone()[0]

        return result

    def _get_amounts_and_date(self, cr, uid, ids, name, arg, context=None):
        '''
        Function that computes values for the followup functional fields. Note that 'payment_amount_due'
        is similar to 'credit' field on res.partner except it filters on user's company.
        '''
        res = super(ResPartner, self)._get_amounts_and_date(cr, uid, ids, name, arg, context=context)
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        current_date = fields2.date.context_today(self, cr, uid, context=context)
        for partner in self.browse(cr, uid, ids, context=context):
            if partner.supplier:
                worst_due_date = False
                amount_due = amount_overdue = 0.0
                for aml in partner.unreconciled_purchase_aml_ids:
                    if aml.company_id == company:
                        date_maturity = aml.date_maturity or aml.date
                        if not worst_due_date or date_maturity < worst_due_date:
                            worst_due_date = date_maturity
                        amount_due += aml.result
                        if date_maturity <= current_date:
                            amount_overdue += aml.result
                res[partner.id] = {'payment_amount_due': amount_due,
                                   'payment_amount_overdue': amount_overdue,
                                   'payment_earliest_due_date': worst_due_date}
        return res

    def _payment_due_search(self, cr, uid, obj, name, args, context=None):
        res = super(ResPartner, self)._payment_due_search(cr, uid, obj, name, args, context=context)
        return res

    _columns = {
        'total_invoiced_real': fields2.function(_invoice_total_real, string="Total Invoiced", type='float',
                                         groups='account.group_account_invoice'),
        'supplier_all_invoice_count': fields2.function(_purchase_invoice_count, string='# Supplier Invoices',
                                                       type='integer'),
        'payment_amount_due': fields2.function(_get_amounts_and_date,
                                              type='float', string="Amount Due",
                                              store=False, multi="followup",
                                              fnct_search=_payment_due_search),
    }

    @api.one
    def _get_products_sold(self):
        lines = self.env["sale.order.line"].read_group([('order_partner_id',
                                                         '=', self.id)],
                                                       ['product_id'],
                                                       groupby="product_id")
        self.sale_product_count = len(lines)

    @api.one
    def _sale_order_count(self):
        self.sale_order_count = len(self.env["sale.order"].
                                    search([('partner_id', 'child_of',
                                             [self.id]),
                                            ('state', 'not in',
                                             ['draft', 'cancel', 'sent'])]))

    @api.one
    def _get_growth_rate(self):
        if self.customer:
            search_date_180 = (date.today() - relativedelta(days=180)).\
                strftime("%Y-%m-%d")
            invoiced_180 = self.with_context(date_from=search_date_180).\
                browse(self.id).total_invoiced_real
            diary_invoice = invoiced_180 / 180.0
            goal = diary_invoice * 15.0
            if goal:
                search_date_15 = (date.today() - relativedelta(days=15)).\
                    strftime("%Y-%m-%d")
                invoiced_15 = self.with_context(date_from=search_date_15).\
                    browse(self.id).total_invoiced_real
                self.growth_rate = invoiced_15 / goal

    @api.one
    def _get_average_margin(self):
        if self.customer:
            margin_avg = 0.0
            total_price = 0.0
            total_cost = 0.0

            d1 = datetime.strptime(datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d")
            final_date = d1.strftime("%Y-%m-%d")
            d2 = d1 - dateutil.relativedelta.relativedelta(months=3)
            start_date = d2.strftime("%Y-%m-%d")

            invoices = self.env['account.invoice'].search(
                [('commercial_partner_id', '=', self.id),
                 ('number', 'not like', '%_ef%'),
                 ('state', 'in', ['paid', 'history', 'open']),
                 ('date_invoice', '>=', start_date),
                 ('date_invoice', '<=', final_date)])

            invoices_line = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', invoices.ids)])

            for i_line in invoices_line:
                self.env.cr.execute("SELECT order_line_id from sale_order_line_invoice_rel" +
                                    " WHERE invoice_id = " + str(i_line.ids[0]))
                order_rel = self.env.cr.fetchone()
                order_line = self.env["sale.order.line"].browse(order_rel)

                if order_line:
                    o_line_data = order_line.read(['purchase_price'])[0]
                    total_price += i_line.quantity * i_line.price_unit * \
                                   ((100.0 - i_line.discount) / 100)
                    total_cost += i_line.quantity * o_line_data['purchase_price']

            if total_price:
                margin_avg = (1 - total_cost / total_price) * 100.0

            self.average_margin = margin_avg

    web = fields.Boolean("Web", help="Created from web", copy=False)
    email_web = fields.Char("Email Web")
    sale_product_count = fields.Integer(compute=_get_products_sold,
                                        string="# Products sold",
                                        readonly=True)
    sale_order_count = fields.Integer(compute="_sale_order_count",
                                      string='# of Sales Order')
    invoice_type_id = fields.Many2one('res.partner.invoice.type',
                                      'Invoice type')
    dropship = fields.Boolean("Dropship")
    send_followup_to_user = fields.Boolean("Send followup to sales agent")
    eur_currency = fields.Many2one('res.currency', default=lambda self: self.env.ref('base.EUR'))
    purchase_quantity = fields.Float('', compute='_get_purchased_quantity')
    att = fields.Char("A/A")
    growth_rate = fields.Float("Growth rate", readonly=True,
                               compute="_get_growth_rate")
    average_margin = fields.Float("Average Margin", readonly=True, compute="_get_average_margin")

    unreconciled_purchase_aml_ids = fields.One2many('account.move.line', 'partner_id',
                                           domain=['&', ('reconcile_id', '=', False), '&',
                                                   ('account_id.active', '=', True), '&',
                                                   ('account_id.type', '=', 'payable'), ('state', '!=', 'draft')])
    _sql_constraints = [
        ('email_web_uniq', 'unique(email_web)', 'Email web field, must be unique')
    ]

    @api.multi
    def _get_purchased_quantity(self):
        for partner in self:
            lines = self.env['purchase.order.line'].search(
                [('order_id.state', '=', 'approved'),
                 ('invoiced', '=', False),
                 ('order_id.partner_id', '=', partner.id)])
            purchases = self.env['purchase.order'].search([('id', 'in', lines.mapped('order_id.id'))])
            total = sum(purchases.mapped('amount_total'))
            partner.purchase_quantity = total

    @api.constrains('ref', 'is_company', 'active')
    def check_unique_ref(self):
        if self.is_company and self.active:
            ids = self.search([('ref', '=', self.ref),
                               ('is_company', '=', True),
                               ('id', '!=', self.id)])
            if ids:
                raise exceptions. \
                    ValidationError(_('Partner ref must be unique'))

    @api.constrains('child_ids', 'is_company', 'active')
    def check_unique_child_ids(self):
        if self.is_company and self.active:
            if not self.child_ids:
                raise exceptions. \
                    ValidationError(_('At least, a contact must be added'))

    @api.constrains('vat', 'is_company', 'supplier', 'customer', 'active')
    def check_unique_vat(self):
        if self.is_company and self.active:
            ids = self.search([('vat', '=', self.vat),
                               ('is_company', '=', True),
                               ('id', '!=', self.id),
                               ('supplier', '=', self.supplier),
                               ('customer', '=', self.customer)])
            if ids:
                raise exceptions. \
                    ValidationError(_('VAT must be unique'))

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if record.parent_id and not record.is_company and not record.dropship:
                name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res

    @api.model
    def create(self, vals):
        if vals.get('dropship', False):
            vals['active'] = False
        if 'web' in vals and not vals['web']:
            vals['email_web'] = None
        vals['date'] = fields.Date.today()
        return super(ResPartner, self).create(vals)

    @api.multi
    @api.constrains('web')
    def check_client_type(self):
        if self.web and self.prospective:
            raise ValidationError(_('The client is prospective. The client cannot be created on the web.'))
        else:
            return True

    @api.multi
    def write(self, vals):
        if vals.get('dropship', False):
            vals['active'] = False
        if 'web' in vals and not vals['web']:
            vals['email_web'] = None
        res = super(ResPartner, self).write(vals)
        if 'lang' in vals and not vals.get('lang', False):
            for partner in self:
                if partner.parent_id and partner.lang != partner.parent_id.lang:
                    partner.lang = partner.parent_id.lang
        return res

    def _all_lines_get_with_partner(self, cr, uid, partner, company_id, days):
        today = time.strftime('%Y-%m-%d')
        moveline_obj = self.pool['account.move.line']

        domain = [('partner_id', '=', partner.id),
                  ('account_id.type', '=', 'receivable'),
                  ('reconcile_id', '=', False),
                  ('state', '!=', 'draft'),
                  ('company_id', '=', company_id),
                  ('date_maturity', '>', today)]
        if days:
            formatted_date = datetime.strptime(today, "%Y-%m-%d")
            due_date = datetime. \
                strftime(formatted_date + timedelta(days=days), "%Y-%m-%d")
            domain.append(('date_maturity', '<=', due_date))

        moveline_ids = moveline_obj.search(cr, uid, domain)

        # lines_per_currency = {currency: [line data, ...], ...}
        lines_per_currency = defaultdict(list)
        for line in moveline_obj.browse(cr, uid, moveline_ids):
            currency = line.currency_id or line.company_id.currency_id
            invoice_obj = self.pool['account.invoice']
            if line.stored_invoice_id:
                invoice = invoice_obj.browse(cr, uid, line.stored_invoice_id[0].id)
                client_order_ref = invoice.invoice_line[0].move_id.procurement_id.sale_line_id.order_id.client_order_ref
                if not client_order_ref:
                    client_order_ref = ""
            else:
                client_order_ref = ""

            line_data = {
                'name': line.move_id.name,
                'ref': line.ref,
                'date': line.date,
                'date_maturity': line.date_maturity,
                'balance': line.amount_currency if currency != line.company_id.currency_id else line.debit - line.credit,
                'blocked': line.blocked,
                'currency_id': currency,
                'client_order_ref': client_order_ref,
            }
            lines_per_currency[currency].append(line_data)

        return [{'line': lines, 'currency': currency} for currency, lines in lines_per_currency.items()]

    def get_not_followup_table_html(self, cr, uid, ids, days=0, context=None):
        assert len(ids) == 1
        if context is None:
            context = {}
        partner = self.browse(cr, uid, ids[0], context=context).commercial_partner_id
        # copy the context to not change global context. Overwrite it because _() looks for the lang in local variable 'context'.
        # Set the language to use = the partner language
        context = dict(context, lang=partner.lang)
        followup_table = ''
        if partner.unreconciled_aml_ids:
            company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
            current_date = fields2.date.context_today(self, cr, uid, context=context)
            rml_parse = account_followup_print.report_rappel(cr, uid, "followup_rml_parser")
            final_res = self._all_lines_get_with_partner(cr, uid, partner, company.id, days=days)

            for currency_dict in final_res:
                currency = currency_dict.get('line', [{'currency_id': company.currency_id}])[0]['currency_id']
                followup_table += '''
                <table border="2" width=100%%>
                <tr>
                    <td>''' + _("Invoice Date") + '''</td>
                    <td>''' + _("Invoice No.") + '''</td>
                    <td>''' + _("Client Order Ref.") + '''</td>
                    <td>''' + _("Due Date") + '''</td>
                    <td>''' + _("Amount") + " (%s)" % (currency.symbol) + '''</td>
                </tr>
                '''
                total = 0
                for aml in currency_dict['line']:
                    block = aml['blocked'] and 'X' or ' '
                    total += aml['balance']
                    strbegin = "<TD>"
                    strend = "</TD>"
                    date = aml['date_maturity'] or aml['date']
                    followup_table += "<TR>" + strbegin + str(aml['date']) + strend +\
                                      strbegin + (aml['ref'] or '') + strend +\
                                      strbegin + (aml['client_order_ref'] or '') + strend +\
                                      strbegin + str(date) + strend + strbegin +\
                                      str(aml['balance']) + strend + "</TR>"

                total = reduce(lambda x, y: x + y['balance'], currency_dict['line'], 0.00)

                total = rml_parse.formatLang(total, dp='Account', currency_obj=currency)
                followup_table += '''<tr> </tr>
                                </table>
                                <strong><center style="font-size: 18px">''' + _("Amount not due") +\
                                  ''' : %s </center></strong>''' % (total)
        return followup_table

    def get_custom_followup_table_html(self, cr, uid, ids, context=None):
        """ Build the html tables to be included in emails send to partners,
            when reminding them their overdue invoices.
            :param ids: [id] of the partner for whom we are building the tables
            :rtype: string
        """
        assert len(ids) == 1
        if context is None:
            context = {}
        partner = self.browse(cr, uid, ids[0], context=context).commercial_partner_id
        #copy the context to not change global context. Overwrite it because _() looks for the lang in local variable 'context'.
        #Set the language to use = the partner language
        context = dict(context, lang=partner.lang)
        followup_table = ''
        if partner.unreconciled_aml_ids:
            company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
            current_date = fields2.date.context_today(self, cr, uid, context=context)
            rml_parse = account_followup_print.report_rappel(cr, uid, "followup_rml_parser")
            final_res = rml_parse._lines_get_with_partner(partner, company.id)

            for currency_dict in final_res:
                currency = currency_dict.get('line', [{'currency_id': company.currency_id}])[0]['currency_id']
                followup_table += '''
                <table border="2" width=100%%>
                <tr>
                    <td>''' + _("Invoice Date") + '''</td>
                    <td>''' + _("Invoice No.") + '''</td>
                    <td>''' + _("Client Order Ref.") + '''</td>
                    <td>''' + _("Due Date") + '''</td>
                    <td>''' + _("Amount") + " (%s)" % (currency.symbol) + '''</td>
                </tr>
                '''
                total = 0
                for aml in currency_dict['line']:
                    block = aml['blocked'] and 'X' or ' '
                    total += aml['balance']
                    strbegin = "<TD>"
                    strend = "</TD>"
                    date = aml['date_maturity'] or aml['date']
                    if date <= current_date and aml['balance'] > 0:
                        strbegin = "<TD><B>"
                        strend = "</B></TD>"
                    followup_table += "<TR>" + strbegin + str(aml['date']) + strend +\
                                      strbegin + (aml['ref'] or '') + strend +\
                                      strbegin + (aml['client_order_ref'] or '') + strend +\
                                      strbegin + str(date) + strend +\
                                      strbegin + str(aml['balance']) + strend + "</TR>"

                total = reduce(lambda x, y: x+y['balance'], currency_dict['line'], 0.00)

                total = rml_parse.formatLang(total, dp='Account', currency_obj=currency)
                followup_table += '''<tr> </tr>
                                </table>
                                <strong> <center style="font-size: 18px">''' + _("Amount due") \
                                  + ''' : %s </center> </strong>''' % (total)
        return followup_table


class rappel_calculated(models.Model):

    _inherit = 'rappel.calculated'

    goal_percentage = fields.Float("Goal Percentage")


class ResPartnerRappelRel(models.Model):

    _inherit = "res.partner.rappel.rel"

    @api.multi
    def _get_invoices(self, period, products):
        res = super(ResPartnerRappelRel, self)._get_invoices(period, products)

        self.ensure_one()
        invoices = self.env['account.invoice'].search(
            [('type', '=', 'out_invoice'),
             ('date_invoice', '>=', period[0]),
             ('date_invoice', '<=', period[1]),
             ('state', 'in', ['open', 'paid']),
             ('commercial_partner_id', '=', self.partner_id.id)])
        refunds = self.env['account.invoice'].search(
            [('type', '=', 'out_refund'),
             ('date_invoice', '>=', period[0]),
             ('date_invoice', '<=', period[1]),
             ('state', 'in', ['open', 'paid']),
             ('commercial_partner_id', '=', self.partner_id.id)])

        # se buscan las rectificativas
        refund_lines = self.env['account.invoice.line'].search(
            [('invoice_id', 'in', [x.id for x in refunds]),
             ('product_id', 'in', products),
             ('no_rappel', '=', False)])
        invoice_lines = self.env['account.invoice.line'].search(
            [('invoice_id', 'in', [x.id for x in invoices]),
             ('product_id', 'in', products),
             ('no_rappel', '=', False)])

        return invoice_lines, refund_lines

    @api.model
    def compute(self, period, invoice_lines, refund_lines, tmp_model=False):
        goal_percentage = 0
        for rappel in self:
            rappel_info = {'rappel_id': rappel.rappel_id.id,
                           'partner_id': rappel.partner_id.id,
                           'date_start': period[0],
                           'amount': 0.0,
                           'date_end': period[1]}
            total_rappel = 0.0
            if rappel.rappel_id.calc_mode == 'fixed':
                if rappel.rappel_id.calc_amount == 'qty':
                    total_rappel = rappel.rappel_id.fix_qty
                else:
                    total = sum([x.price_subtotal for x in invoice_lines]) - \
                        sum([x.price_subtotal for x in refund_lines])
                    if total:
                        total_rappel = total * rappel.rappel_id.fix_qty / 100.0
                    rappel_info["curr_qty"] = total

                rappel_info['amount'] = total_rappel
            else:
                field = ''
                if rappel.rappel_id.qty_type == 'value':
                    field = 'price_subtotal'
                else:
                    field = 'quantity'
                total = sum([x[field] for x in invoice_lines]) - \
                    sum([x[field] for x in refund_lines])
                rappel_info["curr_qty"] = total
                if total:
                    section = self.env['rappel.section'].search(
                        [('rappel_id', '=', rappel.rappel_id.id),
                         ('rappel_from', '<=', total),
                         ('rappel_until', '>=', total)])
                    if not section:
                        section = self.env['rappel.section'].search(
                            [('rappel_id', '=', rappel.rappel_id.id),
                             ('rappel_from', '<=', total),
                             ('rappel_until', '=', False)],
                            order='rappel_from desc', limit=1)
                    if section:
                        goal_percentage = 100
                    else:
                        # Check if goal percentage is more than 80% to get the rappel
                        section = self.env['rappel.section'].search(
                            [('rappel_id', '=', rappel.rappel_id.id),
                             ('rappel_from', '<=', total/0.8),
                             ('rappel_from', '>', total)])
                        if section.rappel_from:
                            goal_percentage = (total / section.rappel_from) * 100
                        else:
                            goal_percentage = 0

                    if not section:
                        rappel_info['amount'] = 0.0
                    else:
                        rappel_info['section_id'] = section.id
                        section = section[0]
                        if rappel.rappel_id.calc_amount == 'qty':
                            total_rappel = section.percent
                        else:
                            total_rappel = total * \
                                section.percent / 100.0
                            rappel_info['amount'] = total_rappel
                else:
                    rappel_info['amount'] = 0.0

            if period[1] <= fields.Date.from_string(fields.Date.today()):
                if total_rappel:
                    self.env['rappel.calculated'].create({
                        'partner_id': rappel.partner_id.id,
                        'date_start': period[0],
                        'date_end': period[1],
                        'quantity': total_rappel,
                        'rappel_id': rappel.rappel_id.id,
                        'goal_percentage': goal_percentage
                    })
                rappel.last_settlement_date = period[1]
            else:
                if tmp_model and rappel_info:
                    self.env['rappel.current.info'].create(rappel_info)

        return True

