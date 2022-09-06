import io
from PIL import Image, ImageFilter, JpegImagePlugin
from easyocr import Reader
import streamlit as st
from datetime import datetime
from dataclasses import dataclass
import uuid
import os


@st.cache
def load_model():
    return Reader(lang_list=['en', 'tr'], model_storage_directory='.', gpu=False)


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
    father_name: str = None
    mother_name: str = None


def is_date(s: str) -> bool:
    try:
        date = datetime.strptime(s, "%d.%m.%Y").date()
        return date
    except:
        return None


def is_document_no(s: str) -> bool:
    if not s[0].isalpha():
        return False
    if not s[3].isalpha():
        return False
    if not s[1:3].isnumeric():
        return False
    if not s[4:-1].isnumeric():
        return False
    return True


def check_citizen(c: Citizen, face: str):
    if face == "front":
        if c.name and c.surname and c.date_of_birth and c.identity_no and c.gender and c.document_no and c.valid_until:
            return True
        return False
    elif face == "back":
        if c.mother_name and c.father_name:
            return True
    return False


@st.cache
def get_front_info(img):
    citizen = Citizen()

    results = reader.readtext(img)

    for i, w in enumerate(results):
        result = w[1]
        date = is_date(result)
        if len(result.strip()) == 11 and result.strip().isnumeric():
            citizen.identity_no = result.strip()
        if len(result.strip()) == 9 and is_document_no(result.strip()):
            citizen.document_no = result.strip()
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


@st.cache
def get_back_info(img):
    mother, father = False, False
    mother_taken, father_taken = False, False
    citizen = Citizen()

    results = reader.readtext(img)
    for i, w in enumerate(results):
        result = w[1]
        if 'mother' in result.lower():
            mother = True
        elif 'father' in result.lower():
            father = True

        if (not mother_taken) and mother and result.strip().isalpha() and result.strip().isupper():
            citizen.mother_name = result.strip()
            mother_taken = True
        elif mother_taken and father and result.strip().isalpha() and result.strip().isupper():
            citizen.father_name = result.strip()

    return citizen


st.write("""
# TC Kimlik Kartından Bilgileri Çekmek
Kimliğinizin ön yüzünü yükleyin!
""")

front_file = st.file_uploader("Ön yüz")

if front_file is not None:
    resized = False
    if (front_file.size / (1024*1024)) < 2.1:
        bytes_data = front_file.read()
        img = Image.open(io.BytesIO(bytes_data))

        width, height = img.width, img.height
        is_not_jpeg = type(img) != JpegImagePlugin.JpegImageFile
        if width > 1200 or is_not_jpeg:
            if img.mode in ("RGBA", "P"):
                img = img.convert('RGB')
            new_width = 800
            perception = new_width / width
            new_height = int(height * perception)
            img = img.resize((new_width, new_height))
            fn = str(uuid.uuid1()) + '.jpg'
            img.save(fn)
            img = Image.open(fn)
            resized = True

        with st.spinner('İşlem yapılıyor...'):
            citizen = get_front_info(img)
            if resized:
                os.remove(fn)
                resized = False

        if check_citizen(citizen, "front"):
            st.write("Fullname: **" + citizen.name +
                     " " + citizen.surname + "**")
            st.write("TC: **" + citizen.identity_no + "**")
            st.write("Document No: **" + citizen.document_no + "**")
            st.write("Birthday: **" + citizen.date_of_birth + "**")
            st.write("Gender: **" + citizen.gender + "**")
            st.write("Valid Until: **" + citizen.valid_until + "**")
        else:
            st.error('Hata oluştu. Daha net bir fotoğraf yükleyin!')
    else:
        st.error('Dosya boyutu en fazla 2MB olmalıdır :(')


st.write("""
Kimliğinizin arka yüzünü yükleyin!
""")

back_file = st.file_uploader("Arka yüz")

if back_file is not None:
    resized = False
    if (back_file.size / (1024*1024)) < 2.1:
        bytes_data = back_file.read()
        img = Image.open(io.BytesIO(bytes_data))

        width, height = img.width, img.height
        is_not_jpeg = type(img) != JpegImagePlugin.JpegImageFile
        if width > 1200 or is_not_jpeg:
            if img.mode in ("RGBA", "P"):
                img = img.convert('RGB')
            new_width = 800
            perception = new_width / width
            new_height = int(height * perception)
            img = img.resize((new_width, new_height))
            fn = str(uuid.uuid1()) + '.jpg'
            img.save(fn)
            img = Image.open(fn)
            resized = True

        with st.spinner('İşlem yapılıyor...'):
            citizen = get_back_info(img)
            if resized:
                os.remove(fn)
                resized = False

        if check_citizen(citizen, "back"):
            st.write("Mother Name: **" + citizen.mother_name + "**")
            st.write("Father Name: **" + citizen.father_name + "**")
        else:
            st.error('Hata oluştu. Daha net bir fotoğraf yükleyin!')
    else:
        st.error('Dosya boyutu en fazla 2MB olmalıdır :(')
