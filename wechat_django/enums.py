class AppType:
    UNKNOWN = 0x00
    OFFICIALACCOUNT = 0x01
    MINIPROGRAM = 0x02
    PAY = 0x04
    THIRDPARTYPLATFORM = 0x08
    MERCHANTPAY = 0x10
    HOSTED = 0x20
    WEBAPP = 0x40


class EncryptStrategy:
    ENCRYPTED = 'encrypted'
    PLAIN = 'plain'
