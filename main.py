import numpy as np
import streamlit as st
from scipy.io import wavfile
import streamlit_survey as ss
import os
import random

if st.session_state.get('samples_list', None) is None:
    samples = list(filter(lambda x: x.endswith(".wav"), os.listdir('samples')))
    random.shuffle(samples)

    st.session_state.samples_list = samples

## Title
survey = ss.StreamlitSurvey("Seamless survey")
pages = survey.pages(len(st.session_state.samples_list) + 2, progress_bar=True, on_submit=lambda: st.json(survey.to_json()))

with pages:
    if pages.current == 0:
        st.title('Seamless survey')
        st.header('Instructions')
        st.write("We've generated a bunch of audio samples from two music models.")
        st.write("One of the two models is made for looping, the other is not.")
        st.write("You are going to listen to the seam of the audio samples made by the two models, your task is to rate how confident you are the sample is from the non-looping model (1) or the looping one (5). When in doubt, you can always rate the sample with either a 2, 3 or 4.") 
    elif pages.current <= len(st.session_state.samples_list):
        i = pages.current - 1
        sample_name = st.session_state.samples_list[i]
        sample_rate, sample = wavfile.read(os.path.join('samples', sample_name))
        sample = np.concatenate([sample[-sample_rate:], sample[:sample_rate]])
        st.audio(sample, format='audio/wav', start_time=0, loop=False, sample_rate=sample_rate)
        survey.radio("Confidence in type of model", options=["1 (non-loop)", "2 (maybe non-loop)", "3 (don't know)", "4 (maybe loop)", "5 (loop)"], horizontal=True, index=2, id=sample_name)
    else:
        st.write("Thank you for participating in the survey!")
        st.write("Press 'Submit' to save your responses. Send them to Davide!")