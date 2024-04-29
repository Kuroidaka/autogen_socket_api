import autogen
from autogen import Agent
from src.user_proxy_webagent import UserProxyWebAgent
from src.groupchatweb import GroupChatManagerWeb
import asyncio
from autogen.agentchat.contrib.capabilities.teachability import Teachability
from datetime import date
import time

from src.custom.CustomAssistantAgent import CustomAssistantAgent
from src.tools.browse.ResearchAgent import ResearcherAgent, search_function_definitions
from src.config.config_list_llm import autogen_config_list, llama3_groq_config_70b, gpt35_config_list

llama70_llm_config = {
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


loyalPrompt = "You are an assistant for your boss, your boss's name is Cảnh with full name is Phạm Doãn Cảnh"




#############################################################################################
# this is where you put your Autogen logic, here I have a simple 2 agents with a function call# Main Autogen Chat class
class AutogenChat():
    def __init__(self, chat_id=None, websocket=None):
        self.websocket = websocket
        self.chat_id = chat_id
        self.client_sent_queue = asyncio.Queue()
        self.client_receive_queue = asyncio.Queue()

        # Define agents

        self.research_agent = CustomAssistantAgent(
            name="research_agent",
            llm_config=research_agent_llm_config,
            system_message="""
            You are an expert researcher and you can do detailed research on any topic and produce facts based results

            YOU DO NOT MAKE THING UP
            
            
            0/If you need more information to solve the task, you can ask the person who posed the question.
            1/ After browse, you should think "Did the previous answer satisfy the question?" If answer is no, continue invoke browse(); But don't do this more than 2 iterations
            2/ You should not make things up, you should only write facts & data that you have gathered
            3/ In the final output, You should include all reference data & links to back up your research;
            When you browse function called number REACH 2 or you response the status then don't include any advice just say TERMINATE.
            """
        )
 
        self.teachability = Teachability(
            reset_db=False,  # Use True to force-reset the memo DB, and False to use an existing DB.
            path_to_db_dir="./assets/tmp/interactive/teachability_db", 
            recall_threshold=1.5,
            verbosity=0
        )
        self.Raine = CustomAssistantAgent(
            name="Raine",
            llm_config=llama70_llm_config,
            system_message=f"""
                with the name Raine, 
                - You are an assistant for your boss, 
                - You are a female programmed to provide both humorous and helpful responses.
                - IMPORTANT: you do not make up thing relate to (realtime-event, personal information)
                
                Send to Planner: If you need assistance with a task or problem, do not attempt to solve it yourself or offer any advice. Instead, interact directly with the "Planner" to discuss the plan. Ensure to include "Planner" in your communication.
            """,
        )
        
        self.teachable_agent = CustomAssistantAgent(
            name="teachable_agent",
            llm_config=llama70_llm_config,
        )
        
        self.planner = CustomAssistantAgent(
            name="Planner",
            system_message=f'''
            As a knowledgeable assistant, determine the most appropriate skill to address the given task. 
            initiate a planning process to ensure completion. Start by proposing a plan, then refine it based on feedback from Raine until it gains the Raine's approval. 
            
            The plan will primarily involve:
            - Research Agent: This agent specializes in research tasks that focus on current events, real-time updates, and internet resources, but does not include information from the current user's inquiry.
            (Using the Research Agent is optional and may not always be necessary.)
            
            Clearly explain the plan at the outset. Specify which steps the Research Agent will manage.''',
            llm_config=llama70_llm_config,
        )        

    #     critic = autogen.AssistantAgent(
    #     name="Critic",
    #     system_message="""Critic. You are a helpful assistant highly skilled in evaluating the quality of a given visualization code by providing a score from 1 (bad) - 10 (good) while providing clear rationale. YOU MUST CONSIDER VISUALIZATION BEST PRACTICES for each evaluation. Specifically, you can carefully evaluate the code across the following dimensions
    # - bugs (bugs):  are there bugs, logic errors, syntax error or typos? Are there any reasons why the code may fail to compile? How should it be fixed? If ANY bug exists, the bug score MUST be less than 5.
    # - Data transformation (transformation): Is the data transformed appropriately for the visualization type? E.g., is the dataset appropriated filtered, aggregated, or grouped  if needed? If a date field is used, is the date field first converted to a date object etc?
    # - Goal compliance (compliance): how well the code meets the specified visualization goals?
    # - Visualization type (type): CONSIDERING BEST PRACTICES, is the visualization type appropriate for the data and intent? Is there a visualization type that would be more effective in conveying insights? If a different visualization type is more appropriate, the score MUST BE LESS THAN 5.
    # - Data encoding (encoding): Is the data encoded appropriately for the visualization type?
    # - aesthetics (aesthetics): Are the aesthetics of the visualization appropriate for the visualization type and the data?

    # YOU MUST PROVIDE A SCORE for each of the above dimensions.
    # {bugs: 0, transformation: 0, compliance: 0, type: 0, encoding: 0, aesthetics: 0}
    # Do not suggest code.
    # Finally, based on the critique above, suggest a concrete list of actions that the coder should take to improve the code.
    # """,
    #     llm_config=llm_config,
    # )
    
        self.user_proxy = UserProxyWebAgent(
            name="user_proxy",
            human_input_mode="ALWAYS", 
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
            function_map={
                "browse": self.browse
            }
        )
        self.user_proxy.set_queues(self.client_sent_queue, self.client_receive_queue)

        # GroupChat setup
        self.groupchat = autogen.GroupChat(
            agents=[self.user_proxy, self.Raine, self.planner, self.research_agent], 
            messages=[], 
            max_round=30,
            allow_repeat_speaker=False,
            speaker_selection_method=self.custom_speaker_selection_func,
        )
        self.manager = GroupChatManagerWeb(groupchat=self.groupchat, llm_config=llama70_llm_config, human_input_mode="ALWAYS")

    
    def custom_speaker_selection_func(self, last_speaker: Agent, groupchat: autogen.GroupChat):
        messages = groupchat.messages

        if len(messages) <= 1:
            return self.Raine
        elif last_speaker is self.planner and messages[-2]["name"] == "Raine":
            # Always let the user to speak after the planner
            return "auto"
        elif last_speaker is self.Raine:
            if "Planner" in messages[-1]["content"]:
                return self.planner

        if last_speaker is self.research_agent:
            if messages[-1]["content"]:
                return self.user_proxy
            
        # If Planner is active and task is ongoing
        # if last_speaker is self.planner:
        #     if not self.planner.task_completed:
        #         # Continue with Planner until task is done
        #         return "auto"
        #     else:
        #         # Once task is done, return control to Raine
        #         return self.Raine

        # Once Raine gets the turn back after task completion
        if last_speaker is self.Raine and "TERMINATE" in  messages[-2]["content"]:
            # Return to user after Raine's response post-task
            return self.user_proxy

        # Default to random if none of the above conditions are met
        return "random"
        
    async def start(self, message):

        self.teachability.add_to_agent(self.Raine)
        
        await self.user_proxy.a_initiate_chat(self.manager, clear_history=True, message=message)

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