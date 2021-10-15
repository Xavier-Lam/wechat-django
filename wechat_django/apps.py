from django.apps import AppConfig
import object_tool

from wechat_django.core import settings


class WeChatDjangoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wechat_django'
    verbose_name = "WeChat Django"

    def ready(self):
        object_tool.ObjectToolConfig.register()

        super().ready()

        from django.contrib.admin import site
        from . import admin, models, views
        from .sites import default_site

        if settings.get("ENABLE_MERCHANT"):
            site.register(models.apps.PayMerchant,
                          admin.app.payapplication.PayMerchantAdmin)
            site.register(models.apps.HostedPayApplication,
                          admin.app.payapplication.HostedPayAdmin)

        if settings.get("ENABLE_THIRDPARTYPLATFORM"):
            default_site.register(views.messagehandler.AuthorizerHandler)
            default_site.register(
                views.thirdpartyplatform.ThirdPartyPlatformAuth)

            site.register(
                models.apps.ThirdPartyPlatform,
                admin.app.thirdpartyplatform.ThirdPartyPlatformApplicationAdmin
            )
            site.register(
                models.apps.AuthorizerApplication,
                admin.app.thirdpartyplatform.AuthorizerApplicationAdmin)

        if settings.get("ENABLE_WECHATPAY"):
            site.register(models.apps.PayApplication,
                          admin.app.payapplication.PayApplicationAdmin)
