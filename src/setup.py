from setuptools import setup, find_packages

setup(
    name="mcp-test-generator",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "python-dotenv>=0.19.0",
        "requests>=2.26.0",
        "gunicorn>=20.1.0",
        "python-json-logger>=2.0.0",
        "prometheus-client>=0.16.0",  # For metrics
        "sentry-sdk[flask]>=1.0.0",   # For error tracking
        "flask-limiter>=3.3.0",       # For rate limiting
        "jira>=3.5.1",                # For Jira integration
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.900",
        ]
    },
    author="Naveen Kesavarapu`",
    author_email="naveenk@zenoti.com.com",
    description="Automated test case generator for Jira to TestRail integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="test-generation, jira, testrail, automation",
    url="https://github.com/yourusername/mcp-test-generator",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 