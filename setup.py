from setuptools import setup

with open("README.md", 'r') as readme:
    long_description = readme.read()

setup(
    name="benderslib",
    version="0.0.1",
    description="An Extensible Benders Decomposition Library in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPL-3.0",
    url="https://benders.dev",

    author="Peng-Hui Guo",
    author_email="m@guo.ph",

    packages=["benderslib"],
    install_requires=[]
)
