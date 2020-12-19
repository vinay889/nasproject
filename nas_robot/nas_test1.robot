*** Settings ***
Library            SeleniumLibrary

*** Variables ***
${LOGIN URL}      http://192.168.43.162:4000
${BROWSER}        HeadlessChrome


*** Test Cases ***
Valid Login
    Open Browser To Login Page
    Input Username    USER1
    Input Password    vinay143
    Submit Credentials
    Set Selenium Speed      2
    [Teardown]    Close Browser

*** Keywords ***
Open Browser To Login Page
    Open Browser    ${LOGIN URL}    ${BROWSER}
    Title Should Be    NAS GATEWAY

Input Username
    [Arguments]    ${username}
    Input Text   username   ${username}

Input Password
    [Arguments]    ${password}
    Input Text   password   ${password}

Submit Credentials
    Click Button    login_button


