# GPT Document Extraction

This is a proof-of-concept for using ChatGPT to extract structured data from messy text documents like scanned/OCR'd PDFs and difficult forms.

It works by asking ChatGPT to turn text documents (found in an input JSON file or a text file) into a JSON record that matches a given JSON Schema specification.

If your input data is a text file where each line is a document, you can use the script like this:

```
./gpt-extract.py --input-type text infile.txt schema.json output.json
```

This would extract each line in infile, using schema.json and write extracted data to output.json. You can find an example JSON schema down below in the "JSON schema file" section.

If your input data is JSON, you'll need to tell the script how to find the documents (and, optionally how to find a unique ID for each recod). The only kind of supported JSON is a list of JSON objects. Your JSON input data should look something like this:

```
[{
  "id": 1
  "doc": "My text here..."
}, {
  "id": 2,
  "doc": "Another record..."
}]
```

You can run the script like this:

```
./gpt-extract.py --input-type json --keydoc doc --keyid id infile.json schema.json output.json
```

Note that the output file (`output.json`), if it exists, needs to be valid JSON (not a blank file) as the script will attempt to load it and continue where the extraction left off.

## Setup

This repo depends on [ChatGPT-wrapper][wrapper-main], which is included as a submodule of this repo. Clone this repo like:

```
git clone --recurse-submodules https://github.com/brandonrobertz/chatgpt-document-extraction
cd chatgpt-document-extraction
```

If you've already cloned the repo you can get and/or update the submodule with this:

```
git submodule update --init --recursive
```

Then install ChatGPT-wrapper and [set up Playwright][playwright-setup]:

```
cd chatgpt-wrapper/
pip install .
cd ..
playwright install
```

You need to login, so run the following command and log into ChatGPT:

```
chatgpt install
```

## Extraction

Once you're set up, you can extract structured data, 

```
./gpt-extract.py --headless --input-type infile.txt schema.json output.json
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

[playwright-setup]: https://playwright.dev/python/docs/library
    "Playwright - Getting Started"
