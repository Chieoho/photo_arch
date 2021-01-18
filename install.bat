pyinstaller -n 照片档案AI辅助著录管理系统 -i .\icon\archives.ico --hidden-import sklearn.utils._cython_blas main.py
echo d | xcopy .\dist\icon .\dist\照片档案AI辅助著录管理系统\icon /s /e
echo d | xcopy .\dist\model .\dist\照片档案AI辅助著录管理系统\model /s /e
echo d | xcopy .\dist\mtcnn .\dist\照片档案AI辅助著录管理系统\mtcnn /s /e
