# 网页开发

## jssdk

首先你需要自行引入微信的js文件

    <script src="//res.wx.qq.com/open/js/jweixin-1.4.0.js"></script>

在模板文件中加入

    <script src="{% url 'wechat_django:jsconfig' 'debug' %}?jsApiList=onMenuShareTimeline,onMenuShareAppMessage&debug=1"></script>

如果你没有使用模板,默认地址应该是

    <script src="/wechat/{{yourappname}}/wx.jsconfig.js?jsApiList=onMenuShareTimeline,onMenuShareAppMessage&debug=1"></script>

其中,jsApiList参数传入需要使用的JS接口列表,debug如填写且settings.py的DEBUG为真值,则会配置调试模式.

以下是上述示例js的输出结果:

    wx.config(JSON.parse('{"debug": true, "appId": "appId", "timestamp": 1575299361, "nonceStr": "95b992c5263b4c6689fc7fdcb6f1ddc8", "signature": "8cb73b3536ee3b787f63d6e6cf9ddd1f06afd94a", "jsApiList": ["onMenuShareTimeline", "onMenuShareAppMessage"]}'));