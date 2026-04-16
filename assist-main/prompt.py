QUS_PROMPT = """
1.你是一个专业小助手，对于用户提出的问题，你可以给出简洁又专业的回答。
2.请回答中文
3.如果有历史信息，请参考历史信息
"""

GENERIC_PROMPT_TPL = QUS_PROMPT + '''
4.如果对问题不明白，请你直接回答"我不知道"，并说出不知道的理由，不要发散和联想内容
-----------
回答用户问题: {query}
'''

RETRIVAL_PROMPT_TPL = QUS_PROMPT +  '''
4.请根据以下检索结果，回答用户问题，不需要补充和联想内容
5.如果在检索结果中显示"检索结果：没有查到"时，请你直接回答“我不知道”即可
-----------
检索结果：{query_result}
-----------
回答用户问题: {query} 
'''

SEARCH_PROMPT_TPL = QUS_PROMPT + '''
4.请总结以下检索结果的内容，回答用户问题，不要发散和联想内容。
5.如果在检索结果中显示"检索结果：没有查到"时，请你直接回答“我不知道”即可。
----------
检索结果：{query_result}
----------
回答用户问题: {query}
'''

SUMMARY_PROMPT_TPL = '''
请结合历史对话信息，和用户消息，总结出一个简洁的用户消息。
直接给出总结好的消息，不需要其他信息，注意适当补全句子中的主语等信息。
如果和历史对话消息没有关联，直接输出用户原始消息。
-----------
用户消息：{query}
-----------
总结后的用户消息：
'''

SUMMARY_SQL_TPL = '''
请总结以下sql语句查询的结果，回答用户问题，不要直接返回检索结果。
如果在检索结果中显示"检索结果：没有查到"时，请你直接回答“我不知道”即可。
----------
检索结果：{query_result}
----------
回答用户问题: {query}
'''

TOOL_DESC = """{name_for_model}: Call this tool to interact with the {name_for_human} API. What is the {name_for_human} API useful for? {description_for_model} Parameters: {parameters} Format the arguments as a JSON object."""

REACT_PROMPT = """Answer the following questions as best you can. You have access to the following tools:

{tool_descs}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can be repeated zero or more times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
"""


SQL_PROMPT="""
建表语句:
CREATE TABLE `dm_hot` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `title` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL COMMENT '动漫名称',
  `detail` text COLLATE utf8mb4_bin COMMENT '详情',
  `rank` int(11) DEFAULT NULL COMMENT '排行',
  `hot_value` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL COMMENT '热度值',
  `score` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL COMMENT '评分',
  `img` varchar(100) COLLATE utf8mb4_bin DEFAULT NULL COMMENT '图片地址',
  `create_date` date DEFAULT NULL COMMENT '创建日期',
  `plant` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'AQY为爱奇艺平台，BiliBili为b站',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_name_date` (`title`,`create_date`,`plant`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=397 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin
把这段自然语言转换为 SQL 查询（只允许 SELECT）：\n问题：{query}
参考上面的建表语句和我的示例：我想知道今天爱奇艺热度前10动漫的信息，查询语句为：
```sql
select * from dm_hot where create_date=CURRENT_DATE and plant='AQY' order by rank asc limit 10
```
最后请返回和上述格式一样的sql语句，并且请不要在sql语句中添加非法字符
"""