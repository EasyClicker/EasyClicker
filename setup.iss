[Setup]
AppName=EasyClicker
AppVersion=1.0.0
DefaultDirName={autopf}\EasyClicker
DefaultGroupName=EasyClicker
UninstallDisplayIcon={app}\EasyClicker.exe
Compression=lzma
SolidCompression=yes
OutputDir=.\
OutputBaseFilename=EasyClicker_Setup_v1.0.0
SetupIconFile=icon.ico

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\EasyClicker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\EasyClicker"; Filename: "{app}\EasyClicker.exe"
Name: "{autodesktop}\EasyClicker"; Filename: "{app}\EasyClicker.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EasyClicker.exe"; Description: "{cm:LaunchProgram,EasyClicker}"; Flags: nowait postinstall skipifsilent