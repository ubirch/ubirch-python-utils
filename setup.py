import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ubirch-python-utils",
    version="1.0.7",
    author="Victor Patrin",
    author_email="victor.patrin150@gmail.com",
    description="A python utils ubirch for ubirch anchoring services.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ubirch/ubirch-python-utils",
    packages=setuptools.find_packages(exclude=['bin', 'tests']),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        'kafka-python >= 1.4.3',
        'boto3 >= 1.7.80'

    ],
)
