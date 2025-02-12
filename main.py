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
survey = ss.StreamlitSurvey("Seamlessness survey")
pages = survey.pages(len(st.session_state.samples_list) + 1, progress_bar=True, on_submit=lambda: st.json(survey.to_json()))

with pages:
    if pages.current == 0:
        st.title('Seamlessness survey')
        st.header('Instructions')
        st.write("We've connected the end and the start of some audio samples.")
        st.write("Your task is to select your confidence that the sample was generated from a non-looping music model (1) and a looping one (5).")
    else:
        i = pages.current - 1
        sample_name = st.session_state.samples_list[i]
        sample_rate, sample = wavfile.read(os.path.join('samples', sample_name))
        sample = np.concatenate([sample[-sample_rate:], sample[:sample_rate]])
        st.audio(sample, format='audio/wav', start_time=0, loop=False, sample_rate=sample_rate)
        survey.radio("Confidence", options=list(range(1, 6)), horizontal=True, index=2, id=sample_name)