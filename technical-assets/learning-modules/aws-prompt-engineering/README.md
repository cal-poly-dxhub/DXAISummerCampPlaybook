
![Prompting Flowchart](./chart.svg)
# Prompt Engineering Advanced Techniques

## Welcome! 👋

This guide covers advanced prompt engineering techniques that will help you get better, more reliable results from AI models tailored to your specific use case.

## 🎛️ Understanding Model Parameters

Before we dive into prompting, let's understand the "knobs and dials" that control how AI models behave.

### Temperature (Number 0-1)
- Tells the model to pick words that have a lower/higher probability of appearing
- **Low (0-0.3)**: Predictable, focused responses
- **High (0.7-1.0)**: Creative, varied responses

### Top P (Nucleus Sampling, Number 0-1)
Controls which words the model considers based on probability.
Chooses words that have probabilites adding up to your Top P
- **Example**: "Today I went to the [park: 50%, store: 30%, moon: 10%, library: 10%]"
- **Top P = 0.8**: Only considers "park" and "store" (80% combined)
- **Lower values = more focused responses**

### Top K
Simply limits to the K most likely next words.
- **Top K = 5**: Only considers the 5 most probable words
- **Use either Temperature OR Top P OR Top K, not all at the same time**

### Other Useful Parameters
- **Max Length**: Stop after X tokens
- **Stop Sequences**: Stop when model outputs specific text (like "END" or "---")
- **Penalties**: Decreases a words probability each time it gets used to avoid repetitive sentences


---

## 📝 Elements of a Good Prompt

Every effective prompt has four key components:

### 1. Instruction
What you want the model to do.
```
"Summarize the following text in 2 sentences."
```

### 2. Context
Background information that helps the model understand.
```
"You are a financial advisor explaining to a college student."
```

### 3. Input Data
The actual content to work with.
```
"Text: [your article here]"
```

### 4. Output Indicator
Format you want back.
```
"Format: Bullet points with key takeaways"
```

### Pro Tips for Better Prompts
- **Be specific and clear** - vague prompts = vague results
- **Use separators** like `---` or `<input>` to organize sections
- **Put instructions first** - models pay more attention to the beginning
- **Focus on what TO DO** instead of what not to do
- **One task per prompt** - break complex requests into steps

---

## Prompting Techniques

### Few-Shot Prompting
Give the model examples to learn from:

```
Classify the movie in <movie> as Positive or Negative:

<Examples>
Example 1:
Review: "Amazing cinematography and great acting!" 
Sentiment: Positive

Example 2:
Review: "Boring plot, terrible dialogue."
Sentiment: Negative
</Examples>

<movie>
Review: "The special effects were incredible but the story dragged."
Sentiment: [model completes this]
</movie>
```

### Chain of Thought Prompting
Ask the model to "think step by step":

```
Problem: If a shirt costs $25 and is on sale for 20% off, what's the final price?

Think through this step by step:
1. Calculate the discount amount
2. Subtract from original price
3. State the final answer
```

### Prompt Chaining
Break complex tasks into smaller steps, where each prompt builds on the previous output.

- **Step 1**: "List the main characters in this story"
- **Step 2**: "For each character from the previous list, describe their motivation"
- **Step 3**: "Identify conflicts between these characters based on their motivations"

### Tree of Thought
Let the model explore multiple approaches and pick the best one:

```
You need to solve this problem. Consider 3 different approaches:

Approach A: [method 1]
Approach B: [method 2] 
Approach C: [method 3]

Evaluate each approach and choose the best one, explaining why.
```

### RAG (Retrieval-Augmented Generation)
Combine external knowledge with the model's built-in knowledge. You retrieve relevant information first, then include it in your prompt as context.

---

## 🎯 Model Choice

Choosing the right model is crucial for balancing performance, cost, and speed:

### Model Categories

### Fast & Cheap
- **Use when:** you need ultra‑low cost, high throughput (simple classification, bulk extraction)  
- **Amazon Model:** Nova Micro — lowest latency, text-only, optimized for speed and minimal cost via Bedrock
- **Anthropic Model:** Claude 3.5 Haiku — fastest Claude variant, outperforms Claude 3 Opus on many tasks at lower cost

---

### Balanced
- **Use when:** you want a balance of reasoning power and cost (creative writing, analysis, moderate complexity)  
- **Amazon Model:** Nova Pro — highly capable multimodal, strong accuracy/cost/speed trade‑off
- **Anthropic Model:** Claude 3.5 Sonnet — well‑rounded performer, midpoint of Claude family;

---

### Premium
- **Use when:** quality and reasoning depth matter most (coding, research, high‑stakes tasks)  
- **Anthropic Model:** Claude Sonnet 4 — latest-mid‑size Claude 4 model, superior instruction following, coding, large context support, and more accurate than 3.7 Sonnet
- **Amazon Model (optional higher tier):** Nova Premier — Amazon’s most capable multimodal model (targeted early 2025 release), ideal for complex reasoning and custom model distillation


