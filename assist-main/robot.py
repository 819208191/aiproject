from langchain_core.prompts import PromptTemplate
from transformers import AutoModelForCausalLM, AutoTokenizer
from prompt import *
from config import *
from data_process import *
from database.mysqlOpt import MySQLUtil
import torch
import re
from baidusearch.baidusearch import search



class QwenChatbot:
    def __init__(self, model_name=None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map='auto').to(self.device)
        self.history = []
        self.retriever = HybridRetriever()
        self.db = MySQLUtil()

    def generic_func(self, query):
        prompt = GENERIC_PROMPT_TPL.format(query=query)
        return self.response(query,prompt)

    def select_func(self, query):
        prompt = SQL_PROMPT.format(query=query)
        res = self.response(query,prompt)
        pattern = re.compile(r"```sql\s+(.*?)\s+```")
        match = pattern.search(res)

        if match:
            sql = match.group(0).strip()  # 去除可能的空白字符
            sql = sql.replace("```sql","")
            sql = sql.replace("```","")
            sql = sql.replace("''","'")
            print(sql)
            users = self.db.execute_query(sql)
            users = users if len(users)!=0 else "没有查到"
            prompt = SUMMARY_SQL_TPL.format(query=query, query_result=users)
        else:
            return "没有查到"
        return self.response(query,prompt)

    def retrival_func(self, query):

        # 召回并过滤文档
        contexts = self.retriever.retrieve(query)

        query_result = []
        for context in contexts:
            query_result.append(context.page_content)

        if len(query_result):
            query_result = '\n\n'.join(query_result)
        else:
            query_result = "没有查到"

        # 填充提示词并总结答案
        prompt = RETRIVAL_PROMPT_TPL.format(query=query,query_result=query_result)
        print(prompt)
        return self.response(query,prompt)

    def search_func(self, query):
        results = search(query)
        contexts = [result['abstract'].split('\n') for result in results]
        results = []
        for context in contexts:
            items = []
            for item in context:
                if len(item) > VALID_NUM:
                    items.append(item)
            results.extend(items)

        query_result = '\n\n'.join(results) if len(results) else '没有查到'
        prompt = SEARCH_PROMPT_TPL.format(query=query,query_result=query_result)

        return self.response(query,prompt)

    def response(self,query,prompt=None,isHistory=True):
        messages = self.history + [{"role": "user", "content":prompt}]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
            enable_thinking=True
        )

        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        response_ids = self.model.generate(**inputs,
                                           temperature=TEMPERARURE,
                                           top_p=TOP_P,
                                           top_k=TOP_K,
                                           do_sample=DO_SAMPLE,
                                           max_new_tokens=MAX_TOKENS)[0][len(inputs.input_ids[0]):].tolist()
        response = self.tokenizer.decode(response_ids, skip_special_tokens=True)
        response = re.sub(r'^.*</think>', '', response, flags=re.DOTALL)
        if not isHistory:
            return response
        # Update history
        self.history.append({"role": "assistant", "content": response})
        self.history.append({"role": "user", "content": query})
        return response


if __name__ == '__main__':
    robot = QwenChatbot(MODEL_PATH)
    #print(robot.search_func("明天厦门的天气怎么样"))
    print(robot.select_func("我想知道今天b站和爱奇艺热度前10动漫的信息"))

