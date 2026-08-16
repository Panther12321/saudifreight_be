from setuptools import find_packages, setup


setup(
    name="naqil",
    version="0.1.0",
    description="Naqil freight marketplace and fleet SaaS backend for Frappe",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
)
