# Cal Poly AI Summer Camp: Generate Vector Embeddings for Text

Welcome to our AI Summer Camp! This project will teach you how to use Large Language Models (LLMs) to generate text embeddings and calculate semantic similarity between different texts. You'll learn how to transform text into numerical vectors and measure how similar different pieces of text are to each other using Python and AWS Bedrock.

## Contact Information

**Instructor**: Ryan Gertz - rgertz@calpoly.edu

Feel free to reach out if you have questions about:
- Setting up AWS credentials
- Understanding embedding concepts
- Troubleshooting errors
- Ideas for extending this project
- General questions about AI and text similarity analysis

## Video Tutorial
- For a walkthrough of installing VS Code and Python on windows [check this video out](https://drive.google.com/file/d/1hwVswLDUorcEJJz8gbOUracmx9Ufj3QE/view?usp=sharing)

- For a walkthrough of setting up a Virtual Environment with python in VS Code [check this repository out](https://github.com/RyanGertz/ai-summercamp-scripts)

- For a complete walkthrough of this project, check out my video explanation:
[AI Summer Camp Tutorial - Generating Vector Embeddings with AWS Bedrock](https://drive.google.com/file/d/1L0xaXiEZtAuLccpL0L2K7PkZeh4dQp3m/view?usp=sharing)

## What You'll Learn

- **Vector Embeddings**: Converting text/data into numerical vectors that capture semantic meaning
- **Cosine Similarity**: Mathematical method to measure how similar two vectors are
- **AWS Bedrock Titan**: Amazon's embedding model

## What This Code Does

This project demonstrates how to use AI to analyze text similarity through embeddings. The code:

1. **Connects to AWS Bedrock**: Uses Amazon Titan embedding model to convert text to vectors
2. **Generates Text Embeddings**: Creates numerical representations of text that capture meaning
3. **Calculates Cosine Similarity**: Measures how similar different texts are to each other
4. **Saves Results**: Outputs embeddings and similarity scores to JSON files

## Prerequisites

Before you start, you'll need:

### 1. Python Installation
- Python 3.7 or higher installed on your computer
- You can download it from [python.org](https://www.python.org/downloads/)
- You can also watch [my video](https://drive.google.com/file/d/1hwVswLDUorcEJJz8gbOUracmx9Ufj3QE/view?usp=drive_link) explaning how to install it on Windows

### 2. AWS Account Setup
- An AWS account
- AWS credentials configured on your computer
- Access to AWS Bedrock service and Amazon Titan embedding model

### 3. Required Python Packages
Install the necessary packages by running this command in your terminal:
```bash
pip install boto3
```

## Understanding the Code

### Key Components

**boto3**: Amazon's Python library that lets us connect to AWS services. Think of it as a bridge between your Python code and Amazon's AI models.

**Vector Embeddings**: High-dimensional numerical vectors that represent the meaning of data. Similar data will have similar embeddings.

**Cosine Similarity**: A mathematical measure that calculates how similar two vectors are, ranging from 0 (completely different) to 1 (identical).

**Amazon Titan V2**: Amazon's embedding model that converts data into high-quality vector representations.

### The Functions Explained

#### Function 1: `cosine_similarity(a, b)`
This function calculates how similar two embedding vectors are:
- Takes two lists of numbers (embeddings) as input
- Computes the dot product and norms of both vectors
- Returns a similarity score between 0 and 1 (note cosine similarity can be [-1,1])

#### Function 2: `get_embedding(text)`
This function converts text into embedding vectors:
- Connects to AWS Bedrock Titan embedding model
- Sends text to the model for processing
- Returns a list of numbers representing the text's meaning
- Each embedding is a vector of 1,024 dimensions

#### Function 3: `output_similarities(pipeline_results)`
This function compares all texts with each other:
- Takes a list of text-embedding pairs
- Calculates cosine similarity for every pair combination
- Saves all similarity scores to a JSON file

#### Function 4: `main()`
This is the main function that orchestrates the entire process:
- Generates embeddings for all texts
- Saves embeddings and outputs cosine similarities

## How to Run the Code

1. **Save the code**: Clone this repo or copy the code into a file called `text_similarity.py`

2. **Open your terminal/command prompt**

3. **Navigate to your project folder**:
   ```bash
   cd path/to/your/project
   ```

4. **Run the code**:
   ```bash
   python text_similarity.py
   ```

5. **Check the output**: Look for these files in your project folder:
   - `embeddings_output.json` - Contains all text embeddings
   - `cosine_similarities.json` - Contains similarity scores between all text pairs

## Customizing The Code

### Add Your Own Text
Create a file called `test_embed.txt` and add any text you want to analyze:
```
This is my custom text that I want to compare with the other examples.
```

### Change the Default Texts
Modify the texts list in the `main()` function:
```python
texts = [
    "Your custom text here",
    "Another piece of text",
    "Machine learning is fascinating",
    "AI will change the world"
]
```

## Understanding the Generated Data

### Embeddings Output (`embeddings_output.json`)
Contains arrays of text-embedding pairs:
```json
[
  {
    "text": "Hello, world!",
    "embedding": [0.123, -0.456, 0.789, ...]
  }
]
```

### Similarities Output (`cosine_similarities.json`)
Contains similarity scores for all text pairs:
```json
[
  {
    "text_a": "Hello, world!",
    "text_b": "Hello Everyone!",
    "similarity": 0.509
  }
]
```

## Common Issues and Solutions

### "No credentials found"
This means your AWS credentials aren't set up. You need:
- AWS Access Keys
- AWS CLI configuration
- IAM permissions for Bedrock

### "Access denied to model"
Your AWS account might not have permission to use Titan embeddings:
- Check your AWS Bedrock model access
- Ensure you have the correct model ID
- Verify your IAM permissions

### "Module not found: boto3"
Install the required package:
```bash
pip install boto3
```

### "ValidationException"
This usually means the input text is empty or invalid:
- Check that your text inputs are not empty
- Ensure text is properly formatted
- Try with shorter text if you're hitting length limits

### "test_embed.txt not found"
This is normal - the file is optional:
- Create the file if you want to add custom text
- The code will work fine without it using default texts

## Important Notes

- **Cost Awareness**: Each embedding generation costs money (usually fractions of a cent per request)
- **Rate Limits**: AWS has limits on how many requests you can make per minute
- **Vector Dimensions**: Titan embeddings are 1,024-dimensional vectors
- **Text Length**: There are limits on how long your input text can be

## Use Cases for Text Similarity Analysis

This type of similarity analysis is useful for:
- **Content Recommendation**: Find similar articles or documents
- **Duplicate Detection**: Identify duplicate or near-duplicate content
- **Search Applications**: Improve search by finding semantically similar content
- **Content Clustering**: Group similar content together
- **Plagiarism Detection**: Identify potentially copied content

## Getting Help

If you run into issues:
1. Check the error message carefully
2. Ask our camp staff for assistance
3. Look up the specific error message online
4. Try running the code with shorter texts first
5. Verify your AWS credentials are working

## Example Results

After running the code, you might see similarity scores like:
- "Hello, world!" vs "Hello Everyone!" = 0.509 (very similar greetings)
- "AWS Bedrock Titan embeddings are cool." vs "Hello, world!" = 0.095 (different topics)

## Resources for Further Learning

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Vector Embedding Video](https://www.youtube.com/watch?v=NEreO2zlXDk)
- [Vector Embeddings Reading](https://aws.amazon.com/what-is/embeddings-in-machine-learning/)
- [Understanding Text Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [Cosine Similarity Wiki](https://en.wikipedia.org/wiki/Cosine_similarity)
- [Cosine Similarity Video](https://www.youtube.com/watch?v=e9U0QAFbfLI)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Vector Similarity Search](https://aws.amazon.com/what-is/vector-databases/)

---

Happy coding! 🚀
