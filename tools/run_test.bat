cd ..
call .\.venv\Scripts\activate.bat
pytest --cov=AzApi ut_AzApi --cov-report html:pytest-report/htmlcov --html pytest-report/report.html

