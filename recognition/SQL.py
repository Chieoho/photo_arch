import sqlite3


class SQL_method:
    '''
    function: 可以实现对数据库的基本操作
    '''
    def __init__(self, dbName, tableName, columns):
        '''
        function: 初始化参数
        dbName: 数据库文件名
        tableName: 数据库中表的名称
        data: 从csv文件中读取且经过处理的数据
        columns: 用于创建数据库，为表的第一行
        Read_All: 创建表之后是否读取出所有数据
        '''
        self.dbName = dbName
        self.tableName = tableName
        self.columns = columns


    def connectDB(self):
        # 连接数据库
        self.connect = sqlite3.connect(self.dbName,  check_same_thread=False)

    def closeDB(self):
        # 断开连接
        self.connect.close()

    def creatTable(self):
        '''
        function: 创建数据库文件及相关的表
        '''
        # 连接数据库
        # connect = sqlite3.connect(self.dbName)
        # 创建表
        self.connect.execute("CREATE TABLE {}({})".format(self.tableName, self.columns))
        # 提交事务
        self.connect.commit()
        # 断开连接
        # connect.close()

    def destroyTable(self):
        '''
        function: 删除数据库文件中的表
        '''
        # 连接数据库
        connect = sqlite3.connect(self.dbName)
        # 删除表
        connect.execute("DROP TABLE {}".format(self.tableName))
        # 提交事务
        connect.commit()
        # 断开连接
        connect.close()

    def executeStatement(self, statement):

        cursor = self.connect.cursor()
        cursor.execute(statement)
        self.connect.commit()
        cursor.close()


    def executeManyStatement(self, statement, data):

        cursor = self.connect.cursor()
        cursor.executemany(statement, data)
        self.connect.commit()
        cursor.close()


    def isExistCurrentRecord(self, statement):
        '''
        function: 向数据库文件中的表插入多条数据
        '''
        # 连接数据库
        # connect = sqlite3.connect(self.dbName)
        # 插入多条数据
        cursor = self.connect.cursor()
        cursor.execute(statement)
        result = cursor.fetchone() # tuple类型，如：(4, )
        cursor.close()

        return  result[0]

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


    def getAllData(self, statement):
        '''
        function: 得到数据库文件中的所有数据
        '''
        self.connect.row_factory = self.dict_factory
        # 创建游标对象
        cursor = self.connect.cursor()
        # 读取数据
        cursor.execute(statement)
        dataList = cursor.fetchall()
        cursor.close()

        return dataList

    def searchData(self, conditions, IfPrint=True):
        '''
        function: 查找特定的数据
        '''
        # 连接数据库
        connect = sqlite3.connect(self.dbName)
        # 创建游标
        cursor = connect.cursor()
        # 查找数据
        cursor.execute("SELECT * FROM {} WHERE {}".format(self.tableName, conditions))
        data = cursor.fetchall()
        # 关闭游标
        cursor.close()
        # 断开数据库连接
        connect.close()
        if IfPrint:
            self.printData(data)
        return data

    def deleteData(self, conditions):
        '''
        function: 删除数据库中的数据
        '''
        # 连接数据库
        connect = sqlite3.connect(self.dbName)
        # 插入多条数据
        connect.execute("DELETE FROM {} WHERE {}".format(self.tableName, conditions))
        # 提交事务
        connect.commit()
        # 断开连接
        connect.close()

