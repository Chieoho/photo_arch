pyinstaller -n ��Ƭ����AI������¼����ϵͳ -i .\icon\archives.ico --hidden-import sklearn.utils._cython_blas main.py
echo d | xcopy .\dist\icon .\dist\��Ƭ����AI������¼����ϵͳ\icon /s /e
echo d | xcopy .\dist\model .\dist\��Ƭ����AI������¼����ϵͳ\model /s /e
echo d | xcopy .\dist\mtcnn .\dist\��Ƭ����AI������¼����ϵͳ\mtcnn /s /e
