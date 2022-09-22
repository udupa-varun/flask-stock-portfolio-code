<#
    .SYNOPSIS
        Sets up the venv.
    .DESCRIPTION
        Powershell script to setup/update the venv on Windows. Assumes the right version of Python is available.
    .EXAMPLE
        C:\code\python\tddio\flask-stock-portfolio-code>.\setup-win.ps1
    .NOTES
        Author: Varun Udupa
        Date:   Aug 29, 2022
#>
# exit on first failure
$ErrorActionPreference = "Stop"

Write-Output "Beginning setup..."

# where was the script called from?
$INVOKE_DIR = (Get-Item .).FullName
Write-Output "Invoke dir: $INVOKE_DIR"

# where is the script located?
$SCRIPT_DIR = $PSScriptRoot
Write-Output "Script dir: $SCRIPT_DIR"
Set-Location $SCRIPT_DIR


$PYVER = "3.10"
$PYCMD = "py -", $PYVER -join ""

# check if python is installed
Write-Output "Looking for Python $PYVER..."
$CMD = $PYCMD, "--version" -join " "
Invoke-Expression $CMD
Write-Output "Valid Python version detected."

# name for the venv
$VENV_NAME = "env"

# check if venv already exists
$VENV_PATH = Join-Path -Path $SCRIPT_DIR -ChildPath $VENV_NAME
if (Test-Path -Path $VENV_PATH) {
    Write-Output "An existing virtual environment '$VENV_NAME' was detected. It will be cleared and recreated."
}

# create new venv
Write-Output "Creating new virtual environment '$VENV_NAME'..."
$CMD = $PYCMD, "-m", "venv", $VENV_NAME, "--clear" -join " "
Invoke-Expression $CMD

# activate venv and upgrade pip
Write-Output "Activating virtual environment '$VENV_NAME'..."
$CMD = ".", $VENV_NAME, "Scripts", "Activate.ps1" -join "\"
Invoke-Expression $CMD

Write-Output "Upgrading pip..."
$CMD = "python -m pip install --upgrade pip"
Invoke-Expression $CMD

# install PDX Libraries requirements
Write-Output "Installing required packages inside virtual environment. This could take a few minutes..."
$CMD = "pip install -r .\requirements.txt"
Invoke-Expression $CMD

$PDX_PYTHONPATH = Resolve-Path($VENV_PATH, "Scripts", "python.exe" -join "\")

# reset location
Set-Location $INVOKE_DIR
Write-Output "Setup is complete."
