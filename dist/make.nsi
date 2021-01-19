Unicode True

!include "MUI2.nsh" # ���Ľ���Ҫ���� 
!include "LogicLib.nsh"  # �������Ҫ����

!insertmacro MUI_LANGUAGE "SimpChinese"

!define AppName "��Ƭ����AI������¼����ϵͳ"
!define InstallFiles "��Ƭ����AI������¼����ϵͳ"

Name ${AppName}

# define name of installer
OutFile "${AppName}_installer.exe"
 
# define installation directory
InstallDir $PROGRAMFILES\${AppName}

# ��װ·��ѡ�񵯿�
Page directory

# ����װ����ť
Page instfiles

# �Թ���ԱȨ�ް�װ
RequestExecutionLevel admin
 
# start default section
Section
    ${If} $INSTDIR == $PROGRAMFILES
	    MessageBox MB_OK "����ֱ�Ӱ�װ��$PROGRAMFILES����ȡ�������°�װ��"
		DetailPrint "����ֱ�Ӱ�װ��$PROGRAMFILES����ȡ�������°�װ��"
		Abort
	${EndIf}
 
    # set the installation directory as the destination for the following actions
    SetOutPath $INSTDIR
	
	File /r "${InstallFiles}\*.*"
 
    # create the uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
 
    # create a shortcut named "new shortcut" in the start menu programs directory
    # point the new shortcut at the program uninstaller
    CreateShortcut "$SMPROGRAMS\ж�� ${AppName}.lnk" "$INSTDIR\uninstall.exe"
SectionEnd
 
# uninstaller section start
Section "uninstall"
 
    # first, delete the uninstaller
    Delete "$INSTDIR\uninstall.exe"
 
    # second, remove the link from the start menu
    Delete "$SMPROGRAMS\ж�� ${AppName}.lnk"
	
	Delete "$DESKTOP\${AppName}.lnk"
 
    RMDir /r "$INSTDIR"
# uninstaller section end
SectionEnd

Section "Desktop Shortcut"

  SetOutPath "$INSTDIR"
  
  CreateShortCut "$DESKTOP\${AppName}.lnk" "$INSTDIR\${AppName}.exe" "" "$INSTDIR\icon\archives.ico"
SectionEnd

Section "Run as admin"
 
 	# ��Ե�ǰ�û���Ч
	WriteRegStr HKCU "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$INSTDIR\${AppName}.exe" "RUNASADMIN"
 
	# ��������û���Ч
	# WriteRegStr HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$INSTDIR\${AppName}.exe" "RUNASADMIN"
SectionEnd