import streamlit as st 
from openai import OpenAI
from urllib.request import urlopen
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import ssl
import urllib.request
import time
import os
# from googlesearch import search
from dotenv import load_dotenv
import concurrent.futures
from datetime import datetime
import json
import pandas as pd
import re

load_dotenv()
client = OpenAI()

ssl._create_default_https_context = ssl._create_unverified_context

def generate_response(prompt):
    response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": "You are a helpful assistant, expert in Analysing Companies."},
        {"role": "user", "content": str(prompt)},
    ],
    temperature=0
    )
    selection = response.choices[0].message.content
    return selection

def generate_response_feedback(initial_question, system_answer, feedback):
    response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": "You are a helpful assistant, expert in Analysing Companies."},
        {"role": "user", "content": str(initial_question)},
        {"role": "system", "content": str(system_answer)},
        {"role": "user", "content": str(feedback)}
    ],
    temperature=0
    )
    selection = response.choices[0].message.content
    return selection

def generate_response_gpt3(prompt):
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant, expert in Analysing Companies."},
        {"role": "user", "content": str(prompt)},
    ],
    max_tokens=300,
    temperature=0
    )
    selection = response.choices[0].message.content
    return selection

def retrieve_html(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = Request(url, headers=headers)
    html = urlopen(req).read()
    soup = BeautifulSoup(html, features="html.parser")

    for script in soup(["script", "style"]):
        script.extract() 

    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

def selenium_search(query):
    for url in search(query + ' website', lang = 'en'):
        return url
    
clients_focus = ["B2C", "B2B", "B2B/B2C"]
prompt_client_focus = """

You are given the description of a company retrieved from a company's website.

You will need to categorize the company within a Client Focus according to the taxonomy below.

There can only be ONE client focus. The answer needs to be concise and only can follow the taxonomy.

DO NOT come up with any taxonomy. STICK to the taxonomy below. 

Give your results in the format JSON  - 

'client_focus': [client focus] 


Here the taxonomy for the client focus:
B2C
B2B
B2B/B2C
"""

startup_industries = ["Deep Tech", "Edtech", "Fintech", "Foodtech", "Healthtech", "Insurtech", "Lawtech", "Salestech", "Mobility", "Energy", "Big data", "Cybersecurity", "Media", "Consumer electronics", "Esports", "Gaming", "Agritech", "Regtech", "Impact & diversity", "HRtech", "Martech", "Cleantech", "Traveltech"]
midmarket_industries = ["Financial advisory", "Legal services", "Digital services", "Content production", "Temporary work", "Recruitment agency", "Marketing agency", "Cloud & infrastructure", "Web 3", "Data protection", "Energy provider", "Energy storage", "Energy effiency", "Clean energy", "Pharmaceutical", "Medical equipement", "Apparel", "Beauty", "Consumer goods", "Logistics & delivery", "Luxury", "Food", "Vehicle production", "Plane crafting", "Building & construction", "Sport media & platform", "Sport club", "Sport equipment", "Payment", "In-store retail", "Office property", "Real estate service", "Hotel & accomodation", "Health & Wellness", "Technology & Innovation", "Telecommunications", "Manufacturing", "Education & Training", "Human Resources"]
corporate_industries = ["Finance & Legal", "Technology", "Media & Telecomunication", "Consulting", "Insurance", "Recruitment", "Construction", "Energy & Chemical", "Automotive", "Retail", "Real estate", "Healthcare", "Travel", "Fashion", "FMCG", "Banking", "Education", "Logistics & Transportation", "Pharmaceuticals", "Environmental", "Food & Beverage"]
business_models = ["SaaS", "Marketplace", "Ecommerce", "Service", "Manufacturing"]


prompt_industry_business =  f"""

You are given the description of a company retrieved from a company's website.

You will need to categorize the company within their Industry and Business Model Category according to the taxonomy below.

There can only be ONE industry and ONE business model. The answer needs to be concise and only can follow the taxonomy.

DO NOT come up with any taxonomy. STICK to the taxonomy below. 

Give your results in the format format JSON - 

'industry': [industry] 
'business_model': [business model]

Here the taxonomy for each of the Industries and Business Models - 

Business Models:
SaaS
Marketplace
Ecommerce
Service
Manufacturing 

Industries:

"""

end_buyers = ["Sales", "Marketing", "HR", "Finance", "Tech & Data", "Legal", "Procurement", "Client support", "CSE", "ESG", "Communication", "Consumer"]
prompt_end_buyer =  f"""

You are given the description of a company retrieved from a company's website.

You will need to categorize the company within an End Buyer category according to the taxonomy below.

There can only be ONE end buyer The answer needs to be concise and only can follow the taxonomy.

DO NOT come up with any taxonomy. STICK to the taxonomy below. 

Give your results in the format format JSON - 

'end_buyer': [end buyer] 

Here the taxonomy for each of the Industries and Business Models - 

End Buyer:
Sales
Marketing
HR
Finance
Tech & Data
Legal
Procurement
Client support
CSE
ESG
Communication
Consumer
"""

organize_prompt = 'From the following scrapped text of a website explain what the business does. The text will be poorly written so take that in mind. Write everything in third person naming the company. Output only a description using key words of the industry. Here the scrapped code/text: '
header_url= "Here the description of the company deducted from their website: "

def truncate_string(input_string):
    if len(input_string) <= 3000:
        return input_string
    else:
        return input_string[:3000]

def format_url(url):
    if url.startswith("http://www."):
        url = url.replace("http://www.", "https://www.")
    elif url.startswith("http://"):
        url = url.replace("http://", "https://www.")
    elif url.startswith("www."):
        url = "https://" + url
    elif not url.startswith("https://"):
        url = "https://www." + url
    return url

def parse_response(input_string):
    lines = input_string.split('\n')
    pairs = [line.split(':') for line in lines]
    pairs = [[key.strip(), value.strip()] for key, value in pairs]
    data = dict(pairs)
    industry = data.get('Industry')
    business_model = data.get('Business Model')

    return industry, business_model

def business_status(company_employees, company_founded_date):
    company_age = 2024 - company_founded_date

    if company_employees == 0 and company_founded_date == 0:
        return 'Uncategorized'
    elif (company_employees < 200 and company_age <= 5) or company_employees < 200:
        return 'Startup'
    elif (201 <= company_employees <= 1000 and 3 <= company_age < 15) or 501 <= company_employees <= 1000:
        return 'MidMarket'
    elif (company_employees >= 1001 or company_age >= 15) or company_employees >= 1001:
        return 'Corporate'
    else:
        return 'Uncategorized'
    
from concurrent.futures import ThreadPoolExecutor
    
def industryGPT(name, url, company_id=0, company_employees=0, company_founded_date=0):
    print('Enriching: ', name)
    print('With URL: ', url)
    print('Company ID: ', company_id)



    full_response = {

            "company_id": str(company_id),
            "metadata": {
                "timestamp": str(datetime.now()),
                "source": "industryGPT"
            },
            "company_profile": {
                "website": str(url),
                "n_employees": str(company_employees),
                "founded_date": str(company_founded_date),
                "business_status": None,
                "industry": None,
                "business_model": None,
                "end_buyer": None,
                "client_focus": None,
                "description": None,
            }

        }
    


    # Categorise business status
    try:
        b_status = business_status(company_employees, company_founded_date)
        full_response["company_profile"]["business_status"] = b_status
        print('Company categorised as: ', b_status)
    except Exception as e:
        print(e)
        print("Error categorising business_status, wrong format of data or no data.")
        return Exception
    
    # Categorise industry & business model
    url_text = retrieve_html(format_url(url))
    print('\n-> Retrieved text from website...')
    
    if len(url_text) > 100:
        print('-> Crafting company description...')
        description_openai = generate_response_gpt3(organize_prompt + truncate_string(url_text))
        print('\nDescription of the company: ', description_openai)

    else:
        print('Scrapped website has less than 100 characters...')
        print('Trying to search on google a new page...')
        new_url = selenium_search(format_url(url))
        url_text = retrieve_html(new_url)
        description_openai = generate_response_gpt3(organize_prompt + truncate_string(url_text))
        print('\nDescription of the company: ', description_openai)

    # Save description
    full_response["company_profile"]["description"] = description_openai




    # Define specific industry
    if b_status == 'Startup':
        industry_categories = startup_industries
        selected_industries = ', '.join(industry_categories)

    if b_status == 'MidMarket':
        industry_categories = midmarket_industries
        selected_industries = ', '.join(industry_categories)

    if b_status == 'Corporate':
        industry_categories = corporate_industries
        selected_industries = ', '.join(industry_categories)
    
    if b_status == 'Uncategorized':
        industry_categories = startup_industries
        selected_industries = ', '.join(industry_categories)
    

    executor = ThreadPoolExecutor(12)


    # Categorise industry & business Model
    response_industry = executor.submit(generate_response, (prompt_industry_business +
                                selected_industries +
                                header_url +
                                description_openai))
    
    response_clientfocus = executor.submit(generate_response, (prompt_client_focus +
                                header_url +
                                description_openai))
    
    response_endbuyer = executor.submit(generate_response, (prompt_end_buyer +
                                header_url +
                                description_openai))



    result_industry = response_industry.result()
    result_clientfocus = response_clientfocus.result()
    result_endbuyer = response_endbuyer.result()

    response_dict_industry = json.loads(result_industry)



    # Is the categorization correct? 
    industry = response_dict_industry["industry"]
    business_model = response_dict_industry["business_model"]

    if industry not in industry_categories or business_model not in business_models:
        print('Industry or Business Model not in category.')
        print('Faulty Industry: ', industry)
        print('Faulty Business Model: ', business_model)

        initial_question = (prompt_industry_business + selected_industries + header_url + description_openai)
        system_answer = "Industry: " + industry + " Business Model: " + business_model
        
        feedback = "The Industry and Business Model is not correct... retry please and stay within taxonomy."
        retry_industry = executor.submit(generate_response_feedback, initial_question, system_answer, feedback)
        retry_industry_dict = retry_industry.result()
        retry_industry_dict_json = json.loads(retry_industry_dict)
        industry = retry_industry_dict_json["industry"]
        business_model = retry_industry_dict_json["business_model"]
    
    
    full_response["company_profile"]["industry"] = industry
    full_response["company_profile"]["business_model"] = business_model



    # Is the categorization correct? 
    response_dict_clientfocus = json.loads(result_clientfocus)
    client_focus = response_dict_clientfocus["client_focus"]

    if client_focus not in clients_focus:
        print('Client Focus not in category.')
        print('Faulty Client Focus: ', client_focus)
        return None
    
    full_response["company_profile"]["client_focus"] = client_focus   
    


    # Is the categorization correct?
    response_dict_endbuyer = json.loads(result_endbuyer)
    end_buyer = response_dict_endbuyer["end_buyer"]

    if end_buyer not in end_buyers:
        print('End Buyer not in category.')
        print('Faulty End buyer: ', end_buyer)
        return None

    full_response["company_profile"]["end_buyer"] = end_buyer
    

    full_response_json = json.dumps(full_response)
    json_string_pretty = json.dumps(full_response, indent=2)
    print('')
    print(json_string_pretty)
    print('--------------------------------')

    return full_response_json

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


st.title("Enrich with industryGPT")

st.caption("""With industryGPT you are able to input the website of a company and enrich its Industry, Business Model, if its a Startup, MidMarket or Corporate company, its EndBuyers and many more points...""")

col_1, col_2, col_3, col_4 = st.columns([1, 1, 1, 1])
name = col_1.text_input('Account name', placeholder="Apolo")
company_id = col_2.text_input('Company ID', placeholder="123456789")
employees = col_3.text_input('Employees', placeholder="75")
founded_date = col_4.text_input('Founded Date', placeholder="2020")

title = st.text_input('Account URL', placeholder="www.example-company.com")
enrich = st.button('Enrich my data!')


if enrich:
    with st.status(f"Scrapping {name} website and crafting enrichment..."):
        try:
            response = industryGPT(name, title, int(company_id), int(employees), int(founded_date))
            print(response)
            st.json(response)
        except Exception as e:
            print(e)
            st.error(f'Cant retrieve answer for {name} ', icon="🚨")




# industryGPT('Apollo', 'https://apollo.io', 123456789, 198, 2019)