from setuptools import find_packages, setup

from saudi_hr import __version__

setup(
	name="saudi_hr",
	version=__version__,
	description="Saudi HR Management System — نظام إدارة شؤون الموظفين وفق نظام العمل السعودي",
	author="IdeaOrbit",
	author_email="info@ideaorbit.net",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=["openpyxl>=3.1.0", "openlocationcode>=1.0.1"],
)
