from config import *
from prompt import *
from robot import *
from typing import Dict, List, Optional, Tuple, Union




class Agent():
    def __init__(self):
        self.robot = QwenChatbot(MODEL_PATH)
        self.toolConfig = self._tools()
        self.system_prompt = self.build_system_input()

    def build_system_input(self):
        tool_descs, tool_names = [], []
        for tool in self.toolConfig:
            tool_descs.append(TOOL_DESC.format(**tool))
            tool_names.append(tool['name_for_model'])
        tool_descs = '\n\n'.join(tool_descs)
        tool_names = ','.join(tool_names)
        sys_prompt = REACT_PROMPT.format(tool_descs=tool_descs, tool_names=tool_names)
        return sys_prompt

    def parse_latest_plugin_call(self, text):
        plugin_name, plugin_args = '', ''
        i = text.rfind('\nAction:')
        j = text.rfind('\nAction Input:')
        k = text.rfind('\nObservation:')
        if 0 <= i < j:  # If the text has `Action` and `Action input`,
            if k < j:  # but does not contain `Observation`,
                text = text.rstrip() + '\nObservation:'  # Add it back.
            k = text.rfind('\nObservation:')
            plugin_name = text[i + len('\nAction:'): j].strip()
            plugin_args = text[j + len('\nAction Input:'): k].strip()
            text = text[:k]
        return plugin_name, plugin_args, text

    def call_plugin(self, plugin_name, query):
        print(plugin_name)
        return getattr(self.robot,plugin_name)(query)

    def text_completion(self, text):
        if len(self.robot.history):
            prompt = SUMMARY_PROMPT_TPL.format(query=text)
            text = self.robot.response(text,prompt,isHistory=False)
            text = text.replace("用户消息：","")
        print(text)
        prompt =  self.system_prompt + "\nQuestion:" + text
        response = self.robot.response(text,prompt,isHistory=False)
        plugin_name, plugin_args, response = self.parse_latest_plugin_call(response)
        if plugin_name:
            response = self.call_plugin(plugin_name, text)
        return response


    def _tools(self):
        tools = [
            {
                'name_for_human': '百度搜索',
                'name_for_model': 'search_func',
                'description_for_model': '百度搜索是一个通用搜索引擎，可以访问互联网、查询百科知识、了解时事新闻等。',
                'parameters': [
                    {
                        'name': 'query',
                        'description': '搜索关键词或短语',
                        'required': True,
                        'schema': {'type': 'string'},
                    }
                ],
            },{
                'name_for_human': '火影忍者知识检索',
                'name_for_model': 'retrival_func',
                'description_for_model': '仅用于回答火影忍者相关问题，不能回答其他问题',
                'parameters': [
                    {
                        'name': 'query',
                        'description': '搜索关键词或短语',
                        'required': True,
                        'schema': {'type': 'string'},
                    }
                ],
            },{
                'name_for_human': '通用回答',
                'name_for_model': 'generic_func',
                'description_for_model': '可以解答通用领域的知识，用于解决用户提出的简单问题',
                'parameters': [
                    {
                        'name': 'query',
                        'description': '提问的问题',
                        'required': True,
                        'schema': {'type': 'string'},
                    }
                ],
            },{
                'name_for_human': '数据库检索',
                'name_for_model': 'select_func',
                'description_for_model': '可以解答用户提出数据库查询相关的问题',
                'parameters': [
                    {
                        'name': 'query',
                        'description': '提问的问题',
                        'required': True,
                        'schema': {'type': 'string'},
                    }
                ],
            }
        ]
        return tools



if __name__ == '__main__':

    agent = Agent()

    # print(agent.text_completion("明天厦门的天气怎么样"))
    print(agent.text_completion("介绍一下卷积神经网络"))
    print(agent.text_completion("它的具体应用有什么"))
    print(agent.text_completion("介绍一下火影忍者的卡卡西"))

