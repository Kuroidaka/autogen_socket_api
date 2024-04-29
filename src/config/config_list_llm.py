import autogen
import os
from autogen import config_list_from_json

local_llama_list = config_list_from_json(
  env_or_file="OAI_CONFIG_LIST",
  filter_dict={
    "model": {
      "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
    }
  }
)

local_mixtral_list = config_list_from_json(
  env_or_file="OAI_CONFIG_LIST",
  filter_dict={
    "model": {
      "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
    }
  }
)

llama3_groq_config_70b = config_list_from_json(
  env_or_file="OAI_CONFIG_LIST",
  filter_dict={
    "model": {
      "llama3-70b-8192",
    }
  }
)

groq_config_list_8b = config_list_from_json(
  env_or_file="OAI_CONFIG_LIST",
  filter_dict={
    "model": {
      "llama3-8b-8192",
    }
  }
)

gpt35_config_list = config_list_from_json(
  env_or_file="OAI_CONFIG_LIST",
  filter_dict={
    "model": {
      "gpt-3.5-turbo",
    }
  }
)

autogen_config_list = llama3_groq_config_70b