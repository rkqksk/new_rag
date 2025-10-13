import anthropic
import os
from dotenv import load_dotenv

load_dotenv(".env")
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

task = "say hi~!라고 한국어와 일본어, 영어로 말해줘."
message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": task}]
)

with open("report_agent.md", "w", encoding="utf-8") as f:
    if isinstance(message.content, list):
        full_text = "\n".join(block.text if hasattr(block, "text") else str(block) for block in message.content)
    else:
        full_text = str(message.content)
    f.write(full_text)
print("결과가 report_agent.md에 저장되었습니다.")

