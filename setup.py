import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [
    'requests>=2.20.0',
]

setuptools.setup(
    name="python-payway", # Replace with your own username
    version="0.0.1",
    author="Ben Napper",
    author_email="reppan197@gmail.com",
    description="Python client for working with Westpac's PayWay REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url="https://github.com/napper1/python-payway",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
)