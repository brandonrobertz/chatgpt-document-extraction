# GPT Document Extraction

This is a proof-of-concept for using ChatGPT to extract structured data from messy text documents like scanned/OCR'd PDFs and difficult forms.

It works by asking ChatGPT to turn text documents (found in an input JSON file or a text file) into a JSON record that matches a given JSON Schema specification.

```
./gpt-extract.py --input-type infile.txt schema.json output.json
```

Would extract each line in infile, using schema.json and write extracted data to output.json.

## Setup

This repo depends on a [forked][wrapper-fork] version of [ChatGPT-wrapper][wrapper-main], which is included as a submodule of this repo:

```
git clone --recurse-submodules https://github.com/brandonrobertz/chatgpt-document-extraction
cd chatgpt-document-extraction
```

If you've already cloned the repo you can get and/or update the submodule with this:

```
git submodule update --init --recursive
```

Then install ChatGPT-wrapper:

```
cd chatgpt-wrapper/
pip install .
cd ..
```

You need to login, so run the script for the first time *without* `--headless`. Subsequent runs will keep track of your logged in session, so you can use `--headless` after logging in.

## Extraction

Once you're set up, you can extract structured data, 

```
./gpt-extract.py --input-type infile.txt schema.json output.json
```

### Input data spec

You can provide one of two options:

1. text file, with one record per row (`--input-type txt`)
2. a JSON file with an array of objects (`--input-type json`). You can specify which keys to use with the `--keydoc` and `--keyid` options which tell the script how to find the document text and the record ID.

### JSON schema file

You need to provide a JSON Schema file that will instruct ChatGPT how to transform the input text. Here's an example that I used:

```
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name of person this document is from": {
      "type": "string"
    },
    "name of person this document is written to": {
      "type": "string"
    },
    "name of person this document is about": {
      "type": "string"
    },
    "violation": {
      "type": "string"
    },
    "outcome": {
      "type": "string"
    },
    "date": {
      "type": "string"
    },
    "summary": {
      "type": "string"
    }
  }
}
```

It can be helpful to name the fields in descriptive ways that ChatGPT can use to figure out what to extract.


[wrapper-main]: https://github.com/mmabrouk/chatgpt-wrapper
    "ChatGPT Wrapper - upstream version"

[wrapper-fork]: https://github.com/brandonrobertz/chatgpt-wrapper
    "ChatGPT Wrapper - forked version with modifications"
