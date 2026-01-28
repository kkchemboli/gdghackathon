import os
import vertexai
from vertexai.preview import rag
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = "us-west1"

def test_retrieval(user_id, query):
    print(f"Testing retrieval for user {user_id} with query '{query}'")
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        # Find corpus
        display_name = f"user-{user_id}"
        corpora = rag.list_corpora()
        target_corpus = None
        for corpus in corpora:
            if corpus.display_name == display_name:
                target_corpus = corpus
                break
        
        if not target_corpus:
            print(f"❌ Corpus {display_name} not found")
            return

        print(f"Found corpus: {target_corpus.name}")
        
        thresholds = [0.0, 0.3, 0.5, 0.7, 1.0]
        for t in thresholds:
            print(f"\n--- Testing threshold {t} ---")
            response = rag.retrieval_query(
                rag_resources=[rag.RagResource(rag_corpus=target_corpus.name)],
                text=query,
                similarity_top_k=5,
                vector_distance_threshold=t
            )
            count = len(response.contexts.contexts)
            print(f"Retrieved {count} chunks")
            for i, chunk in enumerate(response.contexts.contexts):
                print(f"  Chunk {i+1} (distance {chunk.distance}): {chunk.text[:100]}...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_retrieval("test-user-integration", "What is this video about?")
