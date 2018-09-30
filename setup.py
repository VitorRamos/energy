import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="energyOptimal",
    version="0.0.1",
    author="Vitor Ramos Gomes da Silva",
    author_email="ramos.vitor89@gmail.com",
    description="DVFS algorithm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VitorRamos/energy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux",
    ],
)