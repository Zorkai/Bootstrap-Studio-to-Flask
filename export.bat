@echo off
set BASE_PATH=%~dp0
set LOG_PATH=%BASE_PATH%\log.txt
set PYTHON_FILE=%BASE_PATH%\convert.py

:: Create the directory if it doesn't exist
if not exist "%BASE_PATH%" (
    mkdir "%BASE_PATH%"
)

:: Clear or create the log file
echo. > "%LOG_PATH%"

:: Write the script name to the log file
echo Script Name: %~n0.bat >> "%LOG_PATH%"
echo Number of Parameters: %* >> "%LOG_PATH%"
echo. >> "%LOG_PATH%"

if "%1"=="" (
    echo No parameters were provided. >> "%LOG_PATH%"
    echo No parameters were provided.
) else (
    echo Parameters Provided: >> "%LOG_PATH%"
    for %%A in (%*) do (
        echo %%A >> "%LOG_PATH%"
    )
    echo Running Python script with parameter: %1
    :: Run the Python script and pass the first parameter
    py "%PYTHON_FILE%" "%1"
)

:: Inform the user and pause
echo Output has been written to %LOG_PATH%
pause
