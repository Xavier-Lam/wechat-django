# WeChat-Django

[![PyPI](https://img.shields.io/pypi/v/wechat-django.svg)](https://pypi.org/project/wechat-django)
[![Build Status](https://travis-ci.org/Xavier-Lam/wechat-django.svg?branch=master)](https://travis-ci.org/Xavier-Lam/wechat-django)
[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)](https://en.cryptobadges.io/donate/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)

项目官方地址: https://github.com/Xavier-Lam/wechat-django

本拓展基于[wechatpy](https://github.com/jxtech/wechatpy) ,支持的最低django版本为2.2.

## Installation

## Configurations

## Guide
### 消息推送与处理
> 在单元测试过程中,我们发现使用message_handlers时复合使用以下几个参数时存在较大风险
> * `pass_through`为`True`且`ignore_errors`为`False`: 此时你可能期望完整执行所有处理器,但是由于前序处理器抛出了异常,后续处理器将无法继续执行,前序处理器业务逻辑已完成执行,用户无法收到任何响应
> * `match_all`为`True`,match_all参数为真时将捕获所有通过的请求,因为第三方平台通知与一般通知响应差异较大,如处理器内处理不当,容易抛出异常,可能与你的业务逻辑设计初衷违背.
> * `match_all`为`True`且`pass_through`为`False`并且处理器有较高`weight`或较早注册:处理器会拦截消息,处理并响应,造成后续处理器失效