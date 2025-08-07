# memory.py

# In-memory session memory store
session_memory = {}

def add_to_memory(session_id, role, content):
    if session_id not in session_memory:
        session_memory[session_id] = []
    session_memory[session_id].append({"role": role, "content": content})

def get_memory(session_id):
    return session_memory.get(session_id, [])

def clear_memory(session_id):
    if session_id in session_memory:
        del session_memory[session_id]
