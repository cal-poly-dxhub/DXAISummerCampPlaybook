import boto3
import json
import math
from typing import List, Dict


def cosine_similarity(a: List[float], b: List[float]):
  dot = sum(x * y for x, y in zip(a, b))
  norm_a = math.sqrt(sum(x * x for x in a))
  norm_b = math.sqrt(sum(y * y for y in b))
  if norm_a == 0 or norm_b == 0:
    return 0.0
  return round(dot / (norm_a * norm_b), 3)

def output_similarities(pipeline_results: List[Dict[str, List[float]]]):
  sims: List[Dict[str, object]] = []
  n = len(pipeline_results)
  for i in range(n):
    for j in range(i + 1, n):
      a = pipeline_results[i]
      b = pipeline_results[j]
      sim = cosine_similarity(a['embedding'], b['embedding'])
      sims.append({
        'text_a': a['text'],
        'text_b': b['text'],
        'similarity': sim
      })
  with open('cosine_similarities.json', 'w') as f:
    json.dump(sims, f, indent=2)

def get_embedding(text: str):
  client = boto3.client('bedrock-runtime', region_name="us-west-2")
  response = client.invoke_model(
    modelId="amazon.titan-embed-text-v2:0",
    body=json.dumps({'inputText': text})
  )
  body = response['body'].read().decode()
  result = json.loads(body)
  return result.get('embedding', [])

def main() -> None:
  texts = [
    "Hello, world!",
    "Hello Everyone!",
    "AWS Bedrock Titan embeddings are cool.",
    "This is a simple example."
  ]

  with open('test_embed.txt', 'r', encoding='utf-8') as f:
    try:
      file_content = f.read().strip()
      if file_content:
        texts.append(file_content)
    except FileNotFoundError:
      print("test_embed.txt not found. Using default texts.")
    except Exception as e:
      print(f"An error occurred while reading the file: {e}")

  pipeline_results: List[Dict[str, List[float]]] = []
  for text in texts:
    embedding = get_embedding(text)
    pipeline_results.append({
      'text': text,
      'embedding': embedding
    })

  with open('embeddings_output.json', 'w') as f:
    json.dump(pipeline_results, f, indent=2)

  output_similarities(pipeline_results)


if __name__ == '__main__':
  main()