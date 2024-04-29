import asyncio
import autogen
from autogen import ConversableAgent
from autogen.agentchat.contrib.capabilities.teachability import Teachability
from datetime import date
import time

from src.user_proxy_webagent import UserProxyWebAgent
from src.custom.CustomAssistantAgent import CustomAssistantAgent
from src.tools.browse.ResearchAgent import ResearcherAgent, search_function_definitions
from src.config.config_list_llm import autogen_config_list, gpt35_config_list, llama3_groq_config_70b


teachable_llm_config = {
    "model":"llama3-70b-8192",
    "temperature": 0,
    "config_list": llama3_groq_config_70b
}


llm_config_assistant = {
    "model":"llama3-70b-8192",
    "temperature": 0,
    "config_list": llama3_groq_config_70b,
        "functions": [ search_function_definitions ],
}
t = time.localtime()
current_time = time.strftime("%H:%M:%S", t)

#############################################################################################
# this is where you put your Autogen logic, here I have a simple 2 agents with a function call
class AutogenChat():
    def __init__(self, chat_id=None, websocket=None):
        self.websocket = websocket
        self.chat_id = chat_id
        self.client_sent_queue = asyncio.Queue()
        self.client_receive_queue = asyncio.Queue()

        self.research_agent = CustomAssistantAgent(
            name="research_agent",
            llm_config=llm_config_assistant,
            system_message="""
            You are an expert researcher and you can do detailed research on any topic and produce facts based results

            YOU DO NOT MAKE THING UP
            
            
            0/If you need more information to solve the task, you can ask the person who posed the question.
            1/ After browse, you should think "Did the previous answer satisfy the question?" If answer is no, continue invoke browse(); But don't do this more than 2 iterations
            2/ You should not make things up, you should only write facts & data that you have gathered
            3/ In the final output, You should include all reference data & links to back up your research;
            When you browse function called number reach 2 or you response the status then don't include any advice just say TERMINATE.
            """
        )
        
        self.raine = autogen.AssistantAgent(
            name="raine",
            llm_config=teachable_llm_config,
            system_message=f"""
            Your name is Raine
            - You are an female assistant for your boss, 
            - Your boss's name is Canh
            - You always use vulgar, Profanity, innuendos but humorous vocabulary in your sentences, you can use F-words.
            """
        )
        
        self.teachability = Teachability(
            reset_db=False,  # Use True to force-reset the memo DB, and False to use an existing DB.
            path_to_db_dir="./assets/tmp/interactive/teachability_db", 
            recall_threshold=1.5,
            verbosity=0
        )
        
        self.user_proxy = UserProxyWebAgent(  
            name="user_proxy",
            human_input_mode="ALWAYS", 
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
            function_map={
                "browse": self.browse
            }
        )
        
        # add the queues to communicate 
        self.user_proxy.set_queues(self.client_sent_queue, self.client_receive_queue)

    async def start(self, message):
        
        # self.teachability.add_to_agent(self.raine)
        
        await self.user_proxy.a_initiate_chat(
            self.research_agent,
            clear_history=True,
            message=message
        )
        
        # await self.user_proxy.a_initiate_chat(
        #     self.research_agent,
        #     clear_history=True,
        #     message=message
        # )

    async def browse(self, query): 
        try:
            researcher = ResearcherAgent(
                name="ResearcherAgent",
            )
                
            data = await researcher.runv1(message=query)
            # data = "bitcoin price now is 63K$"
            # print("data ready for return", data)
            await self.client_receive_queue.put(data)
            return data
        except Exception as e:
            print(e)
            return "Just response to text to user 'There are some bugs on my AI, someone call Canh'"