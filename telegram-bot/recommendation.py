from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

url = "https://api.awanllm.com/v1/chat/completions"

model_name = os.getenv('MODEL_NAME')
api_key = os.getenv('AWANLLM_API_KEY')

def construct_prompt(patient_data, doctors_data):
    return """
        This is patient data #{patient_data}; This is doctors data #{doctors_data}; Please match most appropriate 3 doctors to the patient data.
    """

def get_doctors_data:
    df = pd.read_csv('data/doctors.csv')
    result = [[row] for row in df.to_dict(orient='records')]

    retturn result

def make_request
    payload = json.dumps({
    "model": model_name,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": construct_prompt(patient_data, get_doctors_data) }
    ],
    "repetition_penalty": 1.1,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_tokens": 1024
    })

    headers = {
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {api_key}"
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    result = response.json()
    content = result['choices'][0]['message']['content']

    return content

make_request