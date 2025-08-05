import os
import re
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURATION ---
# 1. PASTE YOUR API KEY HERE
API_KEY = "AIzaSyDk00rhP88XdFYKSj3rYTQiCPAoY9noksA"

# 2. PASTE THE YOUTUBE CHANNEL ID HERE
CHANNEL_ID = "UCe1HeEEIHtXIqkGn0Bu0wRg"

# 3. DEFINE THE OUTPUT FILENAME
OUTPUT_FILENAME = "topics.json"

# This is the regular expression that finds your topics.
TOPIC_REGEX = re.compile(r"(\d{1,2}:\d{1,2}(?::\d{1,2})?)\s*—\s*(.*?)\s*-\s*(.*)")

def main():
    """
    Main function to orchestrate the data fetching and processing.
    """
    if API_KEY == "PASTE_YOUR_API_KEY_HERE" or CHANNEL_ID == "PASTE_THE_CHANNEL_ID_HERE":
        print("🛑 ERROR: Please paste your API_KEY and CHANNEL_ID into the script.")
        return

    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)

        print(f"🔍 Fetching videos for channel ID: {CHANNEL_ID}")
        video_ids = get_all_video_ids(youtube, CHANNEL_ID)
        
        if video_ids is None:
            print("\nScript stopped. Please check the Channel ID and try again.")
            return

        print(f"✅ Found {len(video_ids)} videos. Now fetching details...")

        all_topics = get_topics_from_videos(youtube, video_ids)
        print(f"✅ Found {len(all_topics)} topics across all videos.")

        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(all_topics, f, indent=4, ensure_ascii=False)

        print(f"\n🎉 Success! All topics have been saved to '{OUTPUT_FILENAME}'.")

    except HttpError as e:
        print(f"\nAn HTTP error {e.resp.status} occurred:")
        try:
            error_details = json.loads(e.content.decode('utf-8'))
            print(json.dumps(error_details, indent=2))
        except json.JSONDecodeError:
            print(e.content)
        print("\n🤔 Common causes for errors: API Key, Channel ID, or exceeded quota.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def get_all_video_ids(youtube, channel_id):
    """
    Retrieves all video IDs from a specific channel.
    """
    try:
        request = youtube.channels().list(part="contentDetails", id=channel_id)
        response = request.execute()

        if not response.get("items"):
            print(f"🛑 ERROR: API call succeeded, but found no channel with the ID '{channel_id}'.")
            return None

        playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        video_ids = []
        next_page_token = None
        while True:
            request = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response.get("items", []):
                video_ids.append(item["contentDetails"]["videoId"])
                
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
                
        return video_ids
    except Exception as e:
        print(f"Error during video ID fetch: {e}")
        return None


def get_topics_from_videos(youtube, video_ids):
    """
    Fetches details and publication dates for videos and parses their descriptions.
    """
    all_topics = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        request = youtube.videos().list(
            part="snippet",
            id=",".join(chunk)
        )
        response = request.execute()

        for item in response.get("items", []):
            video_title = item["snippet"]["title"]
            video_id = item["id"]
            description = item["snippet"]["description"]
            # **NEW**: Get the publication date
            published_at = item["snippet"]["publishedAt"]

            found_topics = TOPIC_REGEX.finditer(description)

            for match in found_topics:
                timestamp, topic_name, topic_desc = match.groups()
                topic_data = {
                    "videoTitle": video_title,
                    "videoId": video_id,
                    "timestamp": timestamp.strip(),
                    "topicName": topic_name.strip(),
                    "topicDescription": topic_desc.strip(),
                    "publishedAt": published_at # **NEW**: Save the date
                }
                all_topics.append(topic_data)
                print(f"  -> Found topic '{topic_name.strip()}' in '{video_title}'")
    
    return all_topics


if __name__ == "__main__":
    main()
