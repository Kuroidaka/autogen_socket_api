from typing import Callable, Dict, List, Literal, Optional, Union

from autogen.runtime_logging import log_new_agent, logging_enabled
from src.custom.CustomConversableAgent import CustomConversableAgent


class CustomUserProxyAgent(CustomConversableAgent):
    # Default UserProxyAgent.description values, based on human_input_mode
    DEFAULT_USER_PROXY_AGENT_DESCRIPTIONS = {
        "ALWAYS": "An attentive HUMAN user who can answer questions about the task, and can perform tasks such as running Python code or inputting command line commands at a Linux terminal and reporting back the execution results.",
        "TERMINATE": "A user that can run Python code or input command line commands at a Linux terminal and report back the execution results.",
        "NEVER": "A computer terminal that performs no other action than running Python scripts (provided to it quoted in ```python code blocks), or sh shell scripts (provided to it quoted in ```sh code blocks).",
    }

    def __init__(
        self,
        name: str,
        is_termination_msg: Optional[Callable[[Dict], bool]] = None,
        max_consecutive_auto_reply: Optional[int] = None,
        human_input_mode: Literal["ALWAYS", "TERMINATE", "NEVER"] = "ALWAYS",
        function_map: Optional[Dict[str, Callable]] = None,
        code_execution_config: Union[Dict, Literal[False]] = {},
        default_auto_reply: Optional[Union[str, Dict, None]] = "",
        llm_config: Optional[Union[Dict, Literal[False]]] = False,
        system_message: Optional[Union[str, List]] = "",
        description: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            system_message=system_message,
            is_termination_msg=is_termination_msg,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            human_input_mode=human_input_mode,
            function_map=function_map,
            code_execution_config=code_execution_config,
            llm_config=llm_config,
            default_auto_reply=default_auto_reply,
            description=(
                description if description is not None else self.DEFAULT_USER_PROXY_AGENT_DESCRIPTIONS[human_input_mode]
            ),
        )

        if logging_enabled():
            log_new_agent(self, locals())
