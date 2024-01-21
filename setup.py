from setuptools import setup

setup(
    entry_points={
        'console_scripts': [
            'cte = cloud_tasks_emulator.cli:main',
        ]
    }
)