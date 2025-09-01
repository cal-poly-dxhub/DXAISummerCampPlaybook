from langchain.agents import initialize_agent, AgentType
from langchain.agents import ZeroShotAgent
from langchain_aws import ChatBedrockConverse
from langchain.tools import Tool

# Step 1: Your tool (same as before)
def calculator(expression: str) -> str:
    try:
        return str(eval(expression))
    except Exception as e:
        return f"❌ Invalid expression: {e}"

tools = [Tool.from_function(
    name="Calculator",
    func=calculator,
    description="Use this tool to evaluate math expressions in Python syntax (e.g., 144 ** 0.5 * 3)."
)]

# Step 2: Claude LLM
llm = ChatBedrockConverse(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region_name="us-west-2",
)

# Step 3: Custom system prompt with instruction to avoid repetition
custom_prefix = """You are a reasoning agent that uses tools to solve problems.
- Use the tools only when needed.
- Once a tool gives you a result (e.g., a number), do not call that tool again with the same input.
- Use prior observations in your final answer if applicable."""

custom_suffix = """Begin!

Question: {input}
{agent_scratchpad}"""

prompt = ZeroShotAgent.create_prompt(
    tools=tools,
    prefix=custom_prefix,
    suffix=custom_suffix,
    input_variables=["input", "agent_scratchpad"]
)

# Step 4: Assemble agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    prompt=prompt,
    verbose=True,
)

# Step 5: Run it
response = agent.invoke({"input": "What is the square root of 144 times 3?"})
print("✅ Final Answer:", response["output"])
