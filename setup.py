import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
    
    
setuptools.setup(
    name="pytwanalysis",
    version="0.0.6",
    author="Lia Nogueira",    
    description="A tool to gather, discover, and analyze Twitter data using a combination of graph-clustering and topic modeling techniques with the goal of semantically grouping tweet messages together.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lianogueira/pytwanalysis",
    project_urls={
        "Source Code": "https://github.com/lianogueira/pytwanalysis",
        "Documentation": "https://lianogueira.github.io/pytwanalysis-documentation/",
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research"        
    ],
)