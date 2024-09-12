import pandas as pd
import os
from parse_code import *
import Levenshtein as lev
import json
import subprocess
from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import AutoModel, AutoTokenizer

checkpoint = "WhereIsAI/UAE-Code-Large-V1"
device = "cpu"  # for GPU usage or "cpu" for CPU usage

tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
model = AutoModel.from_pretrained(checkpoint, trust_remote_code=True).to(device)


def extract_structure(code, file_type):
    if file_type == 'py':
        # Python file
        return extract_python_structure(code, file_type)
    elif file_type in ('js', 'jsx', 'ts', 'tsx', 'vue'):
        # JS family files
        return extract_js_structure(code, file_type)
    elif file_type == 'html':
        # HTML file
        return extract_html_structure(code)
    elif file_type == 'css' or file_type == 'scss':
        # CSS file
        return extract_css_structure(code, file_type)
    else:
        return None


def clean_code_string(code_string):
    # Remove ```<language> if it exists
    code_string = re.sub(r'```.*?$', '', code_string, flags=re.MULTILINE, count=1)
    

    # Remove lines starting with a capital letter
    code_string = re.sub(r'^[A-Z].*$', '', code_string, flags=re.MULTILINE)

    # Remove everything after the closing ```
    code_string = code_string.split('```')[0]

    return code_string.strip()

def count_loc(code_str, exclude_empty=True, exclude_comments=True):
    lines = code_str.splitlines()
    loc = 0
    
    for line in lines:
        stripped_line = line.strip()
        
        if exclude_empty and not stripped_line:
            continue
        
        if exclude_comments:
            # Simple comment exclusion (works for single-line comments in many languages)
            if stripped_line.startswith("#") or stripped_line.startswith("//") or stripped_line.startswith("--"):
                continue
            # For languages with block comments, you may need a more complex parser
        
        loc += 1
    
    return loc


def normalized_loc_difference(code1, code2):
    loc1, loc2 = count_loc(code1), count_loc(code2)
    
    if max(loc1, loc2) == 0:
        return 0
    return abs(loc1 - loc2) / max(loc1, loc2)


def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def normalized_levenshtein_distance(s1, s2):
    # lev_distance = levenshtein_distance(s1, s2)
    lev_distance = lev.distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return lev_distance / max_len


def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def count_overlap(input1, input2):
    # Initialize counters
    count1 = {}
    count2 = {}
    if isinstance(input1, str):
        input1 = json.loads(input1)
    if isinstance(input2, str):
        input2 = json.loads(input2)
    
    # Flatten dictionaries if necessary
    if isinstance(input1, dict):
        input1 = flatten_dict(input1)
    if isinstance(input2, dict):
        input2 = flatten_dict(input2)
    
    # Check if inputs are lists or dictionaries and count occurrences
    if isinstance(input1, list) and isinstance(input2, list):
        for item in input1:
            count1[item] = count1.get(item, 0) + 1
        for item in input2:
            count2[item] = count2.get(item, 0) + 1
    elif isinstance(input1, dict) and isinstance(input2, dict):
        for key in input1:
            count1[key] = count1.get(key, 0) + 1
        for key in input2:
            count2[key] = count2.get(key, 0) + 1
    else:
        raise ValueError("Both inputs must be of the same type: either list or dictionary")
    
    # Find overlap between the two sets of counted items
    overlap = 0
    for item in count1:
        overlap += min(count1[item], count2.get(item, 0))
    
    # Calculate normalized overlap
    min_length = min(len(input1), len(input2))
    if min_length == 0:
        return 0  # Avoid division by zero
    normalized_overlap = overlap / min_length
    
    return normalized_overlap


def calculate_cossim(code1, code2, tokenizer, model, device):
    device = "cpu"
    inputs1 = tokenizer.encode(code1, return_tensors="pt").to(device)
    embedding1 = model(inputs1)[0]
    embedding1 = embedding1.detach().cpu().numpy().reshape(1, -1)
    inputs1 = None  # Clear inputs1 from memory

    inputs2 = tokenizer.encode(code2, return_tensors="pt").to(device)
    embedding2 = model(inputs2)[0]
    embedding2 = embedding2.detach().cpu().numpy().reshape(1, -1)
    inputs2 = None  # Clear inputs2 from memory

    similarity = cosine_similarity(embedding1, embedding2)[0][0]

    # Clean up GPU memory
    del embedding1, embedding2
    torch.cuda.empty_cache()

    return similarity


if __name__=="__main__":
    code_folder = ''
    cossim_folder = ''
    type = ''
    model_name = ''
    output_folder = f''


    for code_csv_file in os.listdir(code_folder):
        if model_name not in code_csv_file:
            continue
        print(f"--> Processing {code_csv_file}...")
        code_df = pd.read_csv(code_folder+code_csv_file)
        output_df = pd.DataFrame(columns=code_df.columns.tolist()+['LOC', 'lev_distance', 'element_overlap', 'cossim_with_original_code'])
        print(code_df.columns)
        
        for _, row in code_df.iterrows():
            file_name = row['File Path']
            file_type = file_name.split('.')[-1]
            original_code = clean_code_string(row['Code'])
            generated_code = clean_code_string(row[f'code_{type}'])
            cossim = calculate_cossim(row['Code'], row['code_'+type], tokenizer, model, 'cpu')

            try:
                original_structure = extract_structure(original_code, file_type)
                generated_structure = extract_structure(generated_code, file_type)

                loc_difference = normalized_loc_difference(original_code, generated_code)
                lev_distance = normalized_levenshtein_distance(original_structure, generated_structure)
                element_overlap = count_overlap(original_structure, generated_structure)

                output_df.loc[len(output_df)] = row.tolist() + [loc_difference, lev_distance, element_overlap, cossim]
            except Exception as e:
                print(generated_code)

        output_df.to_csv(f"")

