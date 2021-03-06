"""
*******************************************************
 * Copyright (C) 2017 MindsDB Inc. <copyright@mindsdb.com>
 *
 * This file is part of MindsDB Server.
 *
 * MindsDB Server can not be copied and/or distributed without the express
 * permission of MindsDB Inc
 *******************************************************
"""

from mindsdb_native.libs.constants.mindsdb import *
from collections import Counter, defaultdict
import string
import json
import hashlib
import numpy
import flair
import langdetect
langdetect.DetectorFactory.seed = 0


def get_language_dist(data):
    lang_dist = defaultdict(lambda: 0)
    lang_dist['Unknown'] = 0
    lang_probs_cache = dict()
    for text in data:
        if text not in lang_probs_cache:
            try:
                lang_probs = langdetect.detect_langs(text)
            except langdetect.lang_detect_exception.LangDetectException:
                lang_probs = []
            lang_probs_cache[text] = lang_probs

        lang_probs = lang_probs_cache[text]
        if len(lang_probs) > 0 and lang_probs[0].prob > 0.90:
            lang_dist[lang_probs[0].lang] += 1
        else:
            lang_dist['Unknown'] += 1

    return dict(lang_dist)


def analyze_sentences(data):
    """
    :param data: list of str

    :returns: 
    tuple(
        int: nr words total,
        dict: word_dist,
        dict: nr_words_dist
    )
    """
    nr_words = 0
    word_dist = defaultdict(lambda: 0)
    nr_words_dist = Counter()
    for text in data:
        sent = flair.data.Sentence(str(text))
        nr_words_dist[len(sent)] += 1
        nr_words += len(sent)
        for tok in sent:
            word = tok.text.strip(string.punctuation + '"\'«»')
            word_dist[word] += 1

    return nr_words, dict(word_dist), dict(nr_words_dist)


def word_tokenize(string):
    sep_tag = '{#SEP#}'
    for separator in WORD_SEPARATORS:
        string = str(string).replace(separator, sep_tag)

    words_split = string.split(sep_tag)
    num_words = len([word for word in words_split if word and word not in ['', None]])
    return num_words


def clean_float(val):
    if isinstance(val, (int, float)):
        return float(val)

    if isinstance(val, numpy.float64):
        return val

    val = str(val).strip(' ')
    val = val.replace(',', '.')
    val = val.rstrip('"').lstrip('"')

    if val == '' or val == 'None' or val == 'nan':
        return None

    return float(val)


def gen_chars(length, character):
    """
    # lambda to Generates a string consisting of `length` consiting of repeating `character`
    :param length:
    :param character:
    :return:
    """
    return ''.join([character for i in range(length)])


def cast_string_to_python_type(string):
    """ Returns None, an integer, float or a string from a string"""
    try:
        if string is None or string == '':
            return None
        return int(string)
    except:
        try:
            return clean_float(string)
        except:
            return string


def splitRecursive(word, tokens):
    words = [str(word)]
    for token in tokens:
        new_split = []
        for word in words:
            new_split += word.split(token)
        words = new_split
    words = [word for word in words if word not in ['', None] ]
    return words


def hashtext(cell):
    text = json.dumps(cell)
    hash = hashlib.md5(text.encode('utf8')).hexdigest()
    return hash


def is_foreign_key(data, column_name, data_subtype, other_potential_subtypes):
    foregin_key_type = DATA_SUBTYPES.INT in other_potential_subtypes or DATA_SUBTYPES.INT == data_subtype

    data_looks_like_id = True

    if not foregin_key_type:
        prev_val_length = None
        for val in data:
            is_uuid = True
            is_same_length = True

            for char in str(val):
                if char not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                                'a', 'b', 'c', 'd', 'e', 'f', '-']:
                    is_uuid = False

            if prev_val_length is None:
                prev_val_length = len(str(val))
            elif len(str(val)) != prev_val_length:
                is_same_length = False
            else:
                prev_val_length = len(str(val))

            if not (is_uuid and is_same_length):
                data_looks_like_id = False
                break

    foreign_key_name = False
    for endings in ['-id', '_id', 'ID', 'Id']:
        if column_name.endswith(endings):
            foreign_key_name = True
    for keyword in ['account', 'uuid', 'identifier', 'user']:
        if keyword in column_name:
            foreign_key_name = True

    return foreign_key_name and (foregin_key_type or data_looks_like_id)
