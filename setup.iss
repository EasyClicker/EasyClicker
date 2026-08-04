[Setup]
AppName=EasyClicker
AppVersion=1.0.7
AppPublisher=Easy click studio
AppPublisherURL=https://github.com/EasyClickStudio/EasyClicker
DefaultDirName={autopf}\EasyClicker
DefaultGroupName=EasyClicker
UninstallDisplayIcon={app}\EasyClicker.exe
UninstallDisplayName=EasyClicker
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=.\
OutputBaseFilename=EasyClicker_Setup_v1.0.7
SetupIconFile=icon.ico

; Принудительно запрашиваем права админа для корректной записи ярлыков
PrivilegesRequired=admin

; Проверка мьютекса из main.py — не даст установить поверх работающего кликера
AppMutex=EasyClicker_Unique_App_Mutex_2026

VersionInfoCompany=Easy click studio
VersionInfoDescription=EasyClicker Installer
VersionInfoTextVersion=1.0.7
VersionInfoVersion=1.0.7
VersionInfoCopyright=Copyright (C) 2026 Easy click studio

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\EasyClicker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\EasyClicker"; Filename: "{app}\EasyClicker.exe"
Name: "{userdesktop}\EasyClicker"; Filename: "{app}\EasyClicker.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EasyClicker.exe"; Description: "{cm:LaunchProgram,EasyClicker}"; Flags: nowait postinstall skipifsilent