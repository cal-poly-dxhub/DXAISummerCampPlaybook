# AWS Bedrock Tools & Converse API Demo

This learning module demonstrates how to create agent-like behavior with Amazon Bedrock models by utilizing the Converse API and tools functionality. The module includes two implementations:

1. A direct implementation using Bedrock's Converse API with Streamlit
2. A LangChain-based implementation that simplifies tool creation and agent workflows

## Prerequisites

- AWS account with Bedrock access
  - Specific model access to Claude 3 Sonnet (anthropic.claude-3-sonnet-20240229-v1:0)
  - Bedrock model access must be granted in the AWS console
- Python 3.11 or higher
- Proper AWS credentials configured locally
  - Run `aws configure` to set up your credentials
  - Or set environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`

## Installation

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd DXAISummerCampPlaybook/technical-assets/learning-modules/aws-bedrock-tools-converse

# Install uv (if not already installed)
pip install uv

# Install dependencies using uv
uv sync

# Or alternatively, install in development mode
uv pip install -e .
```

## File Structure

- `converse_streamlit.py`: Direct implementation of Bedrock's Converse API with tools
- `langchain_demo.py`: LangChain-based implementation for simplified agent creation
- `pyproject.toml`: Project dependencies

## Implementation 1: Direct Bedrock Converse API (Streamlit App)

The `converse_streamlit.py` file demonstrates how to use Amazon Bedrock's Converse API directly to create a tool-using agent with:

- A date tool that provides the current date
- A web search tool using DuckDuckGo to find current information

### Key Features

- **Tool Configuration**: Defines tool specifications with descriptions and input schemas
- **Tool Execution**: Routes tool calls to appropriate Python functions
- **Conversational Loop**: Manages the back-and-forth between the model and tools
- **Streamlit UI**: Provides a simple interface for interacting with the agent

### How to Run

```bash
streamlit run converse_streamlit.py
```

## Implementation 2: LangChain with Bedrock Converse

The `langchain_demo.py` file shows how to use LangChain's abstractions to simplify the creation of a tool-using agent with Amazon Bedrock's Converse API.

### Key Features

- **Tool Definition**: Creates a calculator tool using LangChain's Tool abstraction
- **Custom Prompting**: Uses ZeroShotAgent with custom prompts to guide the model
- **Agent Creation**: Initializes a ReAct-style agent with the Claude 3 Sonnet model
- **Simplified Interface**: Demonstrates LangChain's simplified agent invocation

### How to Run

```bash
python langchain_demo.py
```

## Key Concepts

1. **Tool Definition**: Tools are functions that models can use to extend their capabilities

   - Must be defined with clear descriptions and input/output schemas

2. **Agent Loop**:

   - Model analyzes the user's question
   - Model decides whether to use tools or answer directly
   - If using tools, outputs are routed back to the model
   - Process repeats until model provides final answer

3. **Advantages of LangChain**:
   - Simpler API for defining tools
   - Built-in agent architectures (like ReAct)
   - Easier prompt management
   - Simplified execution loop

## Example Use Cases

- Building specialized agents that can:
  - Perform calculations
  - Search for information
  - Access current date/time
  - Integrate with external APIs and services

## AWS Bedrock Models

This demo uses Claude 3 Sonnet via Amazon Bedrock, but can be adapted to work with other models that support tool use, including Claude 3 (Haiku, Sonnet, Opus) and all newer anthropic models

## Notes

- Ensure your AWS credentials have proper permissions for Bedrock
- The search functionality requires internet access
- For production use, consider rate limiting and error handling

## Additional Resources

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock Converse API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [Streamlit Documentation](https://docs.streamlit.io/)
