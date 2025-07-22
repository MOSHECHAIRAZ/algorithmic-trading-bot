# IBKR Gateway Auto-Login PowerShell Script
# This script uses Windows UI Automation to find and interact with the Gateway login form

Write-Host "IBKR Gateway PowerShell Auto-Login Utility" -ForegroundColor Cyan
Write-Host "---------------------------------------------------" -ForegroundColor Cyan

# Configuration
$IBKR_PATH = "C:\Jts\ibgateway\1037\ibgateway.exe"
$IBKR_USER = "bvqcpy485"
$IBKR_PASS = "R0533124116"

# Check if Gateway exists
if (-not (Test-Path $IBKR_PATH)) {
    Write-Host "Error: Gateway not found at $IBKR_PATH" -ForegroundColor Red
    exit 1
}

# Start the Gateway
Write-Host "Starting IBKR Gateway..." -ForegroundColor Yellow
Start-Process -FilePath $IBKR_PATH

# Wait for Gateway to initialize
Write-Host "Waiting for Gateway to initialize (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Try to use UI Automation
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

# Function to find window by title
function Find-Window {
    param (
        [string[]]$possibleTitles
    )
    
    foreach ($title in $possibleTitles) {
        $condition = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::NameProperty, 
            $title
        )
        
        $windows = [System.Windows.Automation.AutomationElement]::RootElement.FindAll(
            [System.Windows.Automation.TreeScope]::Children,
            $condition
        )
        
        if ($windows.Count -gt 0) {
            Write-Host "Found window: $title" -ForegroundColor Green
            return $windows[0]
        }
    }
    
    Write-Host "Window not found using UI Automation" -ForegroundColor Yellow
    return $null
}

# Find the IB Gateway window
$window = Find-Window @("IB Gateway", "Interactive Brokers Gateway", "IBKR Gateway Login", "Login", "Gateway")

# If window found, try to find input fields
if ($window -ne $null) {
    try {
        # Try to find editable elements (text boxes)
        $controlTypeCondition = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty, 
            [System.Windows.Automation.ControlType]::Edit
        )
        
        $editableElements = $window.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            $controlTypeCondition
        )
        
        if ($editableElements.Count -ge 2) {
            # Assume first is username, second is password
            $usernameField = $editableElements[0]
            $passwordField = $editableElements[1]
            
            # Set username
            $valuePattern = $usernameField.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
            $valuePattern.SetValue($IBKR_USER)
            Write-Host "Username entered" -ForegroundColor Green
            
            # Set password
            $valuePattern = $passwordField.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
            $valuePattern.SetValue($IBKR_PASS)
            Write-Host "Password entered" -ForegroundColor Green
            
            # Find Login button
            $buttonCondition = New-Object System.Windows.Automation.PropertyCondition(
                [System.Windows.Automation.AutomationElement]::ControlTypeProperty, 
                [System.Windows.Automation.ControlType]::Button
            )
            
            $allButtons = $window.FindAll(
                [System.Windows.Automation.TreeScope]::Descendants,
                $buttonCondition
            ) 
            
            $loginButton = $allButtons | Where-Object { $_.Current.Name -match "Login|Log In|Sign In|Enter" }
            
            if ($loginButton -ne $null) {
                # Click login button
                $invokePattern = $loginButton.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                $invokePattern.Invoke()
                Write-Host "Login button clicked" -ForegroundColor Green
            }
            else {
                # If no button found, try to send Enter key
                Write-Host "Login button not found, sending Enter key..." -ForegroundColor Yellow
                [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
            }
        }
        else {
            Write-Host "Could not find username/password fields. Found $($editableElements.Count) editable fields" -ForegroundColor Yellow
            # Fall back to SendKeys method
            Write-Host "Falling back to keyboard input method..." -ForegroundColor Yellow
            [System.Windows.Forms.SendKeys]::SendWait($IBKR_USER)
            Start-Sleep -Milliseconds 800
            [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
            Start-Sleep -Milliseconds 800
            [System.Windows.Forms.SendKeys]::SendWait($IBKR_PASS)
            Start-Sleep -Milliseconds 800
            [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
        }
    }
    catch {
        Write-Host "Error using UI Automation: $_" -ForegroundColor Red
        # Fall back to SendKeys method
        Write-Host "Falling back to keyboard input method..." -ForegroundColor Yellow
        [System.Windows.Forms.SendKeys]::SendWait($IBKR_USER)
        Start-Sleep -Milliseconds 800
        [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
        Start-Sleep -Milliseconds 800
        [System.Windows.Forms.SendKeys]::SendWait($IBKR_PASS)
        Start-Sleep -Milliseconds 800
        [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    }
}
else {
    # Fall back to SendKeys method
    Write-Host "Using keyboard input method..." -ForegroundColor Yellow
    # Try to focus the Gateway window with Alt+Tab
    for ($i = 0; $i -lt 5; $i++) {
        [System.Windows.Forms.SendKeys]::SendWait("%{TAB}")
        Start-Sleep -Milliseconds 500
    }
    
    # Enter credentials
    Start-Sleep -Seconds 1
    [System.Windows.Forms.SendKeys]::SendWait($IBKR_USER)
    Start-Sleep -Milliseconds 800
    [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
    Start-Sleep -Milliseconds 800
    [System.Windows.Forms.SendKeys]::SendWait($IBKR_PASS)
    Start-Sleep -Milliseconds 800
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
}

Write-Host "Login attempt in progress. The Gateway should be logging in now." -ForegroundColor Cyan
