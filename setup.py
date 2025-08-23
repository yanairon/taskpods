from setuptools import setup

setup(
    name="taskpods",
    version="0.1.0",
    py_modules=["taskpods"],
    entry_points={
        "console_scripts": [
            "taskpods=taskpods:main",
        ],
    },
    author="Yanai Ron",
    license="MIT",
    description="Parallel AI task pods via git worktrees",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yanairon/taskpods",
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
