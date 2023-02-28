#!/usr/bin/env python
"""
Generic ChatGPT extraction script. Converts any input data to
any output JSON, as specified by a given JSON schema document.

This is dependent on the ChatGPT wrapper library:

https://github.com/mmabrouk/chatgpt-wrapper

Make sure to also run playwright install before running
this extractor script!
"""
import argparse
from datetime import datetime
import json
import os
import re
import sys
import time

from chatgpt_wrapper import ChatGPT


# max chars to use in prompt
DOC_MAX_LENGTH=3000


parser = argparse.ArgumentParser(description='Extract structured data from text using ChatGPT.')
parser.add_argument(
    '--input-type', 
    choices=['txt', 'json'],
    help='Input file type: txt (one doc per line) or json (list of objects, add document key path using --dockey)'
)
parser.add_argument(
    '--keydoc', 
    help='If using JSON input type, this is the key of the document'
)
parser.add_argument(
    '--keyid', 
    help='If using JSON input type, this is the key of the id/page no'
)
parser.add_argument(
    '--headless', 
    action='store_true',
    help='Hide the browser'
)
parser.add_argument(
    '--login', 
    action='store_true',
    help='Wait for us to login manually. You need to run this the first time'
)
parser.add_argument(
    '--continue-at',
    help='Continue extration at this document index'
)
parser.add_argument(
    '--continue-last',
    action='store_true',
    help='Continue extration at the last document extracted'
)
parser.add_argument(
    '--browser',
    default="firefox",
    help='Choose a browser to use. Needs to already be installed with `playwright install`. Defaults to firefox.'
)
parser.add_argument(
    'infile',
    help='Input file'
)
parser.add_argument(
    'schema_file',
    help='Path to JSON Schema file'
)
parser.add_argument(
    'outfile',
    help='Path to output results JSON file'
)



def clean_document(page_text):
    # cleaned = re.sub("[\n]+", "\n", re.sub("[ \t]+", " ", page_text)).strip()
    cleaned = re.sub(r"[\t ]+", " ", re.sub(r"[\n]+", "\n", page_text)).strip()
    if len(cleaned) < DOC_MAX_LENGTH:
        return cleaned
    front = cleaned[:DOC_MAX_LENGTH - 500]
    end = cleaned[-500:]
    return f"{front} {end}"


def scrape_via_prompt(chat, page_text, schema):
    prompt = f"```{clean_document(page_text)}```\n\nFor the given text, can you provide a JSON representation that strictly follows this schema:\n\n```{schema}```"

    print("Entering prompt", len(prompt), "bytes")
    response = None
    # increasing this increases the wait time
    waited = 0
    # use this prompt so we can change it ("can you continue the
    # previous..") but keep track of the original prompt
    current_prompt = prompt
    while True:
        response = chat.ask(current_prompt)

        if waited == 0:
            print(f"{'='*70}\nPrompt\n{'-'*70}\n{current_prompt}")
            print(f"{'='*70}\nResponse\n{'-'*70}\n{response}")

        waited += 1

        if waited > 5:
            print("Timed out on this prompt")
            break

        if "unusable response produced by chatgpt" in response.lower():
            wait_seconds = 120 * waited
            print("Bad response! Waiting longer for", wait_seconds, "seconds")
            time.sleep(wait_seconds)
            continue

        bad_input = (
            "it is not possible to generate a json representation "
            "of the provided text"
        )

        if bad_input in response.lower():
            response = None
            print("Bad input! Skipping this text")
            continue

        if response.strip() == "HTTP Error 429: Too many requests":
            # sleep for one hour
            print("Sleeping for one hour due to rate limiting...")
            time.sleep(60 * 60)
            continue

        if "}" not in response:
            # retry the session if it's not completing the JSON
            print("Broken JSON response, skipping for now")
            break

        # we have a good response here
        break

    if response is None:
        print("Skipping page due to blank response")

    return prompt, response


def upsert_result(results, result):
    pk = result["id"]
    for r_ix, r_result in enumerate(results):
        if r_result["id"] != pk:
            continue
        # overwrite
        results[r_ix] = result
        return
    # if we're here we did't update an existing result
    results.append(result)


def run(documents, schema, outfile, headless=False, login=False,
        continue_at=None, continue_last=False, browser=None):
    print("Starting ChatGPT interface...")
    chat = ChatGPT(headless=headless, browser=browser)
    if login:
        input("Login then press enter...")
        pass
    else:
       time.sleep(5)

    # TODO: Check for login prompt
    # TODO: Optionally clear all prev sessions

    results = []
    if os.path.exists(outfile):
        with open(outfile, "r") as f:
            results = json.load(f)

    already_scraped = set([
        r.get("id") for r in results
    ])
    if already_scraped:
        print("Already scraped", already_scraped)

    if continue_last:
        continue_at = max(list(already_scraped)) + 1
        print("Continuing at", continue_at)

    print(len(documents), "documents to scrape")

    # flag so that we only sleep after the first try
    first_scrape = True
    for p_ix, page_data in enumerate(documents):
        pk = page_data["id"]
        page_text = page_data["text"]
        if not page_text:
            print("Blank text for ID:", pk, "Skipping...")
            continue

        print("Doc ID:", pk, "Text length:", len(page_text))

        if continue_at is not None and pk < continue_at:
            continue

        if not first_scrape:
            print("Sleeping for rate limiting")
            time.sleep(60)
            first_scrape = False

        prompt, response = scrape_via_prompt(chat, page_text, schema)

        data = None
        try:
            data = json.loads(response.split("```")[1])
        except Exception as e:
            print("Bad result on ID", pk)
            print("Parse error:", e)
            continue

        result = {
            "id": pk,
            "text": page_text,
            "prompt": prompt,
            "response": response,
            "data": data,
        }
        upsert_result(results, result)

        print("Saving results to", outfile)
        with open(outfile, "w") as f:
            f.write(json.dumps(results, indent=2))
        print("ID", pk, "complete")


def parse_input_documents(args):
    documents = []
    with open(args.infile, "r") as f:
        if args.input_type == "txt":
            for i, doc in enumerate(f.readlines()):
                documents.append({
                    "id": i, 
                    "text": doc
                })
        elif args.input_type == "json":
            with open(args.infile, "r") as f:
                input_json = json.load(f)
            type_err_msg = "Input JSON must be an array of objects"
            assert args.keydoc, "--keydoc required with JSON input type"
            # assert args.keyid, "--keyid required with JSON input type"
            assert isinstance(input_json, list), type_err_msg
            assert isinstance(input_json[0], dict), type_err_msg
            assert args.keydoc in input_json[0], f"'{args.keydoc}' not in JSON"
            # assert args.keyid in input_json[0], f"'{args.keyid}' not in JSON"
            for ix, doc_data in enumerate(input_json):
                documents.append({
                    "id": doc_data[args.keyid] if args.keyid else ix,
                    "text": doc_data[args.keydoc]
                })
    return documents


if __name__ == "__main__":
    args = parser.parse_args()

    documents = parse_input_documents(args)

    with open(args.schema_file, "r") as f:
        schema = json.load(f)


    assert not (args.continue_last and args.continue_at), \
        "--continue-at and --continue-last can't be used together"

    run(documents, schema, args.outfile,
        headless=args.headless,
        continue_at=args.continue_at,
        continue_last=args.continue_last,
        browser=args.browser,
    )
