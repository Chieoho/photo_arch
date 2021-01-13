pyinstaller -w --name photo_arch -i .\icon\archives.ico --hidden-import sklearn.utils._cython_blas main.py
echo d | xcopy .\dist\icon .\dist\photo_arch\icon /s /e
echo d | xcopy .\dist\model .\dist\photo_arch\model /s /e
echo d | xcopy .\dist\mtcnn .\dist\photo_arch\mtcnn /s /e
