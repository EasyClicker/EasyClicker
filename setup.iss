[Setup]
AppName=EasyClicker
AppVersion=1.0.0
AppPublisher=EasyClicker
AppPublisherURL=https://github.com/EasyClicker/EasyClicker
DefaultDirName={autopf}\EasyClicker
DefaultGroupName=EasyClicker
UninstallDisplayIcon={app}\EasyClicker.exe
Compression=lzma
SolidCompression=yes
OutputDir=.\
OutputBaseFilename=EasyClicker_Setup_v1.0.0
SetupIconFile=icon.ico

; Данные об авторе и версии внутри EXE-файла установщика
VersionInfoCompany=EasyClicker
VersionInfoDescription=EasyClicker Installer
VersionInfoTextVersion=1.0.0
VersionInfoVersion=1.0.0.0
VersionInfoCopyright=Copyright (C) 2026 EasyClicker

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "EasyClicker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\EasyClicker"; Filename: "{app}\EasyClicker.exe"
; --- ВОТ ЭТА СТРОЧКА ИСПРАВИТ ИКОНКУ НА РАБОЧЕМ СТОЛЕ ---
Name: "{autodesktop}\EasyClicker"; Filename: "{app}\EasyClicker.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\EasyClicker.exe"; Description: "{cm:LaunchProgram,EasyClicker}"; Flags: nowait postinstall skipifsilent