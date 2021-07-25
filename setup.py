from setuptools import setup

long_description = """
A custom sphinx extension that will allow you to link to the JavaDocs for your project from your documentation.

Please see the `GitHub repository <https://github.com/NariKiro/sphinx-JDLinker>`__ for more information.
"""

setup(
    name='sphinx-JDLinker',
    packages=['jdlinker'],
    version='2.0.1',
    license='MIT',
    description='A sphinx extension designed to allow you to create links to a JavaDoc website from your sphinx'
                ' documentation.',
    long_description=long_description,
    url='https://github.com/NariKiro/sphinx-JDLinker',
    author='NariKiro',
    author_email='narikiro@pm.me',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Sphinx :: Extension',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Java',
        'Programming Language :: Python',
        'Topic :: Documentation :: Sphinx'
    ],
    keywords='javadoc link sphinx documentation',
    install_requires=['sphinx >= 2.0.0']
)
