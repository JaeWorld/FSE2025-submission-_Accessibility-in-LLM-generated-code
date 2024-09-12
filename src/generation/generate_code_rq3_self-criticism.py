import json
import os
import openai
# from langchain import OpenAI, LLMChain, PromptTemplate
# from langchain.llms import OpenAI
from openai import OpenAI
import pickle
import pandas as pd



# Set up your OpenAI API key
os.environ['OPENAI_API_KEY'] = ''  # Replace with your actual API key


model_dict = {'openai': 'gpt-4-turbo', 'lm-studio': "TechxGenus/Meta-Llama-3-70B-Instruct-AWQ"}
model_type = 'openai'
model = 'gpt4'


PROMPT_FROM_SUMMARY = f"""
I want you to act as a software developer. You will be provided with a summarized description of a source code file. Write the source code ensuring that it covers all the necessary aspects, including the actions it should take, dependencies, UI components, and any other factors influencing the application's execution. In addition, act as a WCAG accessibility expert and make sure the code you generate complies with the WCAG accessibility rules. The code should be designed to avoid any violations of these rules, ensuring that it meets all accessibility requirements. 
"""

PROMPT_FOR_REVIEW = f"""
I want you to act as a code reviewer and a WCAG accessibility expert. Review the code to check if it meets WCAG accessibility guidelines. If it is fully compliant, return the code unchanged. If there are any accessibility issues, identify and fix them, then return the modified code that fully complies with the guidelines.
"""


if model_type == 'openai':
    client = OpenAI()
elif model_type == 'lm-studio':
    client = OpenAI(
        base_url="",
        api_key="lm-studio"
    )


# Load file path dictionary from pickle file
file_path_dict = pickle.load(open('', 'rb'))

for key, values in file_path_dict.items():
    print(f"> Executing {key}")
    
    # Search for the summary file
    summary_files = [x for x in os.listdir('/') if x.startswith(key + '_chatgpt')]
    
    if not summary_files:
        print(f"No summary file found for key: {key}")
        continue
    
    summary_file_path = os.path.join('', summary_files[0])
    summary_df = pd.read_csv(summary_file_path)
    
    # Initialize DataFrame with additional columns
    code_output_df = pd.DataFrame(columns=summary_df.columns.tolist() + ['code_from_code'])

    for url in values:
        filtered_df = summary_df[summary_df['File Path'].str.contains(url, na=False)]
        
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
                        {"role": "system", "content": PROMPT_FROM_SUMMARY},
                        {"role": "user", "content": f"Summary: {summary_from_code}"}
                    ],
                    temperature=1
                )
            
            code_from_code = response_from_code.choices[0].message.content

            response_from_review = client.chat.completions.create(
                    model=model_dict[model_type],
                    messages=[
                        {"role": "system", "content": PROMPT_FOR_REVIEW},
                        {"role": "user", "content": f"Code: {code_from_code}"}
                    ],
                    temperature=1
                )
            
            reviewed_code = response_from_review.choices[0].message.content


        except Exception as e:
            print(f"Error generating code for {file_path}: {e}")
            code_from_code = "Error generating code"
        
        # Add the new row to the DataFrame
        new_row = filtered_df.iloc[0].tolist() + [reviewed_code]
        code_output_df.loc[len(code_output_df)] = new_row
        
        print(f"> Generated and reviewed code for {file_path}")

    output_file_path = os.path.join(f'', f'')
    code_output_df.to_csv(output_file_path, index=False)
