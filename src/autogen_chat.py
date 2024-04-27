import autogen
from src.user_proxy_webagent import UserProxyWebAgent
import asyncio
from src.tools.browse.ResearchAgent import ResearcherAgent, search_function_definitions


config_list = [
    {
        "model": "gpt-3.5-turbo",
    }
]
llm_config_assistant = {
    "model":"gpt-3.5-turbo",
    "temperature": 0,
    "config_list": config_list,
        "functions": [ search_function_definitions ],
}
llm_config_proxy = {
    "model":"gpt-3.5-turbo-0613",
    "temperature": 0,
    "config_list": config_list,
}


#############################################################################################
# this is where you put your Autogen logic, here I have a simple 2 agents with a function call
class AutogenChat():
    def __init__(self, chat_id=None, websocket=None):
        self.websocket = websocket
        self.chat_id = chat_id
        self.client_sent_queue = asyncio.Queue()
        self.client_receive_queue = asyncio.Queue()

        self.assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config=llm_config_assistant,
            system_message="""You are a helpful assistant, help the user find the status of his order. 
            You are an expert researcher and you can do detailed research on any topic and produce facts based results by using the function browse()
            
            When you ask a question, always add the word "BRKT"" at the end.
            When you responde with the status add the word TERMINATE
            """
            
        )
        self.user_proxy = UserProxyWebAgent(  
            name="user_proxy",
            human_input_mode="ALWAYS", 
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
            function_map={
                "browse": self.browse
            }
        )

        # add the queues to communicate 
        self.user_proxy.set_queues(self.client_sent_queue, self.client_receive_queue)

    async def start(self, message):
        await self.user_proxy.a_initiate_chat(
            self.assistant,
            clear_history=True,
            message=message
        )

    async def browse(self, query): 
        try:
            researcher = ResearcherAgent(
                name="ResearcherAgent",
            )
                
            data = await researcher.runv1(message=query)
            # data = "bitcoin price now is 63K$"
            # print("data ready for return", data)
            return data
        except Exception as e:
            print(e)
            return "Just response to text to user 'There are some bugs on my AI, someone call Canh'"