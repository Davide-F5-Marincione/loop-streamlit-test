import streamlit as st
import os
import requests
import json
import random
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# -----------------------------------------------------------------------------
# Inject custom CSS for radio buttons styled as boxes (mobile friendly)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
/* Radio buttons styled as boxes with semi-transparent backgrounds */
div[role="radiogroup"] {
  display: flex;
  flex-direction: row;
  align-items: center;
}
div[role="radiogroup"] input[type="radio"] {
  display: none;
}
div[role="radiogroup"] > label {
  background-color: rgba(68,68,68,0.7);
  color: white;
  padding: 10px 20px;
  margin-right: 10px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  text-align: center;
}
div[role="radiogroup"] > input[type="radio"]:checked + label {
  background-color: rgba(204,153,0,0.9);
  color: black;
}
div[role="radiogroup"] > label:hover {
  background-color: rgba(102,102,102,0.7);
}

/* Media query for small screens (mobile) */
@media screen and (max-width: 480px) {
  div[role="radiogroup"] > label {
    padding: 5px 10px;
    margin-right: 5px;
    font-size: 12px;
  }
}
</style>
""",
            unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Configuration: GitHub Gist API details (internal)
# -----------------------------------------------------------------------------
CREDENTIALS_JSON = st.secrets["gdrive"]["credentials"]
GIST_ID = st.secrets["github_gist"]["gist_id"]
GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"

FOLDER_1 = "ours"
FOLDER_2 = "baseline"

# -----------------------------------------------------------------------------
# Load evaluator sample assignments from external JSON file ("assignments.json")
# -----------------------------------------------------------------------------
try:
    with open("assignments.json", "r") as f:
        evaluator_samples = json.load(f)["names"]
    evaluator_samples = [k.lower() for k in evaluator_samples]
except Exception as e:
    st.error("Errore nel caricamento del file degli assegnamenti: " + str(e))
    st.stop()

# -----------------------------------------------------------------------------
# Full evaluation criteria description (UI text in Italian)
# -----------------------------------------------------------------------------
CRITERIA_DESCRIPTION = """
Abbiamo generato una serie di tracce audio e unito le loro estremità per farle riprodurre in loop.
Le tracce vengono ripetute, e la loro giunzione si trova a metà di ogni campione ascoltato; il tuo compito è valutare la fluidità della transizione tra 1 e 5.
La scala è in qualità crescente. Una clip con un taglio netto distintamente udibile avrà un voto basso (e.g. 1 o 2), mentre un sample con un taglio impercettibile avrà un voto alto (e.g. 4 o 5). Un buon loop dovrebbe avere un taglio impercettibile.

