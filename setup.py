from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = [l for l in f.read().splitlines() if l]
with open("requirements.dev.txt") as f:
    dev_requirements = [l for l in f.read().splitlines() if l]

setup(
    name='wechat-django',
    version='1.7.6',
    author='Xavier-Lam',
    author_email='Lam.Xavier@hotmail.com',
    url='https://github.com/Xavier-Lam/django-wechat',
    packages=find_packages(),
    keywords='WeChat, weixin, wx, micromessenger',
    description='WeChat Django Extension',
    install_requires=requirements,
    include_package_data=True,
    # tests_require=dev_requirements,
    classifiers=[
        # 'Development Status :: 5 - Production/Stable',
        # 'License :: OSI Approved :: MIT License',
        # 'Operating System :: Windows',
        # 'Operating System :: MacOS',
        # 'Operating System :: POSIX',
        # 'Operating System :: POSIX :: Linux',
        # 'Programming Language :: Python',
        # 'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
        # 'Programming Language :: Python :: 3.6',
        # 'Programming Language :: Python :: 3.7',
        # 'Programming Language :: Python :: Implementation :: CPython',
        # 'Intended Audience :: Developers',
        # 'Topic :: Software Development :: Libraries',
        # 'Topic :: Software Development :: Libraries :: Python Modules',
        # 'Topic :: Utilities',
    ],
    extras_require={
        'cryptography': ["cryptography"],
        'pycrypto': ["pycryptodome"],
    }
)