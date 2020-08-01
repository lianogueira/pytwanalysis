import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="example-pkg-your-username",
    version="0.0.1",
    author="Lia Nogueira",
    author_email="lia.lnm@gmail.com",
    description="A tool to gather, discover, and analyze Twitter data using a combinations of graph-clustering and topic modeling techniques with the goal of semantically grouping tweet messages together.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lianogueira/pyTwitterAnalysis",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
)