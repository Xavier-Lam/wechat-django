from setuptools import find_packages, setup

import os
import re
from setuptools import find_packages, setup


package = dict()

with open(os.path.join("wechat_django", "__init__.py"), "r") as f:
    lines = f.readlines()
    for line in lines:
        match = re.match(r"(__\w+?__)\s*=\s*(.+)$", line)
        if match:
            package[match.group(1)] = eval(match.group(2))

with open("README.md", "rb") as f:
    long_description = f.read().decode("utf-8")

with open("requirements.txt") as f:
    requirements = [l for l in f.read().splitlines() if l]

with open("requirements.unittest.txt") as f:
    test_requirements = [l for l in f.read().splitlines() if l]


setup(
    name=package["__title__"],
    version=package["__version__"],
    author=package["__author__"],
    author_email=package["__author_email__"],
    url=package["__url__"],
    packages=find_packages(),
    keywords=",".join(["WeChat", "weixin", "wx", "WeChatPay",
                       "micromessenger", "django", "微信", "微信支付"]),
    description=package["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    include_package_data=True,
    tests_require=test_requirements,
    test_suite="runtests.main",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ]
)