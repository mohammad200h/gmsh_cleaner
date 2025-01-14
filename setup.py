from setuptools import find_packages, setup

setup(
    name="gmsh_cleaner",
    packages=find_packages(),
    include_package_data=False,
    python_requires='>=3',
    author="Mohammad Hamid",
    license="MIT",
    install_requires=[
        "networkx",
        "numpy",
        "gmsh"
    ],
    entry_points={
        "console_scripts": [
            "gmsh_cleaner=gmsh_cleaner.gmsh_cleaner:main",  # Updated path
        ]
    },
    zip_safe=False
)