import numpy as np
import streamlit as st
from scipy.io import wavfile
import os
import random
import time
import pandas as pd

if st.session_state.get('pairs_list', None) is None:
    pairs_list = list(set(map(lambda x: x[:-4].split("_")[-1], filter(lambda x: x.endswith(".wav"), os.listdir('samples')))))
    pairs_list.sort()
    random.shuffle(pairs_list)

    st.session_state.pairs_list = pairs_list
    st.session_state.i = 0
    st.session_state.orders = set()
    st.session_state.thinks = set()
    st.session_state.start_time = time.time()

## Title
st.title('Audio looping A/B test')
st.header('Instructions')
st.write("You will be presented with pairs of audio samples, one of which is made with a looping model, the other is not. Your task is to determine which one is the looped version.")

def circular_pad_to(wav, seconds=20, sample_rate=32000):
    start_at = random.randint(0, len(wav) - 1)
    return np.tile(wav, (seconds * sample_rate) // len(wav) + 2)[start_at:start_at+seconds * sample_rate]

prefix = 'samples/67_'

def load_pairs(name, seconds=20):
    sr_non, non_looping = wavfile.read(f'{prefix}{name}.wav')
    non_looping = circular_pad_to(non_looping, seconds=seconds, sample_rate=sr_non)
    sr, looping = wavfile.read(f'{prefix}loop_{name}.wav')
    looping = circular_pad_to(looping, seconds=seconds, sample_rate=sr)
    return non_looping, sr_non, looping, sr

def select_A(i):
    def on_click():
        assert (i, False) not in st.session_state.thinks
        st.session_state.thinks.add((i,True))
    return on_click

def select_B(i):
    def on_click():
        assert (i, True) not in st.session_state.thinks
        st.session_state.thinks.add((i,False))
    return on_click


i = st.session_state.i
if i < len(st.session_state.pairs_list):
    pair = st.session_state.pairs_list[i]

    A, a_sr, B, b_sr = load_pairs(pair)
    A_loops = bool(random.randint(0, 1))
    st.session_state.orders.add((pair, A_loops))
    if A_loops:
        A, B = B, A
    st.write(f"**Pair n.{i+1:02d}/{len(st.session_state.pairs_list)}**:")
    st.write(f" *{pair}*")
    a,b,c = st.columns([1,8,4])
    with a:
        st.write("A:")
    with b:
        st.audio(A, format='audio/wav', start_time=0, loop=False, sample_rate=a_sr)
    with c:    
        st.button("A is from looping model", key=f"btn_A_{i}", on_click=select_A(pair))
    a,b,c = st.columns([1,8,4])
    with a:
        st.write("B:")
    with b:
        st.audio(B, format='audio/wav', start_time=0, loop=False, sample_rate=b_sr)
    with c:
        st.button("B is from looping model", key=f"btn_B_{i}", on_click=select_B(pair))
    st.session_state.i += 1
else:
    st.write("You have completed the test")
    st.write(f"You correctly chose: {len(st.session_state.thinks.intersection(st.session_state.orders))}/{len(st.session_state.orders)}")

    # Show table
    df = pd.DataFrame()
    for i, (pair, loops) in enumerate(st.session_state.orders):
        df.loc[i, 'Sample'] = pair
        df.loc[i, 'Correct'] = (pair, loops) in st.session_state.thinks
    st.write(df)