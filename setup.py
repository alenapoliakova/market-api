from setuptools import setup, find_packages

with open("requirements.txt") as file:
    required = file.read().splitlines()

setup(
    name="analyzer",
    version="1.0.0",
    python_requires='>=3.10',
    author="Alena Polyakova",
    author_email='alenapoliakova2003@gmail.com',
    packages=find_packages(exclude=['tests']),
    install_requires=required,
    include_package_data=True,
)
