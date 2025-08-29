import boto3
from configparser import ConfigParser

def read_adapter_config(name, key, config_file="adapter.config"):
    config = ConfigParser()
    config.read(config_file)
    return config[name][key]

# Displays information about a block returned by text detection and text analysis
def DisplayBlockInformation(block):
    print('Id: {}'.format(block['Id']))
    if 'Text' in block:
        print('    Detected: ' + block['Text'])
    print('    Type: ' + block['BlockType'])
   
    if 'Confidence' in block:
        print('    Confidence: ' + "{:.2f}".format(block['Confidence']) + "%")

    # Skip Geometry-related information since it's not necessary for query results
    if 'Relationships' in block:
        print('    Relationships: {}'.format(block['Relationships']))

    if 'Page' in block:
        print('Page: ' + block['Page'])
    print()

def process_text_analysis(path):
    client = boto3.client('textract', region_name='us-east-2')
    queriesConfig = { 
        "Queries": [ 
            {
                "Alias": "grantor",
                "Text": "who is the grantor?",
            },
            {
                "Alias": "grantee",
                "Text": "who is the grantee?",
            },
            {
                "Alias": "locatedinCity",
                "Text": "what city is the real property located in?",
            },
            {
                "Alias": "locatedinCounty",
                "Text": "what county is the real property located in?",
            },
            {
                "Alias": "notarizedDate",
                "Text": "when was this form notarized?",
            },
         
        ]
    }

    with open(path, 'rb') as img_file:
        img_bytes = img_file.read()
        response = client.analyze_document(
        Document={'Bytes': img_bytes}, 
        FeatureTypes=["QUERIES"],
        AdaptersConfig={
            "Adapters":[
                {
                    "AdapterId": read_adapter_config("adapter", "ADAPTER_ID"),
                    "Version":"2",
                }
            ]
        },
        QueriesConfig=queriesConfig)

    blocks=response['Blocks']  
    print ('Detected Document Text')

    kvPairs = {}
    for block in blocks:
        if block['BlockType'] == 'QUERY':
            print()  
            print('-' * 50)
            print(f"Query: {block['Query']['Text']}")
            print(f"Query Alias: {block['Query']['Alias']}")
            if 'Relationships' in block:
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'ANSWER':
                        for answer_id in relationship['Ids']:
                            answer_block = next((b for b in blocks if b['Id'] == answer_id), None)
                            if answer_block and 'Text' in answer_block:
                                print(f"    Answer: {answer_block['Text']}") 
                                kvPairs[block['Query']['Alias']] = answer_block['Text']

    return kvPairs

def main():

    block_count=process_text_analysis("sample_data/sample_deeds/helen_grant.pdf")
    print("\nBlocks detected: " + str(block_count))
    
if __name__ == "__main__":
    main()

