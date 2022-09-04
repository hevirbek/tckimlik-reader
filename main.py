import io
from PIL import Image
import easyocr
import streamlit as st
from datetime import datetime
from dataclasses import dataclass


@st.cache
def load_model():
    return easyocr.Reader(lang_list=['tr'], model_storage_directory='.')


reader = load_model()


@dataclass
class Citizen:
    identity_no: str = None
    name: str = None
    surname: str = None
    date_of_birth: str = None
    document_no: str = None
    gender: str = None
    valid_until: str = None


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


@st.cache
def get_info(img):
    citizen = Citizen()

    results = reader.readtext(img)

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
    if (uploaded_file.size / (1024*1024)) < 2.1:
        bytes_data = uploaded_file.read()
        img = Image.open(io.BytesIO(bytes_data))

        with st.spinner('İşlem yapılıyor...'):
            citizen = get_info(img)

        if check_citizen(citizen):
            st.write("Fullname: **" + citizen.name +
                     " " + citizen.surname + "**")
            st.write("TC: **" + citizen.identity_no + "**")
            st.write("Birthday: **" + citizen.date_of_birth + "**")
            st.write("Gender: **" + citizen.gender + "**")
        else:
            st.error('Hata oluştu. Daha net bir fotoğraf yükleyin!')
    else:
        st.error('Dosya boyutu en fazla 2MB olmalıdır :(')