### Specialized Models
- **Embeddings**: Amazon Titan Text Embedding v2, Cohere embed
- **Image**: DALL-E, Midjourney, Stable Diffusion

## 📊 Classification Techniques

Classification is one of the most practical applications of prompt engineering:

### Basic Classification
```
Task: Classify customer feedback sentiment

Examples:
"Amazing product, love it!" → Positive
"Terrible quality, waste of money" → Negative
"It's okay, nothing special" → Neutral
```
### Multi-Label Classification
```
Classify this email into categories (can be multiple):
[Urgent, Technical Issue, Billing, Feature Request, Complaint]

Email: "Hi, my subscription was charged twice this month and now the app won't load. This is really frustrating as I need this for work tomorrow."

Categories: Urgent, Technical Issue, Billing, Complaint
```

### Advanced Classification with Confidence
```
Classify the following with confidence scores (0-100):

Text: "I think the new feature might be useful, though I haven't tried it yet."

Classification:
- Positive: 60%
- Negative: 10% 
- Neutral: 30%
```

## 🚩 Using Flags for Better Control

Flags help you control model behavior and get more consistent outputs:

### Content Flags
```python
prompt = """
[FLAG: FAMILY_FRIENDLY] 
[FLAG: FORMAL_TONE]
[FLAG: TECHNICAL_LEVEL_BEGINNER]

Explain how machine learning works.
"""
```

### Processing Flags
```python
prompt = """
[FLAG: STRICT_JSON_OUTPUT]
[FLAG: NO_EXPLANATIONS]
[FLAG: VALIDATE_BEFORE_RESPONSE]

Extract person data: "John Smith, age 25, works as a teacher in Boston"
"""
```

### Custom Behavior Flags
```python
system_prompt = """
You are an AI assistant. Follow these flags:
- [CONCISE]: Keep responses under 100 words
- [EXAMPLES]: Always provide examples
- [CITE_SOURCES]: Include source references when possible
- [STEP_BY_STEP]: Break down complex topics
"""
```

## 🎲 Synthetic Data Generation

Use AI to create training data, test cases, and examples:

### Generating Training Data
```python
prompt = """
Generate 10 customer service conversations about billing issues.
Include realistic customer concerns and helpful agent responses.

Format each as:
Customer: [complaint]
Agent: [helpful response]
Outcome: [Resolved/Escalated]
"""
```

### Creating Test Cases
```python
prompt = """
Generate edge cases for testing a username validation system.
Include: special characters, different lengths, Unicode, spaces, numbers

Format:
Username: [test_case]
Expected: [Valid/Invalid]
Reason: [explanation]
"""
```

### Synthetic Dataset with Structure
```python
from pydantic import BaseModel
from typing import List

class SyntheticUser(BaseModel):
    name: str
    age: int
    occupation: str
    interests: List[str]
    location: str

# Generate diverse, realistic user profiles
prompt = """
Create a realistic user profile for a fitness app.
Include diverse demographics, occupations, and interests.
"""
```

## ⚙️ Parsing and ETL (Extract, Transform, Load)

Transform messy, unstructured data into clean, usable formats:
### Document Processing Pipeline
```python
# Step 1: Extract text sections
extract_prompt = """
Extract these sections from the document:
- Executive Summary
- Key Findings  
- Recommendations
- Budget Information
"""

# Step 2: Transform format
transform_prompt = """
Convert this text into structured bullet points:
- Each point should be actionable
- Include relevant numbers/dates
- Prioritize by importance
"""

# Step 3: Load into database format
load_prompt = """
Format this data for database insertion:
Table: project_reports
Columns: title, summary, findings, budget, priority
"""
```
---

## Structured Output with Python's Instructor Library

The `instructor` library helps you get reliable, structured data from AI models instead of just text.

### Basic Setup
```python
import instructor
import boto3

bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")
client = instructor.from_bedrock(bedrock_client)

class Person(BaseModel):
    name: str
    age: int
    occupation: str

# Get structured output
response = client.chat.completions.create(
      modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
      messages=[{"role": "user", "content": "Extract info: John is 25 and works as a teacher"}],
      response_model=Person,
    )

print(person.name)  # "John"
print(person.age)   # 25
```

### Why This Matters
- **Reliable data extraction** from messy text
- **Perfect for ETL pipelines** (Extract, Transform, Load)
- **Synthetic data generation** with guaranteed structure
- **No more parsing headaches** with inconsistent text formats

---

## 💡 Key Takeaways

1. **Experiment with parameters** - small changes can dramatically improve results
2. **Structure your prompts** with clear instructions, context, input, and output format
3. **Use examples** - few-shot prompting is incredibly powerful
4. **Break down complex tasks** - prompt chaining prevents confusion
5. **Get structured data** - libraries like `instructor` turn AI into reliable data processors


## 📚 Additional Resources

- [Instructor Documentation](https://python.useinstructor.com/) - Complete guide to structured outputs
- [OpenAI API Documentation](https://platform.openai.com/docs) - Official API reference
- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
