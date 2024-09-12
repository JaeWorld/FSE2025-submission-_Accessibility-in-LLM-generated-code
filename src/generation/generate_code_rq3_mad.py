from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from openai import OpenAI
# from langchain.llms import OpenAI
import os
import pickle
import pandas as pd
import json

# Set API key
os.environ['OPENAI_API_KEY'] = ''  # Replace with your actual API key

model_dict = {'openai': 'gpt-4-turbo', 'lm-studio': "TechxGenus/Meta-Llama-3-70B-Instruct-AWQ"}
model_type = 'openai'
model_name = 'gpt4'

host_model_id = model_dict[model_type]



def debate_prediction(code_summary, max_iteration):
    if model_type == 'openai':
        llm_1 = ChatOpenAI()
    elif model_type == 'lm-studio':
        llm_1 = ChatOpenAI(
            base_url="",
            api_key="lm-studio",
            model_name=host_model_id
        )

    if model_type == 'openai':
        llm_2 = ChatOpenAI()
    elif model_type == 'lm-studio':
        llm_2 = ChatOpenAI(
            base_url="",
            api_key="lm-studio",
            model_name=host_model_id
        )

    # Define prompt templates
    template_generator = """I want you to act as a software developer. You will be provided with a summarized description of a source code file. Write the source code ensuring that it covers all the necessary aspects, including the actions it should take, dependencies, UI components, and any other factors influencing the application's execution. In addition, act as a WCAG accessibility expert and make sure the code you generate complies with the WCAG accessibility rules. The code should be designed to avoid any violations of these rules, ensuring that it meets all accessibility requirements. 

    Current conversation:
    {history}
    Human: {input}
    AI agent:"""
    PROMPT_generator = PromptTemplate(input_variables=["history", "input"], template=template_generator)

    template_reviewer = """I want you to act as a code reviewer and a WCAG accessibility expert. You will be provided with a source code. Review the code to make sure the code complies with the WCAG accessibility rules. The code should be designed to avoid any violations of these rules, ensuring that it meets all accessibility requirements. Provide suggestions for improvement in making the code more accessible. 
 
    Current conversation:
    {history}
    Human: {input}
    AI agent:"""
    PROMPT_reviewer = PromptTemplate(input_variables=["history", "input"], template=template_reviewer)

    # Create conversation chains
    conversation_generator = ConversationChain(
        llm=llm_1,
        prompt=PROMPT_generator,
        memory=ConversationBufferMemory(ai_prefix="AI agent", input_variables=["history", "input"]),
    )

    conversation_reviewer = ConversationChain(
        llm=llm_2,
        prompt=PROMPT_reviewer,
        memory=ConversationBufferMemory(ai_prefix="AI agent", input_variables=["history", "input"]),
    )

    # Initial predictions
    first_q_for_generator = "'\n" + code_summary
    generated_code = conversation_generator.predict(input=first_q_for_generator)

    first_q_for_reviewer = "'\n" + generated_code
    review = conversation_reviewer.predict(input=first_q_for_reviewer)

    num_debates = 0
    iter_num = 0
    while iter_num <= max_iteration:
        c_1_str = f"I want you to act as a software developer. The other agent returned suggestions for improving accessibility of the code as {review}. Based on the suggestions, act as a WCAG accessibility expert and improve the code so that it meets the accessibility guidelines. Return only the entire improved source code in the output."
        generated_code = conversation_generator.predict(input=c_1_str)

        c_2_str = f"I want you to act as a code reviewer and a WCAG accessibility expert. The other agent returned the code as {code}. Based on the code, determine if it meets with the WCAG accessibility guidelines. If not, provide suggestions that can help code meet the WCAG accessibility guidelines."
        review = conversation_reviewer.predict(input=c_2_str)

        num_debates += 1
        iter_num += 1

    return generated_code


# Load file path dictionary
file_path_dict = pickle.load(open('', 'rb'))

for key, values in file_path_dict.items():
    print(f"> Executing {key}")

    summary_files = [x for x in os.listdir('') if x.startswith(key + '_chatgpt')]
    if not summary_files:
        print(f"No summary file found for key: {key}")
        continue

    summary_file_path = os.path.join('', summary_files[0])
    summary_df = pd.read_csv(summary_file_path)
    code_output_df = pd.DataFrame(columns=summary_df.columns.tolist() + ['code_from_code'])

    for url in values:
        filtered_df = summary_df[summary_df['File Path'].str.contains(url, na=False)]
        if filtered_df.empty:
            print(f"No data found for URL: {url}")
            continue

        summary_from_code = filtered_df['Summary'].iloc[0]
        file_path = filtered_df['File Path'].iloc[0]
                
        code = debate_prediction(summary_from_code, 4)
        
        new_row = filtered_df.iloc[0].tolist() + [code]
        code_output_df.loc[len(code_output_df)] = new_row
        
        print(f"> Generated and reviewed code for {file_path}")

    output_file_path = os.path.join(f'', f'')
    code_output_df.to_csv(output_file_path, index=False)
