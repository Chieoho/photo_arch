pyinstaller -w -n ��Ƭ����AI������¼����ϵͳ -i .\icon\archives.ico --noconfirm --add-data="G:\Git\photo_arch\venv\Lib\site-packages\mxnet\*.dll*;.\mxnet" --hidden-import sklearn.utils._cython_blas --hidden-import sklearn.neighbors._typedefs --hidden-import sklearn.neighbors._quad_tree --hidden-import sklearn.tree._criterion --hidden-import sklearn.tree._utils main.py
echo d | xcopy .\icon .\dist\��Ƭ����AI������¼����ϵͳ\icon /s /e
echo d | xcopy .\model .\dist\��Ƭ����AI������¼����ϵͳ\model /s /e
echo d | xcopy .\mtcnn .\dist\��Ƭ����AI������¼����ϵͳ\mtcnn /s /e
echo d | xcopy .\config .\dist\��Ƭ����AI������¼����ϵͳ\config /s /e
del .\dist\��Ƭ����AI������¼����ϵͳ\photo_arch.db