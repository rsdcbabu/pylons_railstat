try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='railstat',
    version='0.1',
    description='Application to show train location status',
    author='Deepak Chand Babu',
    author_email='rsdcbabu@gmail.com',
    url='http://www.rsdcbabu.com',
    install_requires=[
        "Pylons>=1.0.1rc1",
    ],
    licence='GPLv3',
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'railstat': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'railstat': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = railstat.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
