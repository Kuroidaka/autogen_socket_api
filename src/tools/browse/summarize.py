from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound
from langchain_openai import ChatOpenAI

async def summary(content, objective):
    try:
        # Create an instance of the language model with specific parameters
        llm = ChatGroq(temperature=0, model="mixtral-8x7b-32768")

        # llm = ChatOpenAI(
        #     model='gpt-3.5-turbo-16k-0613',
        #     temperature=0.7
        # )
        # Define the text splitter configuration
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n"], chunk_size=10000, chunk_overlap=500)

        # Assuming 'content' is defined elsewhere in your code
        docs = text_splitter.create_documents([content])

        # Define the map prompt template
        map_prompt = """
        Write a detailed summary of the following text for {objective}:
        {text}
        SUMMARY:
        """
        map_prompt_template = PromptTemplate(
            template=map_prompt, input_variables=["text", "objective"])

        # Load the summarize chain with the language model and prompts
        summary_chain = load_summarize_chain(
            llm=llm,
            chain_type='map_reduce',
            map_prompt=map_prompt_template,
            combine_prompt=map_prompt_template,
            verbose=True
        )
        

        # Invoke the summary chain with the prepared input
        output = await summary_chain.ainvoke(input={'input_documents': docs, 'objective': objective})
        output_text = output['output_text']

        return output_text
    except Exception as e:
        print(f"SUMMARIZE: An error occurred: {str(e)}")
        raise InternalServerError(f"SUMMARIZE: An error occurred: {str(e)}")