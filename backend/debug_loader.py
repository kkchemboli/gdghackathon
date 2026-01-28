from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.youtube import TranscriptFormat

VIDEO_URL = "https://www.youtube.com/watch?v=iiADhChRriM"

def debug_loader():
    print(f"Testing YoutubeLoader with URL: {VIDEO_URL}")
    try:
        loader = YoutubeLoader.from_youtube_url(
            VIDEO_URL,
            add_video_info=False,
            transcript_format=TranscriptFormat.CHUNKS,
            chunk_size_seconds=30,
        )
        documents = loader.load()
        
        if not documents:
            print("❌ No documents loaded!")
            return

        print(f"✅ Loaded {len(documents)} chunks.")
        
        # Print the first few chunks to verify content
        print("\n--- First Chunk Content ---")
        print(documents[0].page_content)
        print("---------------------------")
        
        # Check if content looks like JSON tutorial vs washing machine
        content = " ".join([d.page_content for d in documents]).lower()
        if "json" in content:
            print("✅ Content appears to be about JSON.")
        else:
            print("⚠️ Content does NOT appear to be about JSON.")
            
        if "washing" in content or "drain" in content:
             print("⚠️ Content appears to be about Washing Machines/Draining!")

    except Exception as e:
        print(f"❌ Error loading video: {e}")

if __name__ == "__main__":
    debug_loader()
