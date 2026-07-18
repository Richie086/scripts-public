Describe "PowerShell Example Script" {
    BeforeAll {
        $ScriptPath = "$PSScriptRoot/../powershell/example.ps1"
    }

    It "Should exist" {
        $ScriptPath | Should -Exist
    }

    It "Should run successfully and output hostname" {
        $result = & $ScriptPath -Hostname "10.0.0.1"
        $result | Should -Contain "[INFO] Target hostname: 10.0.0.1"
    }
}
