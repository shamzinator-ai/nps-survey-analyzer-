"""Agent feedback pipeline using RAG with knowledge base and vision."""

from __future__ import annotations

from typing import List
import openai

import kb
import vision


class AgentPipeline:
    """Simple pipeline for a single feedback agent."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    def _kb_context(self, query: str) -> str:
        chunks = kb.search(self.agent_name, query)
        return "\n".join(chunks)

    def run_feedback(self, text_blocks: List[str], images: List[vision.Image.Image]) -> str:
        """Combine KB search with user content and call OpenAI."""
        user_text = "\n".join(text_blocks)
        kb_ctx = self._kb_context(user_text)
        prompt = (
            f"You are the {self.agent_name} expert. "
            "Provide concise feedback."
        )
        # UPDATED: combine KB context and user text
        messages = [
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text + "\n" + kb_ctx}
                ],
            },
        ]
        for img in images:
            messages[1]["content"].append(
                {"type": "image_url", "image_url": vision.image_to_data_uri(img)}
            )
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content.strip()

