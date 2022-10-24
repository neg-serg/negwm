from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="alluvium",
    version="0.1.1",
    author="Marten Lienen",
    author_email="marten.lienen@gmail.com",
    description="Interactive bindings visualizer for i3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cqql/alluvium",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["i3ipc", "PyGObject"],
    entry_points={"console_scripts": ["alluvium=alluvium.main:main"]},
)
