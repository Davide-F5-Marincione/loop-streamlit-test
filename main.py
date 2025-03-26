import streamlit as st
import requests
import json
import base64
import os
import random
import uuid

# Load GitHub credentials from environment variables or Streamlit secrets
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", st.secrets.get("GITHUB_TOKEN"))
GITHUB_REPO = os.getenv("GITHUB_REPO", st.secrets.get("GITHUB_REPO"))

GITHUB_FILE_PATH = "evaluations.json"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"

FOLDER_1 = "bp_resc"  # Folder containing the first 100 audio samples
FOLDER_2 = "test_folder"  # Folder containing the second 100 audio samples

def get_audio_files_from_folder(folder, num_samples=15):
    try:
        all_files = [f for f in os.listdir(folder) if f.endswith((".mp3", ".wav", ".ogg"))]
        return random.sample(all_files, num_samples)  # Randomly select 'num_samples' files
    except FileNotFoundError:
        return []

# Initialize session state
if "evaluator_name" not in st.session_state:
    st.session_state.evaluator_name = None  # Store evaluator name

if "audio_order" not in st.session_state:
    folder_1_samples = get_audio_files_from_folder(FOLDER_1)
    folder_2_samples = get_audio_files_from_folder(FOLDER_2)
    
    all_samples = folder_1_samples + folder_2_samples
    random.shuffle(all_samples)  # Randomize order
    st.session_state.audio_order = all_samples
    st.session_state.audio_index = 0  # Start with the first audio

# Function to get existing file content from GitHub
def get_github_file():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)

    if response.status_code == 200:
        file_info = response.json()
        content = base64.b64decode(file_info["content"]).decode("utf-8")
        sha = file_info["sha"]
        return json.loads(content), sha
    return [], None

# Function to update file on GitHub
def update_github_file(new_data):
    existing_data, sha = get_github_file()
    existing_data.append(new_data)
    updated_content = json.dumps(existing_data, indent=4)

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = {
        "message": "Updated evaluation results",
        "content": base64.b64encode(updated_content.encode()).decode(),
        "branch": "main",
    }
    if sha:
        data["sha"] = sha

    response = requests.put(GITHUB_API_URL, headers=headers, json=data)
    return response.status_code in [200, 201]

# Streamlit UI
st.title("Valutazione delle transizioni in loop")

# Step 1: Ask for evaluator name if not set
if st.session_state.evaluator_name is None:

    st.header('Istruzioni')
    st.write("Abbiamo generato una serie di tracce audio e abbiamo unito le loro estremità per farle riprodurre in loop.")
    st.write("Le tracce vengono ripetute, e la loro giunzione si trova a metà di ogni campione ascoltato; il tuo compito è valutare la fluidità della transizione, dove 1=Terribile e 5=Eccellente.") 
    
    evaluator_name = st.text_input("Inserisci il tuo nome per iniziare:")
    if st.button("Inizia la valutazione") and evaluator_name:
        evaluator_uuid = str(uuid.uuid4())
        st.session_state.evaluator_name = evaluator_name
        st.session_state.evaluator_uuid = evaluator_uuid  # Store the generated UUID
        st.session_state.evaluator_file = f"{evaluator_uuid}.json"
        st.rerun()  # Refresh to start evaluation
else:
    st.write(f"Valutatore: **{st.session_state.evaluator_name}**")

    # Step 2: Show progress
    total_samples = len(st.session_state.audio_order)
    current_index = st.session_state.audio_index + 1  # 1-based index
    progress = current_index / total_samples if total_samples > 0 else 0

    st.progress(progress)  # Show progress bar
    st.write(f"**{current_index}/{total_samples} campioni valutati**")

    # Step 3: Show the current audio sample
    if st.session_state.audio_index < total_samples:
        current_audio = st.session_state.audio_order[st.session_state.audio_index]
        st.audio(os.path.join(AUDIO_DIR, current_audio), format="audio/mp3")
        
        rating = st.radio("Qualità della transizione", options=["1 (terribile)", "2", "3", "4", "5 (eccellente)"], horizontal=True)
        
        if rating == "1 (terribile)":
            rating = 1
        elif rating == "5 (eccellente)":
            rating = 5
        else:
            rating = int(rating[0])

        # Change button text for the last sample
        is_last_sample = st.session_state.audio_index == total_samples - 1
        button_text = "Invia l'ultima valutazione" if is_last_sample else "Invia e continua"

        if st.button(button_text):
            evaluation_data = {
                "evaluator": st.session_state.evaluator_name,
                "sample": current_audio,
                "rating": rating
            }

            if update_github_file(evaluation_data):
                st.success("Valutazione inviata!")
                
                # Move to the next audio
                st.session_state.audio_index += 1
                st.rerun()
            else:
                st.error("Ci sono stati problemi nell'inviare la valutazione :(")
    else:
        st.write("🎉 **Valutazione completata! Grazie mille.** 🎉")