import requests
import json
url = "https://api.awanllm.com/v1/chat/completions"

payload = json.dumps({
  "model": MODEL_NAME,
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": """
    This is patient data:  +
 [{'Name': 'Heather Hunter', 'Country': 'Kazakhstan', 'Sex': 'Male', 'Date_of_Birth': '1994-03-27', 'Age': 31, 'Allergies': nan, 'Location': 'Hornstad', 'Medicine': 'Metformin, Atorvastatin, Omeprazole', 'Mass (kg)': 79.5, 'Height (cm)': 152, 'Medical_History': nan, 'Diagnosed_Disease': 'Lung Adenocarcinoma', 'CEA (ng/mL)': 3.7, 'LDH (U/L)': 172.6, 'Ca 19-9 (U/mL)': 72.1, 'CA 19-9 (U/mL)': nan, 'Bilirubin (mg/dL)': nan, 'Amylase (U/L)': nan, 'CA-125 (U/mL)': nan, 'HE4 (pmol/L)': nan, 'AFP (ng/mL)': nan, 'CA 72-4 (U/mL)': nan, 'Pepsinogen I/II Ratio': nan, 'H. pylori IgG': nan, 'PSA (ng/mL)': nan, 'ALP (U/L)': nan, 'Testosterone (ng/dL)': nan, 'Estradiol (pg/mL)': nan, 'Progesterone (ng/mL)': nan, 'Hemoglobin (g/dL)': nan, 'Fecal Occult Blood': nan, 'CA 15-3 (U/mL)': nan, 'Estrogen Receptor': nan, 'HER2/neu Status': nan}]; 
 [{'Name': 'Justin Cervantes', 'Country': 'UK', 'Hospital': 'Mayo Clinic', 'Specialization': 'Breast Cancer', 'Experience (years)': 12, 'Success Ratio': 0.72, 'Review Score': 4.6, 'H-Index': 74}]
 [{'Name': 'Corey Freeman', 'Country': 'UK', 'Hospital': 'Stanford Health', 'Specialization': 'Prostate Cancer', 'Experience (years)': 5, 'Success Ratio': 0.68, 'Review Score': 3.8, 'H-Index': 8}]
 [{'Name': 'Blake Herrera', 'Country': 'France', 'Hospital': 'Stanford Health', 'Specialization': 'Pancreatic Cancer', 'Experience (years)': 19, 'Success Ratio': 0.84, 'Review Score': 4.7, 'H-Index': 5}]
 [{'Name': 'Elizabeth Johnson', 'Country': 'Germany', 'Hospital': 'Stanford Health', 'Specialization': 'Gastric Cancer', 'Experience (years)': 13, 'Success Ratio': 0.7, 'Review Score': 4.9, 'H-Index': 48}]
 [{'Name': 'Timothy Gray', 'Country': 'UK', 'Hospital': 'Cleveland Clinic', 'Specialization': 'Ovarian Cancer', 'Experience (years)': 8, 'Success Ratio': 0.77, 'Review Score': 4.0, 'H-Index': 38}]
 [{'Name': 'Ashley Jones', 'Country': 'USA', 'Hospital': 'UCLA Medical', 'Specialization': 'Lung Adenocarcinoma', 'Experience (years)': 34, 'Success Ratio': 0.77, 'Review Score': 4.3, 'H-Index': 51}]
 [{'Name': 'Linda Hudson', 'Country': 'France', 'Hospital': 'Cleveland Clinic', 'Specialization': 'Prostate Cancer', 'Experience (years)': 26, 'Success Ratio': 0.73, 'Review Score': 3.9, 'H-Index': 15}]
 [{'Name': 'Gina Reynolds', 'Country': 'France', 'Hospital': 'Cleveland Clinic', 'Specialization': 'Ovarian Cancer', 'Experience (years)': 13, 'Success Ratio': 0.8, 'Review Score': 4.8, 'H-Index': 25}]
 [{'Name': 'Sue Mcclure', 'Country': 'Canada', 'Hospital': 'MD Anderson', 'Specialization': 'Pancreatic Cancer', 'Experience (years)': 26, 'Success Ratio': 0.74, 'Review Score': 4.9, 'H-Index': 14}]
 [{'Name': 'Michael Fields', 'Country': 'Germany', 'Hospital': 'Charité Berlin', 'Specialization': 'Colorectal Cancer', 'Experience (years)': 19, 'Success Ratio': 0.78, 'Review Score': 5.0, 'H-Index': 76}]
 This is doctors data, find most appropriate doctor for the patient and list 3 of them
 """},
  ],
  "repetition_penalty": 1.1,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40,
  "max_tokens": 1024
})
headers = {
  'Content-Type': 'application/json',
  'Authorization': f"Bearer {AWANLLM_API_KEY}"
}

response = requests.request("POST", url, headers=headers, data=payload)
result = response.json()
content = result['choices'][0]['message']['content']

print(content)