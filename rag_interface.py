from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
import torch
from llama_index.prompts.prompts import SimpleInputPrompt
from llama_index.llms import HuggingFaceLLM
from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import set_global_service_context
from llama_index import ServiceContext
from llama_index import VectorStoreIndex, download_loader
from pathlib import Path
from llama_index import VectorStoreIndex,SimpleDirectoryReader,ServiceContext
import gradio as gr
import re

def remove_last_incomplete_sentence(text):
    # Use regular expressions to find the last incomplete sentence
    sentence_pattern = r'[^.!?]*[.!?]'
    match = re.search(sentence_pattern, text[::-1])
    
    if match:
        last_incomplete_sentence_end = len(text) - match.end()
        # Remove the last incomplete sentence
        modified_text = text[:last_incomplete_sentence_end]
    else:
        # No incomplete sentence found, return the original text
        modified_text = text

    return modified_text

# Define variable to hold llama2 weights naming 
name = "sharpbai/Llama-2-7b-chat"
# Set auth token variable from hugging face 
auth_token = ""


# Create a system prompt 
system_prompt = """<s>[INST] <<SYS>>
You are a Customer Support Agent for Yulu a Microbility company.Help Cusotmers regarding their queries in polite manner.
Don't cut the answer abrublty, give answer in complete sentences. 
If a question does not make any sense, or is not factually coherent,explain why instead of answering something not correct. 
A single Yulu ride cost of Yulu Mircale in Bangalore cost Rs 5 (base fare) + 2.5 rupees per minute. In cities other than Bangalore it costs Rs 10(base fare) + 2.5 rupees per minute.
If you do not know the answer to a question, please do not share false information. <</SYS>>
"""

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
                    max_new_tokens=200,
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
documents = SimpleDirectoryReader('/home/chats/LLM-A/data/YuluGyan').load_data()
#documents = loader.load(file_path=Path('./data/annualreport.pdf'), metadata=True)

# Create an index - we'll be able to query this in a sec
index = VectorStoreIndex.from_documents(documents)
# Setup index query engine using LLM 
query_engine = index.as_query_engine()

index = None
def generate_text(prompt = "What all products yulu have?"):
    response = query_engine.query(prompt)
    return response.response



def chat(chat_history, user_input):
  bot_response = query_engine.query(user_input)
  bot_response = remove_last_incomplete_sentence(bot_response.response)+'.'
  #print(bot_response)
  response = ""
  for letter in ''.join(bot_response): #[bot_response[i:i+1] for i in range(0, len(bot_response), 1)]:
      response += letter + ""
      yield chat_history + [(user_input, response)]
     
with gr.Blocks() as demo:
    gr.Markdown('# YULU Chat Bot')
    with gr.Tab("YuluGyan"):
#          inputbox = gr.Textbox("Input your text to build a Q&A Bot here.....")
          chatbot = gr.Chatbot()
          message = gr.Textbox ("How to cancel my booking and get a refund?")
          message.submit(chat, [chatbot, message], chatbot)

demo.queue().launch(share= True)

demo.queue().close()




























