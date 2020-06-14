from setuptools import setup

setup(
    name="gTagger",
    version="0.1",
    packages=["gtagger"],
    author="Muhammad Haroon",
    author_email="m_haroon96@hotmail.com",
    description="CLI song metadata tagger using Genius.com",
    install_requires=[
        'bs4',
        'requests',
        'google',
        'mutagen',
        'pathvalidate'
    ],
    entry_points={
        "console_scripts": [
            "gtagger = gtagger.cli:cli"
        ]
    },
)