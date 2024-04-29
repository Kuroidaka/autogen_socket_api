from src.user_proxy_webagent import UserProxyWebAgent
from src.groupchatweb import GroupChatManagerWeb
import asyncio
import autogen
from autogen import ConversableAgent
from autogen.agentchat.contrib.capabilities.teachability import Teachability

from src.user_proxy_webagent import UserProxyWebAgent
from src.custom.CustomAssistantAgent import CustomAssistantAgent
from src.tools.browse.ResearchAgent import ResearcherAgent, search_function_definitions
from src.config.config_list_llm import autogen_config_list, llama3_groq_config_70b, gpt35_config_list




raine_llm_config = {
    "model":"llama3-70b-8192",
    "temperature": 0,
    "config_list": llama3_groq_config_70b,
}

research_agent_llm_config = {
    "model":"llama3-70b-8192",
    "temperature": 0,
    "config_list": llama3_groq_config_70b,
        "functions": [ search_function_definitions ],
}

gpt35_agent_config_list = {
    "model":"gpt-3.5-turbo",
    "temperature": 0,
    "config_list": gpt35_config_list,
}

teachable_llm_config = {
    "config_list": autogen_config_list
}

loyalPrompt = "You are an assistant for your boss, your boss's name is Cảnh with full name is Phạm Doãn Cảnh"



#############################################################################################
# this is where you put your Autogen logic, here I have a simple 2 agents with a function call
class AutogenChat():
    def __init__(self, chat_id=None, websocket=None):
        self.websocket = websocket
        self.chat_id = chat_id
        self.client_sent_queue = asyncio.Queue()
        self.client_receive_queue = asyncio.Queue()

        self.assistant = autogen.AssistantAgent(
            name="Raine",
            llm_config=raine_llm_config,
            system_message=f"""
            You are an expert Assistant name Raine, {loyalPrompt}
            When you ask a question, always add the word "BRKT"" at the end.
            When you responde with the status add the word TERMINATE
            """
        )
        
        self.research_agent = CustomAssistantAgent(
            name="research_agent",
            llm_config=research_agent_llm_config,
            system_message="""
            You are an expert researcher and you can do detailed research on any topic and produce facts based results

            YOU DO NOT MAKE THING UP
            
            1/ After browse, you should think "is there any new things i should search & scraping based on the data I collected to increase research quality?" If answer is yes, continue invoke browse(); But don't do this more than 2 iterations
            2/ You should not make things up, you should only write facts & data that you have gathered
            3/ In the final output, You should include all reference data & links to back up your research;
            When you browse function called number reach 2 or you response the status then use TERMINATE at the end
            """
        )
        
        self.teachable_agent = autogen.AssistantAgent(
            name="teachable_agent",
            llm_config=teachable_llm_config,
            system_message="You have the great ability to remember things that relate to user's comment, you will try to remember the relate task or things that user mentioned"
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
            system_message="""You ask for ideas for a specific topic""",
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
        )

        self.critic = autogen.AssistantAgent(
            name="Critic",
            system_message="Critic. Double check plan, claims, code from other agents and provide feedback. Check whether the plan includes adding verifiable info such as source URL.",
            llm_config=gpt35_agent_config_list,
        )

        # add the queues to communicate 
        self.user_proxy.set_queues(self.client_sent_queue, self.client_receive_queue)

        self.allowed_speaker_transitions_dict = {
            self.user_proxy: [self.critic, self.teachability, self.research_agent],
            self.critic: [self.user_proxy, self.teachability, self.research_agent],
            self.teachability: [self.user_proxy, self.critic, self.research_agent],
            self.research_agent: [self.user_proxy, self.critic, self.teachability]
        }
        
        self.groupchat = autogen.GroupChat(
            agents=[self.user_proxy, self.critic, self.teachability, self.research_agent],
            messages=[],
            max_round=10,
            admin_name="Raine"
        )
        
        self.manager = GroupChatManagerWeb(
            groupchat=self.groupchat, 
            llm_config=gpt35_agent_config_list,
            human_input_mode="ALWAYS",
            allowed_speaker_transitions_dict=self.allowed_speaker_transitions_dict
        )     

    async def start(self, message):
        await self.user_proxy.a_initiate_chat(
            self.manager,
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

