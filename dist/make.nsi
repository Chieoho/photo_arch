Unicode True

!include "MUI2.nsh" # 中文界面要导入 
!include "LogicLib.nsh"  # 条件语句要导入

!insertmacro MUI_LANGUAGE "SimpChinese"

!define AppName "照片档案AI辅助著录管理系统"
!define InstallFiles "照片档案AI辅助著录管理系统"

Name ${AppName}

# define name of installer
OutFile "${AppName}_installer.exe"
 
# define installation directory
InstallDir $PROGRAMFILES\${AppName}

# 安装路径选择弹框
Page directory

# “安装”按钮
Page instfiles

# 以管理员权限安装
RequestExecutionLevel admin
 
# start default section
Section
    ${If} $INSTDIR == $PROGRAMFILES
	    MessageBox MB_OK "不能直接安装到$PROGRAMFILES，请取消后重新安装。"
		DetailPrint "不能直接安装到$PROGRAMFILES，请取消后重新安装。"
		Abort
	${EndIf}
 
    # set the installation directory as the destination for the following actions
    SetOutPath $INSTDIR
	
	File /r "${InstallFiles}\*.*"
 
    # create the uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
 
    # create a shortcut named "new shortcut" in the start menu programs directory
    # point the new shortcut at the program uninstaller
    CreateShortcut "$SMPROGRAMS\卸载 ${AppName}.lnk" "$INSTDIR\uninstall.exe"
SectionEnd
 
# uninstaller section start
Section "uninstall"
 
    # first, delete the uninstaller
    Delete "$INSTDIR\uninstall.exe"
 
    # second, remove the link from the start menu
    Delete "$SMPROGRAMS\卸载 ${AppName}.lnk"
	
	Delete "$DESKTOP\${AppName}.lnk"
 
    RMDir /r "$INSTDIR"
# uninstaller section end
SectionEnd

Section "Desktop Shortcut"

  SetOutPath "$INSTDIR"
  
  CreateShortCut "$DESKTOP\${AppName}.lnk" "$INSTDIR\${AppName}.exe" "" "$INSTDIR\icon\archives.ico"
SectionEnd

Section "Run as admin"
 
 	# 针对当前用户有效
	WriteRegStr HKCU "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$INSTDIR\${AppName}.exe" "RUNASADMIN"
 
	# 针对所有用户有效
	# WriteRegStr HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$INSTDIR\${AppName}.exe" "RUNASADMIN"
SectionEnd