import os
import openai
import pandas as pd
from openai import OpenAI
from tqdm import tqdm


os.environ['OPENAI_API_KEY'] = ''
openai.api_key = os.getenv('OPENAI_API_KEY')

model_type = 'openai'
model_dict = {'openai': 'gpt-4-turbo', 'lm-studio': "TechxGenus/Meta-Llama-3-70B-Instruct-AWQ"}

if model_type == 'openai':
    client = OpenAI()
elif model_type == 'lm-studio':
    client = OpenAI(
        base_url="",
        api_key="lm-studio"
    )

PROMPT_FROM_CODE = """
I want you to act as a code summarizer. You will be provided with a source code file content. Write a detailed description for this code with the intention of regenerating it using Large Language Model (LLM). Ensure the description covers all necessary aspects for reproducing the code accurately, including the actions it should take, dependencies, UI components, and any other factors influencing the application's execution. Do not include the source code itself to your response.
"""

# Define the front-end related file extensions
FRONT_END_EXTENSIONS = [
        # HTML
        '.html', '.htm',

        # CSS
        '.css', '.scss', '.sass', '.less',

        # JavaScript
        '.js', '.jsx', '.ts', '.tsx',

        # Template and Component Extensions
        # React
        '.jsx', '.tsx',
        # Vue
        '.vue',
        # Angular
        '.ts', '.html', '.css', '.scss',
        # Svelte
        '.svelte',
        # Next.js
        '.js', '.jsx', '.ts', '.tsx',
        # Nuxt.js
        '.js', '.vue', '.ts',
         # Django, Flask
        '.py',

        # Template and Markup Extensions
        '.njk', '.nunjucks', '.ejs', '.pug', '.jade', '.hbs', '.twig',

        # Framework-Specific Extensions
        # Ruby on Rails
        '.erb', '.haml',
        # ASP.NET
        '.cshtml',
        # PHP
        '.php',
        # Java
        '.jsp',
        # ColdFusion
        '.cfm',
        # Scala
        '.scaml'
    ]

def is_ui_related(file_path):
    # Define UI-related extensions
    ui_extensions = {
        '.html', '.htm', '.css', '.scss', '.sass', '.less', '.js', '.ts', 
        '.jsx', '.tsx', '.vue', '.svelte', '.elm', '.svg', '.png', '.jpg', 
        '.jpeg', '.gif', '.json', '.py'
    }

    # Define patterns and keywords for UI-related content
    html_patterns = [
        '<html', '<head', '<body', '<header', '<footer', '<nav', '<main', 
        '<section', '<article', '<aside', '<div', '<span', '<button', 
        '<input', '<form', '<a', '<h1', '<p', '<img', '<video', '<audio', 
        'class=', 'id=', 'style=', 'data-'
    ]
    css_patterns = [
        'color:', 'background:', 'border:', 'font:', 'padding:', 'margin:', 
        'display:', 'position:', 'flex:', 'grid:', '@media', '@import'
    ]
    js_patterns = [
        'document.querySelector', 'document.getElementById', 'addEventListener', 
        'innerHTML', 'style.', 'classList.', 'import React', 'ReactDOM.render', 
        'import Vue', 'new Vue(', 'import { Component } from', '$(', 
        'onclick', 'onchange', 'onsubmit', 'jQuery', '$(document).ready'
    ]
    json_patterns = [
        '"theme":', '"layout":', '"components":', '"data":'
    ]
    vue_patterns = [
        '<template>', '<script>', '<style>', 'export default', 'data', 'methods', 
        'computed', 'components'
    ]
    svelte_patterns = [
        '<script>', '<style>', 'export let', 'export default', 'on:'
    ]
    elm_patterns = [
        'type Msg', 'update', 'view', 'Html', 'import Html'
    ]
    scss_patterns = [
        '$', '@mixin', '@include', '@import'
    ]
    python_patterns = [
        'from flask import', 'import flask', 'app = Flask(', 'from django.http import', 
        'from django.shortcuts import', 'render_template(', 'HttpResponse(', 
        'TemplateView(', 'HttpRequest(', 'Django', 'Flask'
    ]

    def contains_html_tags(content):
        return any(pattern in content for pattern in html_patterns)

    def contains_python_patterns(content):
        return any(pattern in content for pattern in python_patterns)

    # Check file extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in ui_extensions:
        return False

    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

    # Check content against patterns
    if ext.lower() in {'.html', '.htm'}:
        if contains_html_tags(content):
            return True
    elif ext.lower() in {'.css', '.scss', '.sass', '.less'}:
        if any(pattern in content for pattern in css_patterns) or \
           (ext.lower() in {'.scss', '.sass'} and any(pattern in content for pattern in scss_patterns)):
            return True
    elif ext.lower() in {'.js', '.ts', '.jsx', '.tsx', '.vue', '.svelte', '.elm'}:
        if any(pattern in content for pattern in js_patterns) or \
           (ext.lower() == '.vue' and any(pattern in content for pattern in vue_patterns)) or \
           (ext.lower() == '.svelte' and any(pattern in content for pattern in svelte_patterns)) or \
           (ext.lower() == '.elm' and any(pattern in content for pattern in elm_patterns)):
            # Further refine JS files by checking for HTML tags
            if ext.lower() in {'.js', '.ts', '.jsx', '.tsx'}:
                if contains_html_tags(content):
                    return True
            else:
                return True
    elif ext.lower() == '.json':
        if any(pattern in content for pattern in json_patterns):
            return True
    elif ext.lower() == '.py':
        # Ensure Python files contain HTML tags
        if contains_html_tags(content) and contains_python_patterns(content):
            return True

    return False


def summarize_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        code = file.read()

    response_from_code = client.chat.completions.create(
                        model=model_dict[model_type],
                        messages=[
                            {"role": "user", "content": PROMPT_FROM_CODE},
                            {"role": "user", "content": f"Code: {code}"}
                        ],
                        temperature=1
                    )
    summary = response_from_code.choices[0].message.content
    return summary, code

def process_directory(directory):
    summaries = []

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1].lower()

            if file_extension in FRONT_END_EXTENSIONS:
                # Filter out files that are not related to UI
                if not is_ui_related(file_path):
                    continue
                try:
                    summary, original_code = summarize_file_content(file_path)
                    if not summary:
                        continue
                    summaries.append({'File Path': file_path, 'Code': original_code, 'Summary': summary})
                    print(f"> Generated summary of {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")

    # Save summaries to CSV
    if summaries:
        df = pd.DataFrame(summaries)
        csv_file_name = os.path.join('', f'')
        df.to_csv(csv_file_name, index=False)

if __name__ == "__main__":
    # List of repository directories
    repo_directories = os.listdir('')

    for repo_directory in repo_directories:
        print(f"Processing {repo_directory}...")
        process_directory(''+repo_directory)
