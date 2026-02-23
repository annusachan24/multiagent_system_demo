import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from contants import openai_api_key

async def web_search(query: str) -> str:
    """Find information on the web"""
    return "AutoGen is a programming framework for building multi-agent applications."


# Create an agent that uses the OpenAI GPT-4o model.
model_client = OpenAIChatCompletionClient(
    model="gpt-4.1-nano",
    api_key=openai_api_key,
)


agent = AssistantAgent(
    name="web_search_agent",
    model_client=model_client,
    tools=[web_search],
    system_message="Use tools to solve tasks.",
)

async def main():
    result = await agent.run(task="Find information on AutoGen")
    print(result.messages)
    print()
    print(result.messages[-1].content)


if __name__ == "__main__":
    asyncio.run(main())