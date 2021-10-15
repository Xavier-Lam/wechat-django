================
Message Handler
================

.. module:: wechat_django.messagehandler.base


Base
------------
PlainTextReply
~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: PlainTextReply
   :members:


reply2send
~~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: reply2send


MessageMatcher
~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: MessageMatcher
   :members:
   :undoc-members:


MessageResponder
~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: MessageResponder
   :members:
   :undoc-members:


MessageHandler
~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: MessageHandler
   :members:
   :undoc-members:


MessageHandlerCollection
~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: MessageHandlerCollection
   :members: register, register_matchers, handle
   :undoc-members:



.. module:: wechat_django.messagehandler.builtins


Builtin handlers
-------------------


builtin_handlers
~~~~~~~~~~~~~~~~~~~~~~~
.. autodata:: builtin_handlers
   :annotation:


subscribe
~~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: subscribe


thirdpartyplatform_ticket
~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: thirdpartyplatform_ticket


thirdpartyplatform_authorize
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: thirdpartyplatform_authorize


thirdpartyplatform_unauthorize
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: thirdpartyplatform_unauthorize