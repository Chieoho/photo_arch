pyinstaller -w -n 照片档案AI辅助著录管理系统 -i .\icon\archives.ico --noconfirm --add-data="G:\Git\photo_arch\venv\Lib\site-packages\mxnet\*.dll*;.\mxnet" --hidden-import sklearn.utils._cython_blas --hidden-import sklearn.neighbors._typedefs --hidden-import sklearn.neighbors._quad_tree --hidden-import sklearn.tree._criterion --hidden-import sklearn.tree._utils main.py
echo d | xcopy .\icon .\dist\照片档案AI辅助著录管理系统\icon /s /e
echo d | xcopy .\model .\dist\照片档案AI辅助著录管理系统\model /s /e
echo d | xcopy .\mtcnn .\dist\照片档案AI辅助著录管理系统\mtcnn /s /e
echo d | xcopy .\config .\dist\照片档案AI辅助著录管理系统\config /s /e
del .\dist\照片档案AI辅助著录管理系统\photo_arch.db