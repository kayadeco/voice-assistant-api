# memory.py

from collections import defaultdict

# Dictionary to hold chat history for each session
chat_memory = defaultdict(list)

def add_to_memory(session_id, role, content):
    chat_memory[session_id].append({"role": role, "content": content})

def get_memory(session_id):
    return chat_memory[session_id]

def clear_memory(session_id):
    chat_memory[session_id] = []
