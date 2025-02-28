from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="selenium-qt-browser",
    version="1.0.0",
    author="Selenium Qt Browser Team",
    author_email="example@example.com",
    description="A PyQt6-based web browser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/selenium-qt-browser",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.4.0",
        "PyQt6-WebEngine>=6.4.0",
        "requests>=2.28.2",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "selenium-qt-browser=selenium_qt_browser.main:main",
        ],
    },
)