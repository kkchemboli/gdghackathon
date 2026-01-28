import os
import vertexai
from vertexai.preview import rag
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = "us-west1"

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print(f"Initialized Vertex AI with project {PROJECT_ID}")
else:
    print("GCP_PROJECT_ID not set")
    exit(1)

def inspect_corpus(user_id):
    display_name = f"user-{user_id}"
    print(f"Looking for corpus: {display_name}")
    
    corpora = rag.list_corpora()
    target_corpus = None
    
    found_count = 0
    for corpus in corpora:
        if corpus.display_name == display_name:
            print(f"Found corpus: {corpus.name} (Created: {corpus.create_time})")
            target_corpus = corpus
            found_count += 1
            
            # List files in THIS corpus
            print(f"  Files in {corpus.name}:")
            try:
                files = rag.list_files(corpus_name=corpus.name)
                file_count = 0
                for file in files:
                    print(f"    - {file.name} (Display: {file.display_name})")
                    file_count += 1
                if file_count == 0:
                    print("    (No files)")
            except Exception as e:
                print(f"    Error listing files: {e}")

    print(f"Total corpora found with display name '{display_name}': {found_count}")

if __name__ == "__main__":
    inspect_corpus("test-user-integration")
