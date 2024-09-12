import os
import pickle
import openai
import pandas as pd
from openai import OpenAI
from tqdm import tqdm


os.environ['OPENAI_API_KEY'] = ''
openai.api_key = os.getenv('OPENAI_API_KEY')


model = 'gpt4'
model_type = 'openai'
model_dict = {'openai': 'gpt-4-turbo', 'lm-studio': "TechxGenus/Meta-Llama-3-70B-Instruct-AWQ"}

PROMPT_FROM_SUMMARY = """
I want you to act as a software developer. You will be provided with a summarized description of a source code file. Write the source code ensuring that the it covers all the necessary aspects, including the actions it should take, dependencies, UI components, and any other factors influencing the application's execution.
"""

code_from_code_list, code_from_comment_list, code_from_both_list = [], [], []

if model_type == 'openai':
    client = OpenAI()
elif model_type == 'lm-studio':
    client = OpenAI(
        base_url="",
        api_key="lm-studio"
    )


def is_ui_related(file_path):
    # Define UI-related extensions
    ui_extensions = {
        '.html', '.htm', '.css', '.scss', '.sass', '.less', '.js', '.ts', 
        '.jsx', '.tsx', '.vue', '.svelte', '.elm', '.svg', '.png', '.jpg', 
        '.jpeg', '.gif', '.json', '.py'
    }

    # Define patterns and keywords for UI-related content
html_patterns = [
        "<html", "<head", "<title", "<body", "<meta", "<link", "<style", "<script", "<header", "<nav",
        "<section", "<article", "<aside", "<footer", "<h1", "<h2", "<h3", "<h4", "<h5", "<h6", "<p",
        "<blockquote", "<hr", "<pre", "<br", "<code", "<em", "<strong", "<a", "<span", "<b", "<i",
        "<u", "<mark", "<small", "<sup", "<sub", "<del", "<ins", "<ul", "<ol", "<li", "<dl", "<dt",
        "<dd", "<table", "<thead", "<tbody", "<tfoot", "<tr", "<th", "<td", "<caption", "<form", "<input",
        "<textarea", "<button", "<select", "<option", "<label", "<fieldset", "<legend", "<datalist", "<output",
        "<img", "<figure", "<figcaption", "<video", "<audio", "<source", "<track", "<iframe", "<object",
        "<embed", "<canvas", "<svg", "<details", "<summary", "<dialog", "<template", "<slot", "<shadow",
        "<main", "<article", "<section", "<aside", "<time", "<progress", "<meter", "<font", "<center"
    ]

css_patterns = [
        "display:", "position:", "top:", "right:", "bottom:", "left:", "float:", "clear:", "z-index:", 
        "overflow:", "overflow-x:", "overflow-y:", "visibility:", "width:", "min-width:", "max-width:", 
        "height:", "min-height:", "max-height:", "margin:", "margin-top:", "margin-right:", 
        "margin-bottom:", "margin-left:", "padding:", "padding-top:", "padding-right:", 
        "padding-bottom:", "padding-left:", "border:", "border-width:", "border-style:", 
        "border-color:", "border-radius:", "box-shadow:", "box-sizing:", "background:", 
        "background-color:", "background-image:", "background-position:", "background-size:", 
        "background-repeat:", "background-attachment:", "background-clip:", "outline:", 
        "outline-color:", "outline-style:", "outline-width:", "font:", "font-family:", 
        "font-size:", "font-weight:", "font-style:", "font-variant:", "font-stretch:", "color:", 
        "text-align:", "text-decoration:", "text-decoration-color:", "text-decoration-style:", 
        "line-height:", "letter-spacing:", "word-spacing:", "text-transform:", "white-space:", 
        "text-shadow:", "text-overflow:", "flex:", "flex-grow:", "flex-shrink:", "flex-basis:", 
        "flex-direction:", "flex-wrap:", "justify-content:", "align-items:", "align-self:", 
        "align-content:", "order:", "grid:", "grid-template-columns:", "grid-template-rows:", 
        "grid-template-areas:", "grid-column:", "grid-row:", "grid-area:", "grid-gap:", 
        "grid-column-gap:", "grid-row-gap:", "vertical-align:", "align-content:", "justify-items:", 
        "justify-self:", "animation:", "animation-name:", "animation-duration:", 
        "animation-timing-function:", "animation-delay:", "animation-iteration-count:", 
        "animation-direction:", "transition:", "transition-property:", "transition-duration:", 
        "transition-timing-function:", "transition-delay:", "transform:", "transform-origin:", 
        "perspective:", "perspective-origin:", "opacity:", "cursor:", "filter:", "border-collapse:", 
        "border-spacing:", "caption-side:", "empty-cells:", "table-layout:", "list-style:", 
        "list-style-type:", "list-style-position:", "list-style-image:", ":hover:", ":focus:", 
        ":active:", ":visited:", ":first-child:", ":nth-child:", ":last-child:", "::before:", "::after:"
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


# Load file path dictionary from pickle file
file_path_dict = pickle.load(open('', 'rb'))

for key, values in file_path_dict.items():
    print(f"> Executing {key}")
    
    # Search for the summary file
    summary_files = [x for x in os.listdir('') if x.startswith(key + '_chatgpt')]
    
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
        
        response_from_code = client.chat.completions.create(
                    model=model_dict[model_type],
                    messages=[
                        {"role": "system", "content": PROMPT_FROM_SUMMARY},
                        {"role": "user", "content": f"Summary: {summary_from_code}"}
                    ],
                    temperature=1
                )
        code_from_code = response_from_code.choices[0].message.content
        new_row = filtered_df.iloc[0].tolist() + [code_from_code]
        code_output_df.loc[len(code_output_df)] = new_row
        
        print(f"> Generated and reviewed code for {file_path}")


    code_output_df.to_csv(f'')