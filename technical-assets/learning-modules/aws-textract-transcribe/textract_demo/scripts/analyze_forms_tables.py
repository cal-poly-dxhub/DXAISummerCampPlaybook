import boto3

# Initialize Textract client
textract = boto3.client('textract')

# Local document path
document_path = 'sample_data/club_registration_form.pdf'

# Read document bytes
with open(document_path, 'rb') as doc_file:
    document_bytes = doc_file.read()

# Call Textract AnalyzeDocument API for FORMS and TABLES
response = textract.analyze_document(
    Document={'Bytes': document_bytes},
    FeatureTypes=['FORMS', 'TABLES']
)

# Create containers to store results
form_fields = []
table_cells = []

# Build a lookup table of blocks by ID
blocks_map = {block['Id']: block for block in response['Blocks']}

# Extract key-value pairs
for block in response['Blocks']:
    if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
        key_text = ''
        value_text = ''

        # Get key text
        for rel in block.get('Relationships', []):
            if rel['Type'] == 'CHILD':
                for cid in rel['Ids']:
                    word = blocks_map.get(cid)
                    if word and word['BlockType'] == 'WORD':
                        key_text += word['Text'] + ' '

        # Get value block and text
        for rel in block.get('Relationships', []):
            if rel['Type'] == 'VALUE':
                for vid in rel['Ids']:
                    value_block = blocks_map.get(vid)
                    if value_block:
                        for vrel in value_block.get('Relationships', []):
                            if vrel['Type'] == 'CHILD':
                                for cid in vrel['Ids']:
                                    word = blocks_map.get(cid)
                                    if word and word['BlockType'] == 'WORD':
                                        value_text += word['Text'] + ' '

        form_fields.append((key_text.strip(), value_text.strip()))

# Extract table cells
for block in response['Blocks']:
    if block['BlockType'] == 'CELL':
        row = block['RowIndex']
        col = block['ColumnIndex']
        cell_text = ''

        for rel in block.get('Relationships', []):
            if rel['Type'] == 'CHILD':
                for cid in rel['Ids']:
                    word = blocks_map.get(cid)
                    if word and word['BlockType'] == 'WORD':
                        cell_text += word['Text'] + ' '

        table_cells.append((row, col, cell_text.strip()))

# Print extracted form fields
print("\n=== FORMS (Key-Value Pairs) ===")
for key, value in form_fields:
    print(f"{key} : {value}")

# Print extracted table cells
print("\n=== TABLES ===")
for row, col, text in table_cells:
    print(f"Row {row}, Column {col}: {text}")
    

# Optional: Save results to file
with open("textract_output.txt", "w") as f:
    f.write("=== FORMS ===\n")
    for key, value in form_fields:
        f.write(f"{key} : {value}\n")
    f.write("\n=== TABLES ===\n")
    for row, col, text in table_cells:
        f.write(f"Row {row}, Column {col}: {text}\n")


print("\nResults saved to textract_output.txt")
