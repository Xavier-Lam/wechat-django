from collections.abc import Iterable
from copy import deepcopy

from wechatpy import replies


class PlainTextReply(replies.TextReply):
    """Non-XML text reply"""
    def __init__(self, content):
        super().__init__(content=content)

    def render(self):
        """
        Return the content string directly instead of return an XML string
        """
        return self.content


def to_reply(reply):
    if not reply:
        return replies.EmptyReply()
    elif not isinstance(reply, replies.BaseReply):
        return replies.TextReply(content=str(reply))
    return reply


def reply2send(reply):
    """Translate a positive reply to an active reply"""
    reply = to_reply(reply)
    if isinstance(reply, replies.EmptyReply):
        return None, None
    type = ""
    kwargs = dict(user_id=reply.target)
    if isinstance(reply, replies.ArticlesReply):
        kwargs["articles"] = deepcopy(reply.articles)
        for article in kwargs["articles"]:
            article["picurl"] = article["image"]
            del article["image"]
        type = "articles"
    elif isinstance(reply, replies.MusicReply):
        kwargs["url"] = reply.music_url
        kwargs["hq_url"] = reply.hq_music_url
        kwargs["thumb_media_id"] = reply.thumb_media_id
        kwargs["title"] = reply.title
        kwargs["description"] = reply.description
    elif isinstance(reply, replies.VideoReply):
        kwargs["media_id"] = reply.media_id
        kwargs["title"] = reply.title
        kwargs["description"] = reply.description
    elif isinstance(reply, (replies.ImageReply, replies.VoiceReply)):
        kwargs["media_id"] = reply.media_id
    elif isinstance(reply, replies.TextReply):
        kwargs["content"] = reply.content
    else:
        raise NotImplementedError
    type = type or reply.type
    funcname = "send_" + type
    return funcname, kwargs


class MessageMatcher:
    def __init__(self, app_names=None, query=None, matcher=None,
                 match_all=False):
        app_names = app_names or tuple()
        if isinstance(app_names, str):
            app_names = (app_names,)
        self.app_names = app_names
        self.query = query or {}
        self.matcher = matcher
        self.match_all = match_all

    def match(self, message, request, *args, **kwargs):
        result = None
        if self.app_names:
            if request.wechat_app.name in self.app_names:
                result = True
            else:
                return False
        if self.query:
            for key, value in self.query.items():
                if getattr(message, key, None) != value:
                    return False
            result = True
        if getattr(self, "matcher"):
            try:
                result = self.matcher(message, request, *args, **kwargs)
            except NotImplementedError:
                pass
            except Exception:
                # matcher抛出异常则认为未匹配到
                return False
        return self.match_all if result is None else result

    def matcher(self, message, request, *args, **kwargs):
        raise NotImplementedError


class MessageResponder:
    def __init__(self, *, handler=None, ignore_exceptions=False):
        self.ignore_exceptions = ignore_exceptions
        if handler:
            self.handler = handler

    def handler(self, message, request, *args, **kwargs):
        """
        :param message: The message received
        :type message: wechatpy.messages.BaseMessage
        :param request: The comming request object
        :type request: django.http.Request
        """
        raise NotImplementedError

    def __call__(self, message, request, *args, **kwargs):
        try:
            reply = self.handler(message, request, *args, **kwargs)
            return to_reply(reply)
        except Exception:
            if not self.ignore_exceptions:
                raise
            return replies.EmptyReply()


class MessageHandler:
    def __init__(self, matchers, responders, *, weight=0, pass_through=False,
                 ignore_exceptions=False):
        if not isinstance(matchers, Iterable):
            matchers = (matchers,)
        if not isinstance(responders, Iterable):
            responders = (responders,)
        self.matchers = matchers
        self.responders = tuple(
            responder if isinstance(responder, MessageResponder) else
            MessageResponder(handler=responder,
                             ignore_exceptions=ignore_exceptions)
            for responder in responders
        )
        self.weight = weight
        self.pass_through = pass_through
        self.ignore_exceptions = ignore_exceptions

    def match(self, message, request, *args, **kwargs):
        for matcher in self.matchers:
            if matcher.match(message, request, *args, **kwargs):
                return matcher

    def reply(self, message, request, *args, **kwargs):
        responses = []
        for responder in self.responders:
            try:
                reply = responder(message, request, *args, **kwargs)
                if not isinstance(reply, replies.EmptyReply):
                    responses.append(reply)
            except Exception:
                if not self.ignore_exceptions:
                    raise
        return tuple(responses)

    def __call__(self, message, request, *args, **kwargs):
        if self.match(message, request, *args, **kwargs):
            return self.reply(message, request, *args, **kwargs)
        return tuple()


class MessageHandlerCollection(list):
    DEFAULT_PASSTHROUGH = False
    DEFAULT_WEIGHT = 0

    def __init__(self, *items):
        super().__init__()
        for item in items:
            self.extend(item)

    def register(self, *, app_names=None, query=None, matcher=None,
                 weight=None, match_all=False, pass_through=None,
                 ignore_exceptions=False):
        """
        Register a message handler

        :param app_names: The names of the applications who receive the
                          message
        :param query: Query conditions dict, like
                      `{"type": "text", "content": "a"}`
        :param weight: Higher weight means this handler will be matched
                       earlier
        :param match_all: True if all messages should be handled by this
                          handler
        :param pass_through: True if the message already matched this handler
                             keep looking for next handler
        :param ignore_exceptions: True if you want to ignore an exception
                                  occurred in this handler and do not
                                  interrupt execution of following code

        Example::

            from wechat_django import message_handlers
            from wechatpy import create_reply


            @message_handlers(app_names="app_name", query={"type": "text"},
                              pass_through=True)
            def your_handler(message, request, *args, **kwargs):
                return create_reply("success", message=message)
        """

        if pass_through is None:
            pass_through = self.DEFAULT_PASSTHROUGH
        weight = self.DEFAULT_WEIGHT if weight is None else weight
        matcher = MessageMatcher(app_names=app_names, query=query,
                                 matcher=matcher, match_all=match_all)

        def decorator(func):
            self.register_matchers(matcher, func, weight=weight,
                                   pass_through=pass_through,
                                   ignore_exceptions=ignore_exceptions)
            return func

        return decorator

    def register_matchers(self, matchers, responders, *, weight=0,
                          pass_through=False, ignore_exceptions=False):
        handler = MessageHandler(matchers, responders,
                                 weight=weight,
                                 pass_through=pass_through,
                                 ignore_exceptions=ignore_exceptions)
        self.append(handler)

    def handle(self, message, request, *args, **kwargs):
        rv = []
        for handler in self:
            replies = handler(message, request, *args, **kwargs)
            if replies:
                rv.extend(replies)
                if not handler.pass_through:
                    break
        return tuple(rv)

    def append(self, obj):
        idx = next(
            (i for i, v in enumerate(self) if obj.weight > v.weight),
            len(self))
        super().insert(idx, obj)

    def extend(self, items):
        for item in items:
            self.append(item)

    def insert(self, idx, obj):
        raise NotImplementedError

    def reverse(self):
        raise NotImplementedError

    def sort(self, *args, **kwargs):
        raise NotImplementedError

    __call__ = register
