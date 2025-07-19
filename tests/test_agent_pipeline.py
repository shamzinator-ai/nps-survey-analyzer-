import os
import sys
from unittest.mock import MagicMock
import openai
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agent_pipeline import AgentPipeline
import kb
import vision


def test_agent_pipeline(monkeypatch):
    monkeypatch.setattr(kb, "search", lambda a, q: ["ctx"])
    fake_img = MagicMock()
    monkeypatch.setattr(vision, "image_to_data_uri", lambda i: "data:image/png;base64,AAA=")
    resp = MagicMock()
    resp.choices = [type('O', (), {'message': type('M', (), {'content': 'ok'})()})]
    monkeypatch.setattr(openai.chat.completions, "create", lambda **kwargs: resp)
    pipeline = AgentPipeline("UX")
    result = pipeline.run_feedback(["hello"], [fake_img])
    assert result == 'ok'
