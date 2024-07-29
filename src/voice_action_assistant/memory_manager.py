import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
import pyperclip
from pydantic import BaseModel


class Memory(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]


class MemoryManager:
    def __init__(self, persist_directory: str = "./voice_assistant_memories"):
        # Ensure the persist directory exists
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
        )

        self.collection = self.client.get_or_create_collection(
            name="memories",
        )

    def save_memory(self, memory: Memory) -> str:
        # Add the memory to the collection
        self.collection.add(
            ids=[memory.id], documents=[memory.content], metadatas=[memory.metadata]
        )

        return memory.id

    def query_memories(self, query: str, n_results: int = 20) -> List[Memory]:
        results = self.collection.query(
            query_texts=[query], n_results=n_results, include=["documents", "metadatas"]
        )

        memories = []
        for id, doc, metadata in zip(
            results["ids"][0], results["documents"][0], results["metadatas"][0]
        ):
            memories.append(Memory(id=id, content=doc, metadata=metadata))

        return memories

    def delete_memory(self, memory_id: str) -> None:
        self.collection.delete(ids=[memory_id])

    def update_memory(self, new_memory: Memory) -> None:
        self.collection.update(
            ids=[new_memory.id], documents=[new_memory.content], metadatas=[new_memory.metadata]
        )

    def get_all_memories(self) -> List[Memory]:
        results = self.collection.get(include=["documents", "metadatas"])
        return [
            Memory(id=id, content=doc, metadata=metadata)
            for id, doc, metadata in zip(
                results["ids"], results["documents"], results["metadatas"]
            )
        ]

    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        try:
            result = self.collection.get(ids=[memory_id], include=["documents", "metadatas"])
            if result["ids"]:
                return Memory(
                    id=result["ids"][0],
                    content=result["documents"][0],
                    metadata=result["metadatas"][0],
                )
        except Exception as e:
            print(f"Error retrieving memory: {e}")
        return None


class MemoryIndexManager:
    def __init__(self):
        self.current_results: list[dict] = []
        self.animal_names = [
            "Elephant",
            "Giraffe",
            "Penguin",
            "Kangaroo",
            "Dolphin",
            "Tiger",
            "Koala",
            "Panda",
            "Lion",
            "Zebra",
        ]

    def index_memories(self, memories: list[Memory]) -> None:
        self.current_results = []
        for animal_name, memory in zip(self.animal_names, memories):
            self.current_results.append(
                {"id": memory.id, "animal_name": animal_name, "content": memory.content}
            )

    def get_memory_by_animal(self, animal_name: str) -> dict:
        return next(
            (m for m in self.current_results if m["animal_name"].lower() == animal_name.lower()),
            None,
        )


def save_transcript(transcript: str, include_clipboard: bool) -> str:
    id = hashlib.md5(transcript.encode()).hexdigest()
    if include_clipboard:
        clipboard_content = pyperclip.paste()
        memory = Memory(
            id=id,
            content=f"Transcript: {transcript}\nClipboard: {clipboard_content}",
            metadata={"type": "clipboard_and_transcript", "timestamp": datetime.now().isoformat()},
        )
    else:
        memory = Memory(
            id=id,
            content=f"Transcript: {transcript}",
            metadata={"type": "clipboard_and_transcript", "timestamp": datetime.now().isoformat()},
        )

    memory_manager = MemoryManager()
    memory_id = memory_manager.save_memory(memory)
    return f"Memory saved with ID: {memory_id}"


def query_memories(query: str) -> str:
    memory_manager = MemoryManager()
    memories = memory_manager.query_memories(query)

    result = "Relevant memories:\n\n"
    for memory in memories:
        result += f"Content: {memory.content}\n"
        result += f"Metadata: {json.dumps(memory.metadata, indent=2)}\n\n"

    return result


memory_index_manager = MemoryIndexManager()

# Example usage

if __name__ == "__main__":
    # Save a memory
    transcript = "This is a test transcript"
    save_result = save_transcript(transcript, include_clipboard=True)
    print(save_result)

    # Query memories
    query_result = query_memories("test transcript")
    print(query_result)
