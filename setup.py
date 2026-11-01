import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="github_storage_system",                     # This is the name of the package
    version="0.1.0",
    author="prasannan-robots",                     # Full name of the author
    description="Use a GitHub repository as simple file storage",
    url="https://github.com/prasannan-robots/Github_storage_system",
    long_description=long_description,      # Long description read from the the readme file
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),    # List of all python modules to be installed
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],                                      # Information to filter the project on PyPi website
    python_requires='>=3.8',
    py_modules=["github_storage_system"],             # Name of the python package
    package_dir={'':'github_storage_system/src'},     # Directory of the source code of the package
    install_requires=["PyGithub>=1.55"],
)