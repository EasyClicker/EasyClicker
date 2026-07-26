[Setup]
AppName=EasyClicker
AppVersion=1.0.3
AppPublisher=Easy click studio
AppPublisherURL=https://github.com/EasyClicker/EasyClicker
DefaultDirName={autopf}\EasyClicker
DefaultGroupName=EasyClicker
UninstallDisplayIcon={app}\EasyClicker.exe
Compression=lzma
SolidCompression=yes
OutputDir=.\
OutputBaseFilename=EasyClicker_Setup_v1.0.3
SetupIconFile=icon.ico

; Данные об авторе и версии внутри EXE-файла установщика
VersionInfoCompany=Easy click studio
VersionInfoDescription=EasyClicker Installer
VersionInfoTextVersion=1.0.3
VersionInfoVersion=1.0.3
VersionInfoCopyright=Copyright (C) 2026 Easy click studio

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist/EasyClicker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\EasyClicker"; Filename: "{app}\EasyClicker.exe"
Name: "{autodesktop}\EasyClicker"; Filename: "{app}\EasyClicker.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\EasyClicker.exe"; Description: "{cm:LaunchProgram,EasyClicker}"; Flags: nowait postinstall skipifsilent