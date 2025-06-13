import os
import re
import numpy as np
import tensorflow as tf
import pickle
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.applications.inception_v3 import InceptionV3, preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array

def clean_text(text):
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_captions(caption_path):
    with open(caption_path, 'r') as f:
        captions = f.readlines()[1:]
    captions = [caption.lower().strip() for caption in captions]
    caption_map = {}
    for line in captions:
        img_id, caption = line.split(",", 1)
        caption = f"<startseq> {clean_text(caption)} <endseq>"
        caption_map.setdefault(img_id, []).append(caption)
    return caption_map 

def fit_tokenizer(caption_map):
    all_captions = [c for captions in caption_map.values() for c in captions]
    tokenizer = Tokenizer(oov_token="<unk>")
    tokenizer.fit_on_texts(all_captions)
    return tokenizer

def load_and_preprocess_image(image_path, target_size=(299, 299)):
    image = load_img(image_path, target_size=target_size)
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = preprocess_input(image)
    return image

def prepare_dataset(feature_path, caption_path):
    # Load pre-extracted image features
    with open(feature_path, 'rb') as f:
        image_features = pickle.load(f)

    # Load captions and build tokenizer
    caption_map = load_captions(caption_path)
    tokenizer = fit_tokenizer(caption_map)

    img_ids = list(caption_map.keys())
    features = []
    caption_seqs = []

    for img_id in img_ids:
        if img_id not in image_features:
            continue
        feature = image_features[img_id]
        captions = caption_map[img_id]

        for cap in captions:
            seq = tokenizer.texts_to_sequences([cap])[0]
            caption_seqs.append(seq)
            features.append(feature)  # No duplication of large image data

    # Pad caption sequences
    caption_seqs = pad_sequences(caption_seqs, padding='post')
    features = np.array(features)

    return features, caption_seqs, tokenizer


