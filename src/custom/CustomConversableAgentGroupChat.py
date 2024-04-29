from autogen import Agent, ConversableAgent
import autogen
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
import json
import re
from utils.convert_object import convertObj

try:
    from termcolor import colored
except ImportError:
    def colored(x, *args, **kwargs):
        return x


class CustomConversableAgentGroup(autogen.ConversableAgent):
   
    def _process_received_message(self, message: Union[Dict, str], sender: Agent, silent: bool):
        
        # print("________________process_MSG", message)
        return super()._process_received_message(message, sender, silent)
    
    def _print_received_message(self, message: Union[Dict, str], sender: Agent):
        # print("________________print_MSG", message)
        return super()._print_received_message(message, sender)
    
    def a_send(
        self,
        message: Union[Dict, str],
        recipient: Agent,
        request_reply: Optional[bool] = None,
        silent: Optional[bool] = False,
    ):
        if isinstance(message, str):
            # print("________________MSG", message)
            message = convertObj(message)
        return super().a_send(message, recipient, request_reply, silent)
    
    async def a_check_termination_and_human_reply(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[Agent] = None,
        config: Optional[Any] = None,
    ) -> Tuple[bool, Union[str, None]]:
        
        return super().a_check_termination_and_human_reply(messages, sender, config)