import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", api_version="v1beta", max_retries=2)


#response = model.invoke("tell me something about sun in 2 sentences")
#print(response.content)
