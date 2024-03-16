# Requirements:
# OpenAI API key at OPENAI_API_KEY
# Polygonscan API key at POLYGON_API_KEY

from openai import OpenAI
import requests
from pathlib import Path
import time
import json
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.

client = OpenAI(
    # Defaults to os.environ.get("OPENAI_API_KEY")
)

class NelsonBot:
    assistant_id="asst_K0OmaJzsc4pFwFzyrHVPKilr"
    address = "0x257B2457b10C02d393458393515F51dc8880300d"
    wallet_thread = None
    wallet_thread_id = "thread_GFQDDGOCOl7X5YWHj30cHA6T"
    wallet_transactions = None

    def __init__(self):
        self.data = []
        self.input_address() # kick off in the constructor

    def input_address(self):
        print("===What address do you want more information about [blank for default]?===")
        input_string=input()

        self.init_wallet_thread(input_string) # create thread based on wallet
        self.input_query()

    def init_wallet_thread(self, address):
        initial_address=address
        # requests for etherscan, will use default address if falsey
        self.get_polygonscan(address)

        # re-use thread if thread default exists and using default wallet
        if self.wallet_thread_id and not initial_address:
            print("Reusing thread ",self.wallet_thread_id)
        else:
            self.wallet_thread = thread = client.beta.threads.create()
            self.wallet_thread_id = self.wallet_thread.id
            print("Created thread with wallet transactions", self.wallet_thread_id)

        # associate wallet context with initial question to thread via message
        print("Bot processing transactions")
        transactions_text = repr(self.wallet_transactions)
        message=client.beta.threads.messages.create(thread_id=self.wallet_thread_id,role="user",content="These are recent transaction data related to the specific blockchain wallet in question. Begin blockchain transactions. "+ transactions_text +" End blockchain transactions. Give me brief summary of recent transactions.")
        client.beta.threads.runs.create(assistant_id=self.assistant_id,thread_id=thread.id)

        return self.wallet_transactions

    def get_polygonscan(self, address):
        # requests for etherscan
        if not address:
            address = self.address

        # get wallet transactions
        polygonscan_url = "https://api.polygonscan.com/api?module=account&action=txlist&address="+address+"&startblock=0&endblock=99999999&page=1&offset=1000&sort=asc&apikey="+os.environ.get("POLYGON_API_KEY")
        r = requests.get(polygonscan_url)
        result_obj=r.json()
        self.wallet_transactions=result_obj["result"]

        return self.wallet_transactions

    def input_query(self):
        print("===What do you want to ask wallet bot?===")
        input_string=input()

        # send to openai
        client.beta.threads.messages.create(thread_id=self.wallet_thread_id,role="user",content=input_string)
        run=client.beta.threads.runs.create(assistant_id=self.assistant_id,thread_id=self.wallet_thread_id)
        messages = self.poll_for_finish(self.wallet_thread_id,run.id) # wait for finish
        self.print_non_user_messages(messages)

        # go back to main menu
        self.input_query()

    def print_non_user_messages(self, messages):
        message_arr=list()
        for message in messages:
            if message.role=="user":
                break
            result=message.content[0].text.value
            message_arr.append(result)
        message_arr.reverse()
        for msg in message_arr:
            print(msg)

    def poll_for_finish(self,thread_id,run_id):
        while (True):
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )

            if run_status.status == 'completed':
                return client.beta.threads.messages.list(
                    thread_id=thread_id
                ) 
            elif run_status.status in ['queued', 'in_progress']:
                print("Still waiting for run to finish")
                time.sleep(2)
            else:
                print(f"Run status: {run_status.status}")
                break


bot = NelsonBot()