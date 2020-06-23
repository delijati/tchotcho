import setuptools

with open("requirements.txt") as f:
    requirements = [x for x in f.read().split("\n") if x and not x.startswith("#")]


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="tchotcho",
    version="0.7.0",
    author="Josip Delic",
    description="tchotcho",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/delijati/tchotcho",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
    zip_safe=False,
    include_package_data=True,
    package_dir={"": "src"},
    packages=setuptools.find_namespace_packages(where="src"),
    install_requires=requirements,
    extras_require={"tests": ["pytest", "pytest-cov", "pytest-env", "moto"]},
    entry_points={"console_scripts": ["tchotcho = tchotcho.__main__:cli"]},
)
