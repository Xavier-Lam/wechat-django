# flake8: noqa

from .base import Application
from .ordinaryapplication import OrdinaryApplication
from .miniprogram import MiniProgramApplication
from .officialaccount import OfficialAccountApplication
from .pay import HostedPayApplication, PayApplication, PayMerchant
from .thirdpartyplatform import (AuthorizerApplication,
                                 MiniProgramAuthorizerApplication,
                                 OfficialAccountAuthorizerApplication,
                                 ThirdPartyPlatform)
