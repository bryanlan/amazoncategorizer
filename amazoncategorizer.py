import csv
import os
import shutil
import time
from multichatplayground.llminvoker import chat_bot_backend
from multichatplayground.modelindex import model_specs

# Constants
csvFile = r'D:\temp\amazon orders 5.25.24\AmazonRetailOrders1.csv'
outputFile = r'D:\temp\amazon orders 5.25.24\AmazonRetailOrders1_processed.csv'
writeColumn = 2  # Example: write data into the 2nd column (1-based index)
readColumn = 25  # Example: read data from the 25th column (1-based index)
categoryList = ['Groceries', 'Kids Toys and Education', 'Home Maintenance', 'Clothing', 'Medicine and Vitamins', 'General Supplies', 'Electronics', 'Other', 'Dog', 'Books and digital']  # Define your categories
startRow = 2  # Start processing from the 2nd row

# Function to create the prompt for the LLM
def create_prompt(text, categories):
    categories_str = ", ".join(categories)
    prompt = f"Please categorize the following text which describes an amazon purchase into one of the following categories: {categories_str}. Text: \"{text}\" Respond ONLY with the category name which must be one of {categories_str}, no other text."
    return prompt

# Verify if the file exists
if not os.path.exists(csvFile):
    print(f"File not found: {csvFile}")
    exit()

# Copy the original file to create a backup if the output file is empty
if not os.path.exists(outputFile) or os.path.getsize(outputFile) == 0:
    shutil.copyfile(csvFile, outputFile)

# Read the output CSV file and find the first blank row
with open(outputFile, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    rows = list(reader)

total_rows = len(rows)

# Find the first blank row in the output file from startRow onwards
for index in range(startRow - 1, total_rows):
    if len(rows[index]) < writeColumn or not rows[index][writeColumn - 1].strip():
        startRow = index + 1
        break

# Write the updated data back to the CSV file immediately after each row is processed
start_time = time.time()

# Process each row and update the file
for index, row in enumerate(rows, start=1):
    if index >= startRow:
        if len(row) >= readColumn:
            text_to_categorize = row[readColumn - 1]
            prompt = create_prompt(text_to_categorize, categoryList)
            
            # Attempt to get a valid category from the LLM up to 5 times
            for attempt in range(5):
                category = chat_bot_backend([(prompt, "")], "Ollama: phi3", 200, assistantPrompt="")[0].strip()
                if category in categoryList:
                    break
            else:
                category = "LLM_FAILED"
            
            if len(row) >= writeColumn:
                row[writeColumn - 1] = category
            else:
                # Extend the row with empty strings if needed
                row.extend([''] * (writeColumn - len(row) - 1))
                row.append(category)
            
            # Update the row in the file immediately
            rows[index - 1] = row
            
            # Write back the updated rows to the CSV file
            with open(outputFile, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
            
            elapsed_time = time.time() - start_time
            rows_processed = index - startRow + 1
            remaining_rows = total_rows - index
            average_time_per_row = elapsed_time / rows_processed
            estimated_remaining_time = average_time_per_row * remaining_rows
            print(f"Processed {index} row of {total_rows} total, category is {category}. Estimated remaining time: {estimated_remaining_time:.2f} seconds")
