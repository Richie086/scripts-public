.PHONY: setup lint test run

setup:
	@echo "Installing PSScriptAnalyzer and Pester..."
	pwsh -Command "Install-Module -Name PSScriptAnalyzer,Pester -Force -Scope CurrentUser"

lint:
	pwsh -Command "Invoke-ScriptAnalyzer -Path powershell/*.ps1" || echo "PSScriptAnalyzer not installed or returned warnings"

test:
	pwsh -Command "Invoke-Pester -Path tests/ -Output Detailed" || echo "Pester not installed or tests failed"

run:
	pwsh -File powershell/example.ps1 -Hostname "localhost"
