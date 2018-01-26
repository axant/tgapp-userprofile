# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import TGController, expose, flash, require, url, predicates,\
        lurl, request, redirect, validate, config, override_template
from tg.util import Bunch
from tg.i18n import ugettext as _, lazy_ugettext as l_

from tw2.core import ValidationError

from tgext.pluggable import app_model, plug_url, primary_key
from userprofile.lib import create_user_form, get_user_data, get_profile_css, \
                            update_user_data, create_change_password_form


edit_password_form = create_change_password_form()


class RootController(TGController):
    allow_only = predicates.not_anonymous()

    @expose('userprofile.templates.index')
    def _default(self):
        user = request.identity['user']
        user_data, user_avatar = get_user_data(user)
        user_displayname = user_data.pop('display_name', (None, 'Unknown'))
        user_partial = config['_pluggable_userprofile_config'].get('user_partial')
        return dict(user=user,
                    user_data=user_data,
                    user_avatar=user_avatar,
                    user_displayname=user_displayname,
                    profile_css=get_profile_css(config),
                    user_partial=user_partial)

    @expose('userprofile.templates.edit')
    def edit(self):
        user = request.identity['user']
        user_data, user_avatar = get_user_data(user)
        user_data = Bunch(((fieldid, info[1]) for fieldid, info in user_data.items()))
        return dict(user=user_data, profile_css=get_profile_css(config),
                    user_avatar=user_avatar,
                    form=create_user_form(user))

    @expose()
    def save(self, **kw):
        user = request.identity['user']

        try:
            form = create_user_form(user)
            form.validate(kw)
        except ValidationError:
            override_template(self.save, 'kajiki:userprofile.templates.edit')
            user_data, user_avatar = get_user_data(user)
            return dict(user={},
                        profile_css=get_profile_css(config),
                        user_avatar=user_avatar,
                        form=form)

        profile_save = getattr(user, 'save_profile', None)
        if not profile_save:
            profile_save = update_user_data
        profile_save(user, kw)
        flash(_('Profile successfully updated'))
        return redirect(plug_url('userprofile', '/'))

    @expose('userprofile.templates.chpasswd')
    def chpasswd(self, **kw):
        return dict(profile_css=get_profile_css(config),
                    form=edit_password_form)

    @expose()
    @validate(edit_password_form, error_handler=chpasswd)
    def save_password(self, password, verify_password):
        user = request.identity['user']
        user.password = password
        flash(_('Password successfully changed'))
        return redirect(plug_url('userprofile', '/'))
