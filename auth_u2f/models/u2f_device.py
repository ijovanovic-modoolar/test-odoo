# coding: utf-8
# Copyright (C) 2017 Joren Van Onder

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

from u2flib_server.u2f import complete_registration

from odoo import api, fields, models
from odoo.http import request


class U2FDevice(models.Model):
    _name = 'u2f.device'

    name = fields.Char(required=True)
    json = fields.Char(required=True,
                       string='Scan', help='Technical data returned by u2flib or the browser')
    user_id = fields.Many2one('res.users', required=True, readonly=True)
    default = fields.Boolean(help='Device used during login!', readonly=True)
    new_field = fields.Char('New field')
    new_field2 = fields.Char('New field2')

    @api.model
    def create(self, vals):
        res = super(U2FDevice, self).create(vals)
        res._register_device()
        res.action_make_default()
        return res

    def _register_device(self):
        for device in self:
            baseurl = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            registration_data, cert = complete_registration(request.session.u2f_last_registration_challenge, device.json, [baseurl])
            device.json = registration_data.json
            del request.session['u2f_last_registration_challenge']

        return True

    def action_make_default(self):
        self.ensure_one()
        self.user_id.u2f_device_ids.write({'default': False})
        self.default = True

        return True
