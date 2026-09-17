from setuptools import setup, find_packages

setup(
    name="career_compiler_document_engineering",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pydantic>=2.0.0",
        "jinja2>=3.1.2",
    ],
    extras_require={
        "dev": ["pytest", "black", "isort"],
    },
)
