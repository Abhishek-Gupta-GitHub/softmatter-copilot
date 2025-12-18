import json
from textwrap import dedent

class ChatExplainer:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def build_prompt(self, user_question: str, summary: dict) -> str:
        return dedent(f"""
        You are a soft-matter postdoc helping with confocal particle tracking.

        The user asked:
        \"\"\"{user_question}\"\"\".

        Here is a JSON summary of the analysis:
        \"\"\"{json.dumps(summary, indent=2)}\"\"\".

        Task:
        - Explain MSD, alpha, and D in 1–2 paragraphs.
        - Comment on depth, bleaching, and crowding diagnostics.
        - Give 3 concrete next-experiment suggestions.
        - Do not invent numbers; only use values present in the JSON.

        Answer in clear, technical prose.
        """)

    def call_llm(self, prompt: str) -> str:
        if self.llm is None:
            return (
                "MSD and the fitted alpha parameter indicate the overall diffusive "
                "behaviour under your current imaging conditions. Depth and bleaching "
                "diagnostics highlight where intensity and track quality degrade.\n\n"
                "Next experiments: (1) Restrict analysis to the depth range with "
                "stable intensity, (2) lower laser power or shorten acquisition to "
                "reduce bleaching, (3) adjust particle density or magnification to "
                "mitigate crowding and improve tracking."
            )
        return self.llm.complete(prompt)

    def explain(self, user_question: str, summary: dict) -> str:
        prompt = self.build_prompt(user_question, summary)
        return self.call_llm(prompt)

