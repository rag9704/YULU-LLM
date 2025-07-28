import os
import slack_sdk
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask,request,Response,jsonify
from slackeventsapi import SlackEventAdapter
import gc
from threading import Thread


from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
import torch
from llama_index.prompts.prompts import SimpleInputPrompt
from llama_index.llms import HuggingFaceLLM
from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import VectorStoreIndex,SimpleDirectoryReader,ServiceContext,download_loader,set_global_service_context


# Create a system prompt 
system_prompt = """<s>[INST] <<SYS>>
You are a Customer Support Agent for Yulu a Microbility company.Help Cusotmers regarding their queries in polite manner.
If a question does not make any sense, or is not factually coherent,explain why instead of answering something not correct. 
A single Yulu ride cost of Yulu Mircale in Bangalore cost Rs 5 (base fare) + 2.5 rupees per minute. In cities other than Bangalore it costs Rs 10(base fare) + 2.5 rupees per minute.
If you do not know the answer to a question, please do not share false information. <</SYS>>
"""


# Define variable to hold llama2 weights naming 
name = "sharpbai/Llama-2-7b-chat"
#name = "mistralai/Mistral-7B-Instruct-v0.1"
# Set auth token variable from hugging face 
auth_token = ""


def get_tokenizer_model():
    # Create tokenizer
    tokenizer = AutoTokenizer.from_pretrained(name, cache_dir='./model/', use_auth_token=auth_token)

    # Create model
    model = AutoModelForCausalLM.from_pretrained(name, cache_dir='./model/'
                            , use_auth_token=auth_token, torch_dtype=torch.float16, 
                            rope_scaling={"type": "dynamic", "factor": 2}, load_in_8bit=True) 

    return tokenizer, model
tokenizer, model = get_tokenizer_model()

# Throw together the query wrapper
query_wrapper_prompt = SimpleInputPrompt("{query_str} [/INST]")

# Create a HF LLM using the llama index wrapper 
llm = HuggingFaceLLM(context_window=4096,
                    max_new_tokens=130,
                    generate_kwargs={"temperature": 0.0, "do_sample": False},
                    system_prompt=system_prompt,
                    query_wrapper_prompt=query_wrapper_prompt,
                    model=model,
                    tokenizer=tokenizer)

# Create and dl embeddings instance  
embeddings=LangchainEmbedding(
    HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
)

# Create new service context instance
service_context = ServiceContext.from_defaults(
    chunk_size=1024,
    llm=llm,
    embed_model=embeddings
)

# And set the service context
set_global_service_context(service_context)

# Download PDF Loader 
PyMuPDFReader = download_loader("PyMuPDFReader")
# Create PDF Loader
loader = PyMuPDFReader()
# Load documents 
documents = SimpleDirectoryReader('./data/YuluGyan').load_data()
#documents = loader.load(file_path=Path('./data/annualreport.pdf'), metadata=True)

# Create an index - we'll be able to query this in a sec
index = VectorStoreIndex.from_documents(documents)
# Setup index query engine using LLM 
query_engine = index.as_query_engine()

print("querying start -------")

#### hugging face done

env_path= Path('.')/'token.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGN_TOKEN'],'/slack/events', app)


client =slack_sdk.WebClient(token = os.environ['SLACK_TOKEN'],timeout=120)
BOT_ID = client.api_call("auth.test")['user_id']

message_counts ={}

@slack_event_adapter.on('message')
def message(payload):
    event  = payload.get('event',{})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    msg = 'write your query using {/} commands'
    
    client.chat_postMessage(channel=channel_id,text=msg)


def backgroundworker(channel_id,text):

    # your task

    payload = {"text":"your task is complete",
                "username": "bot"}
    response = query_engine.query(text)
    client.chat_postMessage(channel=channel_id,text=response.response)

    #requests.post(response_url,data=json.dumps(payload))  
@app.route('/query',methods = ['GET','POST'])
def query():
    data = request.form
    channel_id = data.get('channel_id')
    text  = data.get('text')
    

    thr = Thread(target=backgroundworker, args=[channel_id,text])
    thr.start()
    return jsonify(message= "working on your request") 



  

#client.chat_postMessage(channel='#testt',text='test ing 1')

if __name__ == "__main__":
    app.run(debug=True,port=5002,use_reloader=False)
