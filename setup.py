# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import find_packages, setup

import wechat_django

with open("readme.md", "rb") as f:
    long_description = f.read().decode("utf-8")

with open("requirements.txt") as f:
    requirements = [l for l in f.read().splitlines() if l]

setup(
    name=wechat_django.__title__,
    version=wechat_django.__version__,
    author=wechat_django.__author__,
    author_email=wechat_django.__author_email__,
    url=wechat_django.__url__,
    packages=find_packages(),
    keywords="WeChat, weixin, wx, micromessenger, 微信, django",
    description=wechat_django.__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    include_package_data=True,
    tests_require=requirements + ["cryptography>=2.5", "httmock==1.2.6"],
    test_suite="runtests.main",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: Chinese (Traditional)",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
    extras_require={
        "cryptography": ["cryptography"],
        "pycrypto": ["pycryptodome"],
    }
)
