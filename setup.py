from setuptools import setup


setup(
    name="because",
    version="0.0.0",
    description="Python API for Boundless Services",
    maintainer="Sasha Hart",
    maintainer_email="harts@boundlessgeo.com",
    url="https://github.com/harts-boundless/because",
    packages=[
        "because",
    ],
    install_requires=[
        "typing==3.5.3.0",
    ],
)
