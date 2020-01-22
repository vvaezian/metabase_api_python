import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="metabase-api",
    version="0.1.1",
    author="Vahid Vaezian",
    author_email="vahid.vaezian@gmail.com",
    description="A Python Wrapper for Metabase API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vvaezian/metabase_api_python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
