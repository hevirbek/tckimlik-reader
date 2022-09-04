import numpy as np
import matplotlib.pyplot as plt
import cv2
import easyocr
import streamlit as st
from datetime import datetime

@st.cache
def load_model():
    return easyocr.Reader(lang_list=['tr'], model_storage_directory='.')


reader = load_model()


class Citizen:
    def __init__(self, identity_no=None, name=None, surname=None, date_of_birth=None, document_no=None, gender=None, valid_until=None):
        self.identity_no = identity_no
        self.name = name
        self.surname = surname
        self.date_of_birth = date_of_birth
        self.document_no = document_no
        self.gender = gender
        self.valid_until = valid_until


def is_date(s: str) -> bool:
    try:
        date = datetime.strptime(s, "%d.%m.%Y").date()
        return date
    except:
        return None


def check_citizen(c: Citizen):
    if c.name and c.surname and c.date_of_birth and c.identity_no and c.gender:
        return True
    return False


def get_info(img):
    citizen = Citizen()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17)

    results = reader.readtext(bfilter)

    for i, w in enumerate(results):
        result = w[1]
        date = is_date(result)
        if len(result.strip()) == 11 and result.strip().isnumeric():
            citizen.identity_no = result
        elif 'surname' in result.lower():
            citizen.surname = results[i+1][1]
        elif 'name(s)' in result.lower():
            citizen.name = results[i+1][1]
        elif date != None and date.year < datetime.today().year:
            citizen.date_of_birth = result
        elif date != None and date.year >= datetime.today().year:
            citizen.valid_until = result
        elif result.strip().replace(" ", "").lower() in ['e/m', 'k/f', 'e', 'm', 'k', 'f']:
            if 'e' in result.strip().replace(" ", "").lower():
                citizen.gender = 'E/M'
            elif 'k' in result.strip().replace(" ", "").lower():
                citizen.gender = 'K/F'

    return citizen


st.write("""
# TC Kimlik Kartından Bilgileri Çekmek
Kimliğinizin ön yüzünü yükleyin!
""")

uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    # img = cv2.imread(uploaded_file.name)

    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)

    with st.spinner('İşlem yapılıyor...'):
        citizen = get_info(img)

    if check_citizen(citizen):
        st.write("Fullname: **" + citizen.name + " " + citizen.surname + "**")
        st.write("TC: **" + citizen.identity_no + "**")
        st.write("Birthday: **" + citizen.date_of_birth + "**")
        st.write("Gender: **" + citizen.gender + "**")
    else:
        st.error('Hata oluştu. Daha net bir fotoğraf yükleyin!')
