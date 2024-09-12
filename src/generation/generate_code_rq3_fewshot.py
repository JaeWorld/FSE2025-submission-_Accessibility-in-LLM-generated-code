import os
import json
import pickle
import openai
import pandas as pd
from openai import OpenAI
from tqdm import tqdm


os.environ['OPENAI_API_KEY'] = ''
openai.api_key = os.getenv('OPENAI_API_KEY')


model_dict = {'openai': 'gpt-4-turbo', 'lm-studio': "TechxGenus/Meta-Llama-3-70B-Instruct-AWQ"}
model_type = 'openai'
model_name = 'gpt4'

PROMPT_FROM_SUMMARY = """
I want you to act as a software developer. You will be provided with a summarized description of a source code file. Write the source code ensuring that it covers all the necessary aspects, including the actions it should take, dependencies, UI components, and any other factors influencing the application's execution. 
In addition, act as a WCAG accessibility expert and make sure the code you generate complies with the WCAG accessibility rules. The code should be designed to avoid any violations of these rules, ensuring that it meets all accessibility requirements. You will also receive detailed information about accessibility rules, along with correct and incorrect examples for each rule. Use this information to generate compliant source code.
"""

code_from_code_list, code_from_comment_list, code_from_both_list = [], [], []

if model_type == 'openai':
    client = OpenAI()
elif model_type == 'lm-studio':
    client = OpenAI(
        base_url="",
        api_key="lm-studio"
    )


violation_info_dict = json.load(open(''))

def prompt_construction():
    prompt = PROMPT_FROM_SUMMARY
    for violations in violation_info_dict['accessibility_violations']:
        formatted_violations = f"""
Rule: {violations['violation_type']}
Description: {violations['description']}
Incorrect Example: {violations['incorrect_example']}
Correct Example: {violations['example']}
        """

        prompt += formatted_violations

    return prompt.strip()



file_path_dict = pickle.load(open('', 'rb'))
prompt = prompt_construction()


for key, values in file_path_dict.items():
    print(f"> Executing {key}")
    # Search for the summary file
    summary_files = [x for x in os.listdir('') if x.startswith(key+'')]
    
    if not summary_files:
        print(f"No summary file found for key: {key}")
        continue
    
    summary_file_path = summary_files[0]
    summary_df = pd.read_csv(os.path.join('', summary_file_path))
    
    # Initialize DataFrame with additional column
    code_output_df = pd.DataFrame(columns=summary_df.columns.tolist() + ['code_from_code'])

    for url in values:
        filtered_df = summary_df[summary_df['File Path'].str.contains(url)]
        
        if filtered_df.empty:
            print(f"No data found for URL: {url}")
            continue
        
        summary_from_code = filtered_df['Summary'].iloc[0]
        file_path = filtered_df['File Path'].iloc[0]

        # Generate code from API response
        try:
            response_from_code = client.chat.completions.create(
                model=model_dict[model_type],
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Summary: {summary_from_code}"}
                ],
                temperature=1
            )

            code_from_code = response_from_code.choices[0].message.content
        except Exception as e:
            print(f"Error generating code for {file_path}: {e}")
            code_from_code = "Error generating code"
        
        # Add the new row to the DataFrame
        new_row = filtered_df.iloc[0].tolist() + [code_from_code]
        code_output_df.loc[len(code_output_df)] = new_row
        
        print(f"> Generated code for {file_path}")

    code_output_df.to_csv(os.path.join(f'', f''), index=False)