Note:
- Puoi ignorare, nella tua valutazione, la qualità audio della registrazione (mono 32kHz) e cercare di valutare principalmente il contenuto. 
- Sei libero di chiudere questa pagina in qualsiasi momento e riprendere in seguito: i tuoi risultati sono salvati ogni volta che invii una valutazione, e riprenderai da dove hai lasciato.
- È fortemente suggerito l'utilizzo di cuffie o altoparlanti dedicati per ascoltare i campioni.
- Ti chiediamo gentilmente di NON condividere il link a questo sito web con nessuno (almeno che non ti sia stato chiesto di farlo).
"""


def get_audio_files_from_folder(folder, num_samples=15):
    try:
        all_files = [folder + "/" + f for f in os.listdir(folder) if f.endswith((".mp3", ".wav", ".ogg"))]
        return random.sample(all_files, num_samples)  # Randomly select 'num_samples' files
    except FileNotFoundError:
        return []

# -----------------------------------------------------------------------------
# Helper Functions for GitHub Gist Operations (internal)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Helper Functions for Google Drive Operations (internal)
# -----------------------------------------------------------------------------
def get_gist_content(filename: str) -> str:
    try:
        credentials = service_account.Credentials.from_service_account_info(
            CREDENTIALS_JSON
        )
        drive_service = build("drive", "v3", credentials=credentials)
        results = (
            drive_service.files()
            .list(q=f"name='{filename}'", fields="files(id)")
            .execute()
        )
        items = results.get("files", [])
        if items:
            file_id = items[0]["id"]
            request = drive_service.files().get_media(fileId=file_id)
            file_content = request.execute()
            return file_content.decode("utf-8")
        else:
            return None
    except Exception as e:
        st.error(f"Errore durante il recupero del file da Google Drive: {e}")
        return None


def count_completed_evaluations(csv_filename: str) -> int:
    content = get_gist_content(csv_filename)
    if not content:
        return 0
    lines = content.strip().split("\n")
    return max(0, len(lines) - 1)


def append_evaluation(csv_filename: str, new_line: str) -> None:
    try:
        credentials = service_account.Credentials.from_service_account_info(
            CREDENTIALS_JSON
        )
        drive_service = build("drive", "v3", credentials=credentials)
        content = get_gist_content(csv_filename)
        if not content:
            content = "username,sample_id,rating\n"
        updated_content = content + new_line
        media_body = MediaFileUpload(io.BytesIO(updated_content.encode("utf-8")), mimetype='text/csv', resumable=True)
        results = drive_service.files().list(q=f"name='{csv_filename}'", fields="files(id)").execute()
        items = results.get("files", [])
        if items:
            file_id = items[0]["id"]
            updated_file = drive_service.files().update(fileId=file_id, media_body=media_body).execute()
        else:
            file_metadata = {'name': csv_filename}
            file = drive_service.files().create(body=file_metadata, media_body=media_body, fields='id').execute()
        st.success("Valutazione inviata correttamente!")
    except Exception as e:
        st.error(f"Errore durante l'aggiornamento del file Google Drive: {e}")


def remove_last_evaluation(csv_filename: str) -> bool:
    try:
        credentials = service_account.Credentials.from_service_account_info(
            CREDENTIALS_JSON
        )
        drive_service = build("drive", "v3", credentials=credentials)
        content = get_gist_content(csv_filename)
        if content:
            lines = content.strip().split("\n")
            if len(lines) > 1:
                updated_content = "\n".join(lines[:-1]) + "\n"
                media_body = MediaFileUpload(io.BytesIO(updated_content.encode("utf-8")), mimetype='text/csv', resumable=True)
                results = drive_service.files().list(q=f"name='{csv_filename}'", fields="files(id)").execute()
                items = results.get("files", [])
                if items:
                    file_id = items[0]["id"]
                    updated_file = drive_service.files().update(fileId=file_id, media_body=media_body).execute()
                    return True
                else:
                    return False
        return False
    except Exception as e:
        st.error(f"Errore durante l'aggiornamento del file Google Drive: {e}")
        return False


# -----------------------------------------------------------------------------
# Main Interface (internal code in English, UI text in Italian)
# -----------------------------------------------------------------------------
st.title("Valutazione Audio")

# --- Login Phase ---
if "username" not in st.session_state:
    raw_username = st.text_input(
        "Inserisci il tuo username (esattamente come assegnato)")
    if st.button("Continua"):
        if not raw_username.strip():
            st.warning("Inserisci un username.")
        else:
            username_lower = raw_username.strip().lower()
            if username_lower not in evaluator_samples:
                st.error(
                    "Username non riconosciuto. Riprova o chiedi supporto.")
            else:
                st.session_state.username = username_lower
                st.rerun()
    st.stop()

username = st.session_state.username

# --- Intermediate Phase ---
if "evaluation_started" not in st.session_state:
    st.markdown(CRITERIA_DESCRIPTION)

    if st.button("Inizia valutazione"):
        st.session_state.evaluation_started = True
        st.rerun()
    st.stop()

# --- Evaluation Phase ---
random.seed(username)  # Seed the random number generator for reproducibility
folder_1_samples = get_audio_files_from_folder(FOLDER_1)
folder_2_samples = get_audio_files_from_folder(FOLDER_2)
assigned_samples = folder_1_samples + folder_2_samples
random.shuffle(assigned_samples)

num_samples = len(assigned_samples)
csv_filename = f"{username}_results.csv"

if "current_sample_index" not in st.session_state:
    st.session_state.current_sample_index = count_completed_evaluations(
        csv_filename)

# Final screen: if all samples are evaluated, show final message with undo option.
if st.session_state.current_sample_index >= num_samples:
    st.success("Hai completato tutte le valutazioni. Grazie!")

    def undo_last_completed():
        if st.session_state.current_sample_index > 0:
            if remove_last_evaluation(csv_filename):
                st.session_state.current_sample_index -= 1
                st.warning("L'ultima valutazione è stata annullata")

    st.button("Annulla l'ultima valutazione", on_click=undo_last_completed)
    st.stop()

current_sample = assigned_samples[st.session_state.current_sample_index]

st.subheader(
    f"Campione #{st.session_state.current_sample_index+1} di {num_samples}")

audio_filepath = current_sample
if os.path.exists(audio_filepath):
    st.audio(audio_filepath, format="audio/wav")
else:
    st.warning("File audio non trovato.")
    
st.markdown("---\r\nPercettibilità del taglio")
rating = st.radio(" ",
    options=["1 (taglio netto)", "2", "3", "4", "5 (taglio impercettibile)"],
    index=None,
    key=f"rating_{st.session_state.current_sample_index}",
    label_visibility="hidden")

if rating is not None:
    if rating == "1 (taglio netto)":
        rating = 1
    elif rating == "5 (taglio impercettibile)":
        rating = 5
    else:
        rating = int(rating[0])

# --- Callback Functions ---
def submit_evaluation():
    if rating is None:
        st.warning("Seleziona una valutazione prima di inviare.")
        return
    new_line = f"{username},{current_sample},{rating}\n"
    append_evaluation(csv_filename, new_line)
    st.session_state.current_sample_index += 1
    # st.rerun()


def undo_evaluation():
    if st.session_state.current_sample_index <= 0:
        st.warning("Nessuna valutazione da annullare.")
        return
    if remove_last_evaluation(csv_filename):
        st.session_state.current_sample_index -= 1
        st.warning("L'ultima valutazione è stata annullata")
        # st.rerun()
    else:
        st.error("Impossibile annullare l'ultima valutazione.")


col_undo, col_submit = st.columns([1, 2])
with col_undo:
    st.button("Annulla l'ultima valutazione", on_click=undo_evaluation)
with col_submit:
    st.button("Invia valutazione e continua", on_click=submit_evaluation)
