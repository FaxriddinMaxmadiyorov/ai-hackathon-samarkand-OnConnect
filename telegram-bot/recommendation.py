from dotenv import load_dotenv
import os
import requests
import json
import pandas as pd

load_dotenv()

url = "https://api.awanllm.com/v1/chat/completions"
model_name = os.getenv('MODEL_NAME')
api_key = os.getenv('AWANLLM_API_KEY')

def construct_prompt(patient_data, doctors_data):
    return f"""
This is patient data: {patient_data}
This is doctors data: {doctors_data}
Please match the 3 most appropriate doctors to the patient data based on their specialization, experience, and the patient's medical needs.

Return the result in the following format:
1. Dr. [Name] - [Specialization] - [Brief reason for recommendation]
2. Dr. [Name] - [Specialization] - [Brief reason for recommendation]
3. Dr. [Name] - [Specialization] - [Brief reason for recommendation]
"""

def get_doctors_data():
    """Read doctors data from CSV file."""
    try:
        df = pd.read_csv('data/doctors.csv')
        # Convert to list of dictionaries for easier processing
        doctors_list = df.to_dict(orient='records')
        return doctors_list
    except FileNotFoundError:
        print("Warning: doctors.csv file not found. Using sample data.")
        # Sample doctors data if file doesn't exist
        return [
            {"name": "Dr. Smith", "specialization": "Cardiology", "experience": "10 years"},
            {"name": "Dr. Johnson", "specialization": "Neurology", "experience": "8 years"},
            {"name": "Dr. Brown", "specialization": "Orthopedics", "experience": "12 years"},
            {"name": "Dr. Davis", "specialization": "Internal Medicine", "experience": "15 years"},
            {"name": "Dr. Wilson", "specialization": "Pediatrics", "experience": "7 years"}
        ]

def read_patient_data(file_path):
    """Read patient data from Excel file."""
    try:
        print(file_path)
        df = pd.read_csv(file_path)
        # Convert to string representation for the prompt
        patient_info = df.to_string(index=False)
        return patient_info
    except Exception as e:
        print(f"Error reading patient data: {e}")
        return f"Error reading patient data from {file_path}"

def make_request(patient_data, doctors_data=None):
    print('Make API request to get doctor recommendations.')
    try:
        if doctors_data is None:
            doctors_data = get_doctors_data()
        
        prompt = construct_prompt(patient_data, doctors_data)
        
        payload = json.dumps({
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a medical assistant that helps match patients with appropriate doctors based on their medical data and needs."},
                {"role": "user", "content": prompt}
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
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return content
        else:
            return f"API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error making API request: {str(e)}"

def get_recommendations(patient_file_path):
    print('GET-RECOMMENDATION')
    print(patient_file_path)

    """Main function to get doctor recommendations for a patient."""
    patient_data = read_patient_data(patient_file_path)
    print('PATIENT-DATA')
    print(patient_data)
    doctors_data = get_doctors_data()
    recommendations = make_request(patient_data, doctors_data)
    return recommendations