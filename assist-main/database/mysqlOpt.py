import pymysql
from pymysql.cursors import DictCursor
from typing import Union, List, Dict, Any, Optional
import configparser
import os
from functools import wraps


class MySQLUtil:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_file: str = './database/config.ini'):
        """
        单例模式初始化，从配置文件读取数据库配置

        :param config_file: 配置文件路径，默认当前目录下的config.ini
        """
        if self._initialized:
            return

        self._initialized = True
        self.connection = None
        self.cursor = None
        self.config_file = config_file
        self._load_config()
        self.connect()

    def _load_config(self):
        """从配置文件加载数据库配置"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")

        config = configparser.ConfigParser()
        config.read(self.config_file, encoding='utf-8')

        try:
            db_config = config['DATABASE']
            self.host = db_config.get('host', 'localhost')
            self.port = db_config.getint('port', 3306)
            self.user = db_config.get('user', 'root')
            self.password = db_config.get('password', '')
            self.database = db_config.get('database', '')
            self.charset = db_config.get('charset', 'utf8mb4')
        except KeyError:
            raise ValueError("配置文件中缺少必要的DATABASE配置节")

    def connect(self) -> None:
        """建立数据库连接"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=DictCursor,
                autocommit=False  # 手动控制事务
            )
            self.cursor = self.connection.cursor()
            print("数据库连接成功")
        except pymysql.Error as e:
            print(f"数据库连接失败: {e}")
            raise

    def close(self) -> None:
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.connection = None
        self.cursor = None
        print("数据库连接已关闭")

    def reconnect(self) -> None:
        """重新连接数据库"""
        self.close()
        self.connect()

    def check_connection(func):
        """装饰器：检查连接是否有效"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                if not self.connection or not self.connection.open:
                    self.reconnect()
                return func(self, *args, **kwargs)
            except pymysql.OperationalError as e:
                print(f"数据库操作错误: {e}, 尝试重新连接...")
                self.reconnect()
                return func(self, *args, **kwargs)

        return wrapper

    @check_connection
    def execute_query(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> List[Dict[str, Any]]:
        """执行查询SQL语句"""
        try:
            self.cursor.execute(sql, params or ())
            return self.cursor.fetchall()
        except pymysql.Error as e:
            print(f"查询执行失败: {e}")
            raise

    @check_connection
    def execute_update(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> int:
        """执行更新SQL语句"""
        try:
            affected_rows = self.cursor.execute(sql, params or ())
            self.connection.commit()
            print(f"插入数据成功: {affected_rows}")
            return affected_rows
        except pymysql.Error as e:
            self.connection.rollback()
            print(f"更新执行失败: {e}")
            raise

    @check_connection
    def execute_many(self, sql: str, params_list: List[Union[tuple, dict]]) -> int:
        """批量执行SQL语句"""
        try:
            affected_rows = self.cursor.executemany(sql, params_list)
            self.connection.commit()
            return affected_rows
        except pymysql.Error as e:
            self.connection.rollback()
            print(f"批量执行失败: {e}")
            raise

    @check_connection
    def get_one(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> Optional[Dict[str, Any]]:
        """获取单条记录"""
        try:
            self.cursor.execute(sql, params or ())
            return self.cursor.fetchone()
        except pymysql.Error as e:
            print(f"获取单条记录失败: {e}")
            raise

    @check_connection
    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        sql = """
        SELECT COUNT(*) as count 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s
        """
        result = self.get_one(sql, (self.database, table_name))
        return result['count'] > 0 if result else False

    def __del__(self):
        """析构函数自动关闭连接"""
        self.close()


# 使用示例
if __name__ == '__main__':
    # 使用单例模式
    db1 = MySQLUtil()
    db2 = MySQLUtil()

    print(f"db1和db2是同一个实例: {db1 is db2}")  # 输出 True

    # 查询示例
    users = db1.execute_query("SELECT * FROM people")
    print("查询结果:", users)
