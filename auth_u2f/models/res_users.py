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

from odoo import api, fields, models
from odoo.http import request
from odoo.addons.auth_u2f.models.http import U2FAuthenticationError

import logging
from u2flib_server.u2f import (begin_registration, begin_authentication,
                               complete_authentication)

from odoo.addons.base.res import res_users
res_users.USER_PRIVATE_FIELDS.append('u2f_device_ids')

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    u2f_device_ids = fields.One2many('u2f.device', 'user_id', string='U2F devices')

    def _u2f_get_device(self):
        self.ensure_one()
        default_devices = self.u2f_device_ids.filtered('default')
        return default_devices[0] if default_devices else False

    @api.model
    def u2f_get_registration_challenge(self):
        user = self.env.user
        print(user.login)
        baseurl = user.env['ir.config_parameter'].sudo().get_param('web.base.url')
        already_registered_u2f_devices = user.u2f_device_ids.mapped('json')
        challenge = begin_registration(baseurl, already_registered_u2f_devices)
        request.session.u2f_last_registration_challenge = challenge.json

        return challenge

    def _u2f_get_login_challenge(self):
        baseurl = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        challenge = begin_authentication(baseurl, [self._u2f_get_device().json])
        return challenge

    def u2f_check_credentials(self, last_challenge, last_response):
        if self._u2f_get_device():
            baseurl = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            try:
                device, c, t = complete_authentication(last_challenge, last_response, [baseurl])
            except Exception:
                _logger.info('Exception during U2F authentication.', exc_info=True)
                raise U2FAuthenticationError()

            _logger.debug('Successful U2F auth with: %s, %s, %s', device, c, t)
        return True
