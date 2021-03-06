# Import Necessary Libraries
import os
import re

import json
import pandas as pd
import numpy as np
from sklearn import metrics

# Global Variables
attributeDictionary = {
    "Document Name": "DN",
    "Parties": "P",
    "Agreement Date": "AD",
    "Expiration Date": "ED",
    "Governing Law": "GL",
    "No-Solicit Of Employees": "NS",
    "Anti-Assignment": "AA",
    "License Grant": "LG",
    "Cap On Liability": "CL",
    "Insurance": "IN"
}


# FUNCTIONS

# Function to load json file and return json fle in dictionary format
# Parameters: file path to json in string format
# Return: dictionary of JSON
def load_json(path):
    with open(path, "r") as f:
        dict = json.load(f)
    return dict


# Function to get answer data from json dictionary
# Parameters: json in dictionary form
# Return: Returns
def get_answers(test_json_dict):
    results = {}
    ner_list = ["Document Name", "Parties", "Agreement Date", "Expiration Date", "Governing Law",
                "No-Solicit Of Employees", "Anti-Assignment", "License Grant", "Cap On Liability", "Insurance"]
    data = test_json_dict["data"]
    for contract_num, contract in enumerate(data):
        title = contract["title"]
        new_ner_list = []
        for ner in ner_list:
            title_appended = title + "__" + ner
            new_ner_list.append(title_appended)
        for para in contract["paragraphs"]:
            qas = para["qas"]
            for qa in qas:
                id = qa["id"]
                if id in new_ner_list:
                    answers = qa["answers"]
                    final_format = []
                    for i in range(len(answers)):
                        ans = [answers[i]["text"], answers[i]["answer_start"]]
                        final_format.append(ans)
                    results[id] = final_format
    return results


# Function to get all the titles as a list
# Parameters: json in dictionary form
# Return: titles as a list
def get_titles(test_json_dict):
    data = test_json_dict["data"]
    titles = []
    for contract in data:
        title = contract['title']
        titles.append(title)
    return titles


# Function to get all contexts
# Parameters:  json in dictionary form
# Return: dictionary with key value as title of contract and value being the context
def get_contexts(test_json_dict):
    results = {}
    data = test_json_dict['data']
    for contract in data:
        title = contract['title']
        for para in contract["paragraphs"]:
            results[title] = para["context"]
    return results


# Function to a list of sentances
# Parameters: context as string
# Return: list of sentences split by blank space
def get_sentences(context):
    lines = context.splitlines()
    lines = [x for x in lines if x]
    sentence_word_split = []
    for sentence in lines:
        sentence_word_split.append(sentence.split())
    return sentence_word_split


# Function to get all of the ids and answers associated with a certain document
# Parameters: the answers dictionary resulting from get_answers(), title of document you want information for
# Return: dictionary of answers and ids associated with a certain document, key is id, value is answers
def get_title_answers(answers, title):
    title_ans = []
    for key in answers.keys():
        if title in key:
            title_ans.append(key)
    temp_dict = {}
    for id in title_ans:
        temp_dict[id] = answers[id]
    return temp_dict


# Function to get all the words in a document with detailed context information Parameters: context as string Return:
# list of all words in a document with start index, end index, and a filler BIO-ANNOTATED label 'O' to be updated later
def split_context_w_indexes(context_text):
    words = []
    my_context = context_text + ' '
    index = 0
    word = ''
    starting_index = 0
    ending_index = 0
    while len(my_context) > index:
        if index == 0:
            word = word + my_context[index]
            starting_index = 0
            index = index + 1
        else:
            cur_char = my_context[index]
            if len(word) == 0:
                if cur_char == ' ' or cur_char == '\n':
                    index = index + 1
                elif cur_char != ' ':
                    word = word + cur_char
                    starting_index = index
                    index = index + 1
            else:
                if cur_char == ' ' or cur_char == '\n':
                    ending_index = index
                    words.append([word, starting_index, ending_index, 'O'])
                    word = ''
                    index = index + 1
                elif cur_char != ' ':
                    word = word + cur_char
                    index = index + 1
    return words


# Function to get all answers assocaited with a title
# Parameters: result from get_title_answers()
# Return: list of answers in format [answer text, start index, end index, BIO-ANNOTATED TAG]
def get_title_ans_list_bio_anno(title_ans, answers):
    full_ans_list = []
    for title_id in title_ans:
        id_split = title_id.split('__')
        id_answers = answers[title_id]
        for ans in id_answers:
            full_ans_list.append([ans[0], ans[1], ans[1] + len(ans[0]), attributeDictionary[id_split[1]]])
    return full_ans_list


def mark_sentence(entity_list, text_list):
    word_list = []
    for word, start_, end_, t in text_list:
        match = False
        for text, start, end, tag in entity_list:
            if start_ == start:
                temp = (word, start_, end_, 'B-' + tag)
                word_list.append(temp)
                match = True
            elif (start_ > start) & (start_ <= end):
                temp = (word, start_, end_, 'I-' + tag)
                word_list.append(temp)
                match = True
                if end_ == end:
                    try:
                        entity_list.remove((text, start, end, tag))
                        print("rm")
                    except ValueError:
                        print("")
                break
        # print(word_list)
        if not match:
            temp = (word, start_, end_, '0')
            word_list.append(temp)

    return word_list


def main():
    cuad_json = load_json("json/CUAD_v1.json")
    titles = get_titles(cuad_json)
    answers = get_answers(cuad_json)
    contexts = get_contexts(cuad_json)

    # for ans in answers:
        # print(titles)

    # LIMEENERGYCO_09_09_1999-EX-10-DISTRIBUTOR AGREEMENT
    # [['DISTRIBUTOR AGREEMENT', 44]]
    title_index = 0
    for title in titles:
        my_context = contexts[title]
        # print(my_context[0:105])
        print(title)
        ex = split_context_w_indexes(my_context)
        # print(ex)
        title_ans = get_title_answers(answers, title)

        # print(title_ans)

        full_list = get_title_ans_list_bio_anno(title_ans, answers)
        # for l in full_list:
            # print(l)

        word_list = mark_sentence(full_list, ex)
        # for word in word_list:
            # print(word)

        # output something
        f = open("train/" + title + "_train.txt", "w", encoding="utf-8")
        itr = 0
        # get indexes where theres a period in order to create a newline for each  sentence
        for word in word_list:
            f.write(word_list[itr][0] + " " + word_list[itr][3] + "\n")
            if "." in word_list[itr][0]:
                if '.' == word_list[itr][0][-1]:
                    f.write("\n")
            itr += 1


if __name__ == '__main__':
    main()
