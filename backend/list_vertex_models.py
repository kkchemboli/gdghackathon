import os
import vertexai
from google.cloud import aiplatform
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = "us-west1"

def list_models():
    print(f"Listing models in project {PROJECT_ID}, location {LOCATION}")
    try:
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        models = aiplatform.Model.list()
        print(f"Found {len(models)} models.")
        for model in models:
            print(f"- {model.display_name} ({model.resource_name})")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
