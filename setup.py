from setuptools import setup, find_packages

setup(
    name="mcp_server",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask>=2.3.3",
        "flask-cors>=4.0.0",
        "python-dotenv>=0.19.0",
        "requests>=2.26.0"
    ]
) 