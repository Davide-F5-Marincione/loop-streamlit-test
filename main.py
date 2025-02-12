import numpy as np
import streamlit as st
from scipy.io import wavfile
import streamlit_survey as ss
import os
import random
import json

if st.session_state.get('samples_list', None) is None:
    samples = list(filter(lambda x: x.endswith(".wav"), os.listdir('samples')))
    random.shuffle(samples)

    st.session_state.samples_list = samples

## Title
survey = ss.StreamlitSurvey("Seamless survey")
def prep_to_send(data):
    ret = {}
    data = json.decoder.JSONDecoder().decode(data)
    for key in data.keys():
        if key.endswith(".wav"):
            if type(data[key]["value"]) == str:
                ret[key] = int(data[key]["value"][:1])
            else:
                ret[key] = int(data[key]["value"])
    return ret

pages = survey.pages(len(st.session_state.samples_list) + 2, progress_bar=True, on_submit=lambda: st.json(prep_to_send(survey.to_json())))

with pages:
    if pages.current == 0:
        st.title('Seamless survey')
        st.header('Instructions')
        st.write("We've generated a bunch of audio samples and have stitched their ends to make them loop.")
        st.write("The samples are repeated, therefore with the stitch in the middle of the track; your task is to rate their seamlessness, where 1=Terrible and 5=Excellent.") 
    elif pages.current <= len(st.session_state.samples_list):
        i = pages.current - 1
        sample_name = st.session_state.samples_list[i]
        sample_rate, sample = wavfile.read(os.path.join('samples', sample_name))
        st.audio(sample, format='audio/wav', start_time=0, loop=False, sample_rate=sample_rate)
        survey.radio("Quality of the stitch", options=["1 (terrible)", "2", "3", "4", "5 (excellent)"], horizontal=True, index=2, id=sample_name)
    else:
        st.write("Thank you for participating in the survey!")
        st.write("Press 'Submit' to show your results. Send them to Davide!")