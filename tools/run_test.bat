cd ..
call .\.venv\Scripts\activate.bat
if exist pytest-report (
    echo Delete pytest-report...
    rmdir /s /q pytest-report
)
pytest --cov=azapidevops tests/ut_AzApi --cov-report html:pytest-report/ut/ut_htmlcov --html pytest-report/ut/ut_report.html
pytest --cov=azapidevops tests/st_AzApi --cov-report html:pytest-report/st/st_htmlcov --html pytest-report/st/st_report.html
