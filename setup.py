import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="RTFDE",
    version="0.1.1",
    author="seamus tuohy",
    author_email="code@seamustuohy.com",
    description="A library for extracting HTML content from RTF encapsulated HTML as commonly found in the exchange MSG email format.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seamustuohy/RTFDE",
    packages=setuptools.find_packages(
        exclude=['tests*'],
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Markup :: HTML",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Filters",
        "Topic :: Communications :: Email :: Filters"
    ],

    python_requires='>=3.8',
    install_requires=['lark==1.1.8',
                      'oletools>=0.56'],
    extras_require={'msg_parse': ['extract_msg>=0.27'],
                    'dev': ['lxml>=4.6',
                            'mypy>=1.1.1',
                            'pdoc3>=0.10.0',
                            'coverage>=7.2.2']}
)
