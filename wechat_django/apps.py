from django.apps import AppConfig
import object_tool

from wechat_django.utils.django import get_setting


class WeChatDjangoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wechat_django'
    verbose_name = "WeChat Django"

    def ready(self):
        object_tool.ObjectToolConfig.register()

        super().ready()

        from django.contrib.admin import site
        from . import admin, models

        if get_setting("ADMIN_SHOW_MERCHANT"):
            site.register(models.apps.PayMerchant,
                          admin.app.payapplication.PayMerchantAdmin)
            site.register(models.apps.HostedPayApplication,
                          admin.app.payapplication.HostedPayAdmin)
        if get_setting("ADMIN_SHOW_THIRDPARTYPLATFORM"):
            site.register(
                models.apps.ThirdPartyPlatform,
                admin.app.thirdpartyplatform.ThirdPartyPlatformApplicationAdmin)
            site.register(
                models.apps.AuthorizerApplication,
                admin.app.thirdpartyplatform.AuthorizerApplicationAdmin)
        if get_setting("ADMIN_SHOW_WECHATPAY"):
            site.register(models.apps.PayApplication,
                          admin.app.payapplication.PayApplicationAdmin)
