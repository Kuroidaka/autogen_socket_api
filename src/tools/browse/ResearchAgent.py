import os
# from autogen.agentchat.contrib.teachable_agent import TeachableAgent
from langchain.agents import AgentExecutor, create_openai_functions_agent, Tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from src.tools.browse.serp_search import search
from src.tools.browse.scrape import scrape, ScrapeWebsiteTool

from langchain.prompts import MessagesPlaceholder
# from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.agents import AgentType
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

search_function_definitions = {
    "name": "browse",
    "description": "search events, data, news, etc for a topic.",
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "query": {
                "type": "string",
                "description": "The query to search for.",
            }
        },
    },
    "required": ["query"],
}

class ResearcherAgent:

    
    
    def __init__(self, name="ResearcherAgent"):
        
        # self.agent = TeachableAgent(
        #     name=name,
        #     llm_config={
        #         "model": "gpt-4-1106-preview",
        #         "temperature": 0,
        #         "max_tokens": 2048,
        #         "functions": self.function_definitions,
        #         "timeout": 600,
        #     },
        #     system_message="", #missing system msg
        #     default_auto_reply="Researcher Agent: I am a researcher agent. I can interact with the research user proxy agent to perform tasks related to research",
        #     teach_config={
        #         "verbosity": 0,
        #         "reset_db": False,
        #         "path_to_db_dir": "./assets/tmp/interactive/teachability_db/research",
        #         "recall_threshold": 1.5,
        #         "timeout": 600,
        #     },
        # )
        
        self.tools = [
            Tool(
                name="Search",
                func=search,
                description="useful for when you need to answer questions about current events, data. You should ask targeted questions"
            ),
            ScrapeWebsiteTool(),
        ]
        
        self.system_messageV1 = """
        You are an expert researcher and you can do detailed research on any topic and produce facts based results, 
        YOU DO NOT MAKE THING UP
        you will try as hard as possible to gather facts & data to back up the research, if there are no information relate to the provided task then just tell it to user
            You have 6 main responsibilities:
            1/ You always use Search() to find the information relate to that provided task. You should do enough research to gather as much information as possible about the objective
            2/ If there are url of relevant links & articles, you can use scrape_website() to find the detail data to gather more information from a website url, but if the information is enough you can response no need to use scrape_website() anymore
            3/ You should not make things up, you should only write facts & data that you have gathered
            5/ In the final output, You should include all reference data & links to back up your research; You should include all reference data & links to back up your research
            6/ In the final output, You should include all reference data & links to back up your research; You should include all reference data & links to back up your research
        """

     
     
    def get_agent(self):
        return self.agent
    
    async def runv1(self, message):     
        try:   
            # llm = ChatGroq(
            #     temperature=0,
            #     model_name="llama3-70b-8192",
            #     groq_api_key=os.getenv("GROQ_API_KEY")
            # )
            
            llm = ChatOpenAI(
                model='gpt-3.5-turbo-1106',
                temperature=0.7
            )
            tools = self.tools
            
            chat_template = ChatPromptTemplate.from_messages(
                [
                    ("system", self.system_messageV1),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )

            

            prompt = chat_template
            agent = create_openai_functions_agent(llm, tools, prompt)

            agent_executor = AgentExecutor(
                agent=agent, tools=tools, verbose=True, max_iterations=3
            )

            demo_ephemeral_chat_history_for_chain = ChatMessageHistory()

            conversational_agent_executor = RunnableWithMessageHistory(
                agent_executor,
                lambda session_id: demo_ephemeral_chat_history_for_chain,
                input_messages_key="input",
                output_messages_key="output",
                history_messages_key="chat_history",
            )

            actual_content = await conversational_agent_executor.ainvoke(
                {"input": message},
                {"configurable": {"session_id": "unused"}},
            )
            
            return actual_content.get("output")
        except Exception as e:
            print(e)
            msg="There are some bugs on my AI, someone call Canh"
            print(msg)
            return msg
# Usage
# researcher = ResearcherAgent(
#     name="ResearcherAgent",
# )
        
# data = await researcher.runv1(message)