# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m, transaction
from django.utils.translation import ugettext_lazy as _

from ..exceptions import AbilityError
from ..utils.model import model_fields
from . import appmethod, WeChatApp, WeChatModel


class Template(WeChatModel):
    app = m.ForeignKey(
        WeChatApp, related_name="templates", on_delete=m.CASCADE)
    template_id = m.CharField(_("template_id"), max_length=64)
    title = m.CharField(_("title"), max_length=32)
    content = m.TextField(_("content"))
    example = m.TextField(_("example"), blank=True, null=True)

    primary_industry = m.CharField(
        _("primary industry"), max_length=64, blank=True, null=True)
    deputy_industry = m.CharField(
        _("deputy industry"), max_length=64, blank=True, null=True)

    comment = m.TextField(_("remark"), blank=True, null=True)
    created_at = m.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("template")
        verbose_name_plural = _("templates")

        unique_together = ("app", "template_id")

    @classmethod
    @appmethod("sync_templates")
    def sync(cls, app):
        """
        同步微信模板
        :type app: wechat_django.models.WeChatApp
        """
        if app.type == WeChatApp.Type.SERVICEAPP:
            resp = app.client.template.get_all_private_template()
            templates = resp["template_list"]
        elif app.type == WeChatApp.Type.MINIPROGRAM:
            templates = list(cls._iter_wxa_templates(app))
        else:
            raise AbilityError(AbilityError.TEMPLATE, "")

        with transaction.atomic():
            (app.templates
                .exclude(template_id__in=[t["template_id"] for t in templates])
                .delete())
            rv = []
            for t in templates:
                defaults = dict(app=app)
                defaults.update({
                    k: v for k, v in t.items() if k in model_fields(cls)})
                template = cls.objects.update_or_create(
                    app=app, template_id=t["template_id"],
                    defaults=defaults
                )[0]
                rv.append(template)
            return rv

    def send(
        self, user, data=None, url=None, appid=None, pagepath=None, page=None,
        form_id=None, emphasis_keyword=None, **kwargs):
        """
        发送模板消息
        :param user: 用户openid或用户对象
        :type user: wechat_django.models.WeChatUser or str
        :param data: 接口的data字段
        :param url: 跳转的url 仅服务号有效
        :param appid: 跳转小程序的appid 仅服务号有效
        :param pagepath: 跳转小程序的具体页
        :param page: 跳转小程序的具体页 pagepath的别名
        :param form_id: 发送模板消息需要的form_id 仅小程序有效
        :param emphasis_keyword: 模板需要放大的关键词，不填则默认无放大
        :param kwargs: 接口的data字段 可直接传字符串 当data未填写时 使用该字段
        """
        from . import WeChatUser

        openid = user.openid if isinstance(user, WeChatUser) else user
        pagepath = pagepath or page
        if not data:
            data = {
                k: v if isinstance(v, dict) else dict(value=v)
                for k, v in kwargs.items()
            }

        if self.app.type == WeChatApp.Type.SERVICEAPP:
            return self._send_service(openid, data, url, appid, pagepath)
        elif self.app.type == WeChatApp.Type.MINIPROGRAM:
            return self._send_miniprogram(
                openid, data, form_id, pagepath, emphasis_keyword)
        else:
            raise AbilityError(AbilityError.TEMPLATE, "")

    def _send_service(
        self, openid, data, url=None, appid=None, pagepath=None):
        """发送服务号模板消息"""
        miniprogram = dict(
            appid=appid,
            pagepath=pagepath
        ) if appid else None
        return self.app.client.message.send_template(
            openid, self.template_id, data, url, miniprogram)

    def _send_miniprogram(
        self, openid, data, form_id, page=None, emphasis_keyword=None):
        """发送小程序模板消息"""
        return self.app.client.wxa.send_template_message(
            openid, self.template_id, data, form_id, page=page,
            emphasis_keyword=emphasis_keyword)

    @staticmethod
    def _iter_wxa_templates(app):
        while True:
            offset = 0
            count = 20
            templates = app.client.wxa.list_templates(offset, count)
            if not templates:
                return
            for template in templates:
                yield template
            if len(templates) < count:
                # 未满说明没有下一页了
                return
            offset += count

    def __str__(self):
        return "{title} ({template_id})".format(
            title=self.title, template_id=self.template_id)
