from uuid import uuid4
from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage
from models import model
from tools import calculate_right_refund, get_user_purchase_history, issue_refund_ticket
from prompts import agent_system_prompt
from objects import Answer

load_dotenv()

agent = create_agent(
    model=model,
    system_prompt=agent_system_prompt,
    tools=[get_user_purchase_history, calculate_right_refund, issue_refund_ticket],
    response_format=Answer,
    checkpointer=InMemorySaver()
)

def run_conversation():
    config = {"configurable": {"thread_id": str(uuid4())}}
    question = HumanMessage(content="I would like to request a refund")
    print(question.content)

    while True:
        response = agent.invoke({"messages": question}, config=config)
        structured_response = response["structured_response"]
        print(structured_response.answer)

        if not structured_response.conversation:
            break

        question = HumanMessage(content=input("reply: \n"))

    print("\nthe job is done!")

if __name__ == "__main__":
    run_conversation()
