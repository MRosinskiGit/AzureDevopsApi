cd ..
call .\.venv\Scripts\activate.bat
pytest --cov=AzApi ut_AzApi --cov-report html:pytest-report/ut/ut_htmlcov --html pytest-report/ut/ut_report.html
pytest --cov=AzApi st_AzApi --cov-report html:pytest-report/st/st_htmlcov --html pytest-report/st/st_report.html
