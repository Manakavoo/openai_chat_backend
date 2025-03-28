import json
import os
from youtube_transcript_api import YouTubeTranscriptApi
import requests

def get_transcript(video_id, json_file='video_transcripts.json'):
    """
    Retrieve video transcript with JSON caching mechanism.
    
    :param video_id: YouTube video ID
    :param json_file: Path to the JSON file for caching transcripts
    :return: Dictionary containing video title and transcript
    """
    # Initialize existing transcripts
    existing_transcripts = {}
    
    # Step 1: Check if JSON file exists and has the transcript
    try:
        # If JSON file exists, try to load the transcript
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                existing_transcripts = json.load(f)
                
            # If transcript exists in JSON, return it
            if video_id in existing_transcripts:
                print(f"Transcript found in JSON for video {video_id}")
                return existing_transcripts[video_id]
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, we'll use an empty dictionary
        existing_transcripts = {}
    
    # Step 2: Retrieve transcript using YouTube packages
    try:
        # Construct video URL
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Title retrieval method
        title = None
        
        # Method 1: Requests-based web scraping
        try:
            response = requests.get(video_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            title = response.text.split('<title>')[1].split('</title>')[0].replace(' - YouTube', '').strip()
        except Exception as requests_error:
            print(f"Requests title retrieval error: {requests_error}")
        
        # Fallback: If requests method fails, use the transcript metadata
        if not title:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                title = transcript_list.find_transcript(['en']).fetch()[0].get('text', 'Untitled')
            except Exception as transcript_title_error:
                print(f"Transcript title retrieval error: {transcript_title_error}")
        
        # Get transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Format transcript
        transcript_list = [f"{entry['start']}s: {entry['text']}" for entry in transcript]
        transcript_text = "\n".join(transcript_list)
        
        # Prepare result
        result = {
            "title": title or "Title Not Found",
            "transcript": transcript_text if len(transcript_text) < 20000 else transcript_text[:20000] + "...",
            "length": len(transcript)
        }
        
        # Step 3: Save to JSON for future use
        try:
            # Update existing transcripts
            existing_transcripts[video_id] = result
            
            # Save updated transcripts to JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(existing_transcripts, f, ensure_ascii=False, indent=4)
            
            print(f"Transcript saved to JSON for video {video_id}")
        except Exception as save_error:
            print(f"Error saving transcript to JSON: {save_error}")
        
        return result
    
    except Exception as e:
        return {"error": str(e)}

# Example usage
def main():
    # List of video IDs to process
    video_ids = [  # your first video
        "dcXqhMqhZUo"  # add more video IDs as needed
    ]
    
    # Process each video ID
    for video_id in video_ids:
        print(f"\nProcessing video ID: {video_id}")
        result = get_transcript(video_id)
        print(result.get('title', 'Title Not Found'))
        print(len(result.get('transcript', 'Transcript Not Found')))
        # # Check if transcript was successfully retrieved
        # if 'error' not in result:
        #     print("Title:", result['title'])
        #     print("Transcript Length:", len(result['transcript']))
        # else:
        #     print("Error:", result['error'])

if __name__ == "__main__":
    main()