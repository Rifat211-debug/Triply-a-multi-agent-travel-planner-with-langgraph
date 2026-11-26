import os 
import certifi
import uuid
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage

from backend.config import get_database_url
from backend.agents import graph




load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# PostgreSQL Checkpointer
DATABASE_URL = get_database_url()

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit = True,
    row_factory = dict_row
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()

travel_graph = graph.compile(checkpointer = checkpointer)


# Function for FastAPI
def run_travel_agent(user_input: str, thread_id: str | None = None):
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"
        
    config = {
        "configurable": {"thread_id": thread_id}
    }   
    
    result = travel_graph.invoke(
        {
            "messages": [HumanMessage(content = user_input)],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config = config
    ) 
    
    final_answer = result["messages"][-1].content
    
    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }



      