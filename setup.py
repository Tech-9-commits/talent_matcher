from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="talent_matcher",
    version="0.0.1",
    description="AI-powered resume parsing and candidate matching for Frappe and ERPNext HRMS",
    author="Talent Matcher Team",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
