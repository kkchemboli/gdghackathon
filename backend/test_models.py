import os
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")

def test_model(model_name, location):
    print(f"Testing model: {model_name} in {location}")
    try:
        vertexai.init(project="393482995031", location=location)
        model = GenerativeModel(model_name)
        response = model.generate_content("Hi")
        print(f"✅ {model_name} works in {location}!")
        return True
    except Exception as e:
        # print(f"❌ {model_name} failed in {location}: {e}")
        return False

if __name__ == "__main__":
    models_to_test = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-001",
    ]
    locations = ["us-west1", "us-central1", "us-east1", "asia-south1", "europe-west1"]
    
    for loc in locations:
        for m in models_to_test:
            if test_model(m, loc):
                print(f"FOUND WORKING COMBINATION: {m} in {loc}")
                exit(0)
    print("No working combination found.")
