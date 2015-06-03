# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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


from openerp import models, fields, api


class location_moves(models.TransientModel):

    _name = 'location.moves'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    qty = fields.Float('Qty', required=True)
    move_type = fields.Selection(
        [('pantry_kitchen', 'Pantry -> Kitchen'),
         ('kitchen_cooked', 'Kitchen -> Coocked'),
         ('kitchen_nursing', 'Kitchen -> Nursing'),
         ('nursing_damaged', 'Nursing -> Damaged'),
         ('nursing_coocked', 'Nursing -> Coocked')],
        'Move type', required=True)

    @api.one
    def create_moves(self):
        loc_obj = self.env['stock.location']
        types = {
            'pantry_kitchen': loc_obj.move_pantry_kitchen,
            'kitchen_cooked': loc_obj.move_kitchen_coocked,
            'kitchen_nursing': loc_obj.move_kitchen_nursing,
            'nursing_damaged': loc_obj.move_nursing_damaged,
            'nursing_coocked': loc_obj.move_nursing_coocked,
        }
        types[self.move_type](self.product_id.id, self.qty)
        return True
