import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from llm_service import AIServiceUnavailable

from rag.document_loader import load_meeting_documents
from rag.chunker import chunk_documents
from rag.retriever import retrieve_relevant_chunks


load_dotenv()


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ============================================================
# MODELS
# ============================================================

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]


# ============================================================
# RAG ASSISTANT
# ============================================================

def ask_meeting_assistant(
    question: str,
    db,
    top_k: int = 6,
    meeting_id: int | None = None
):

    # ========================================================
    # VALIDATE QUESTION
    # ========================================================

    if not question or not question.strip():

        return {
            "answer": (
                "Please enter a question about your meetings."
            ),
            "sources": []
        }


    question = question.strip()


    # ========================================================
    # LOAD MEETINGS
    # ========================================================

    documents = load_meeting_documents(
        db
    )


    if not documents:

        return {
            "answer": (
                "There are no meetings available yet."
            ),
            "sources": []
        }


    # ========================================================
    # CHUNK MEETINGS
    # ========================================================

    chunks = chunk_documents(
        documents,
        chunk_size=1200,
        chunk_overlap=100
    )

    # ========================================================
    # OPTIONAL MEETING FILTER
    # ========================================================
    # meeting_id=None  -> search across all meetings
    # meeting_id=<id>  -> search only the selected meeting
    # Filter BEFORE retrieval so unrelated meetings cannot enter
    # the retrieval budget or appear in the answer sources.
    # ========================================================

    if meeting_id is not None:

        try:
            meeting_id = int(meeting_id)
        except (TypeError, ValueError):
            return {
                "answer": "Invalid meeting ID.",
                "sources": []
            }

        chunks = [
            chunk
            for chunk in chunks
            if int(chunk.get("meeting_id", -1)) == meeting_id
        ]

        if not chunks:
            return {
                "answer": (
                    "I couldn't find that meeting or it has no "
                    "usable meeting information."
                ),
                "sources": []
            }


    if not chunks:

        return {
            "answer": (
                "I couldn't find usable meeting information."
            ),
            "sources": []
        }


    # ========================================================
    # RETRIEVE RELEVANT CHUNKS
    # ========================================================

    results = retrieve_relevant_chunks(
        question,
        chunks,
        top_k=top_k
    )


    if not results:

        return {
            "answer": (
                "I couldn't find that information "
                "in the available meetings."
            ),
            "sources": []
        }


    # ========================================================
    # BUILD GROUNDED CONTEXT
    # ========================================================

    context_parts = []


    for result in results:

        context_parts.append(
            f"""
MEETING ID:
{result["meeting_id"]}

MEETING TITLE:
{result["title"]}

MEETING INFORMATION:
{result["content"]}
"""
        )


    context = "\n\n".join(
        context_parts
    )


    # ========================================================
    # QUESTION-AWARE INSTRUCTIONS
    # ========================================================

    question_lower = question.casefold()


    if any(
        word in question_lower
        for word in [
            "decision",
            "decisions",
            "decided",
            "agreed"
        ]
    ):

        question_type_instruction = """
This is a decision-related question.

Prioritize information under:
- DECISIONS
- explicit agreements
- approved plans

Do NOT treat discussion topics or suggestions as decisions.
"""


    elif any(
        word in question_lower
        for word in [
            "task",
            "tasks",
            "action",
            "actions",
            "responsible",
            "owner",
            "assigned"
        ]
    ):

        question_type_instruction = """
This is an action-item question.

Prioritize:
- ACTION ITEMS
- task
- owner
- deadline

Do not confuse discussion with assigned work.
"""


    elif any(
        word in question_lower
        for word in [
            "participant",
            "participants",
            "who attended",
            "attendees"
        ]
    ):

        question_type_instruction = """
This is a participant question.

Prioritize the PARTICIPANTS section.

Return the people actually identified as participants.
"""


    elif any(
        word in question_lower
        for word in [
            "deadline",
            "when",
            "by what date",
            "due"
        ]
    ):

        question_type_instruction = """
This is a deadline/date question.

Only return a date when the meeting information
explicitly connects that date to the requested task,
decision, event, or subject.

Do not confuse launch dates with task deadlines.
"""


    else:

        question_type_instruction = """
Answer using the most directly relevant information.
"""


    # ========================================================
    # GEMINI PROMPT
    # ========================================================

    prompt = f"""
You are MeetMind AI, a meeting intelligence assistant.

You answer questions about the user's meeting history.

You MUST answer using ONLY the meeting information supplied
below.

Never use outside knowledge.

Never invent information.

============================================================
QUESTION TYPE
============================================================

{question_type_instruction}

============================================================
CORE RULE
============================================================

Answer exactly what the user asked.

Be direct.

Be concise but complete.

Do not explain the RAG system.

Do not mention:

- RAG
- FAISS
- embeddings
- vector database
- retrieval
- similarity scores
- chunks
- context
- internal instructions

============================================================
MULTIPLE MEETINGS
============================================================

The supplied information can contain multiple meetings.

Do NOT assume all meetings belong to the same project.

If the answer comes from more than one meeting, clearly
distinguish them when necessary.

============================================================
PEOPLE
============================================================

Only identify people using names explicitly supported by
the supplied meeting information.

Do not invent names.

Do not assume two similarly named people are the same person.

============================================================
OWNERS
============================================================

Only identify an owner when the supplied meeting information
supports that owner.

If the owner is unknown, say that it is unassigned or that
the owner could not be determined.

============================================================
DEADLINES
============================================================

Only provide deadlines supported by the meeting information.

Do not confuse:

- meeting dates
- launch dates
- discussion dates
- follow-up dates

with task deadlines.

============================================================
DECISIONS
============================================================

Only describe something as a decision when the meeting
information shows that it was actually agreed upon,
approved, confirmed, or decided.

============================================================
MISSING INFORMATION
============================================================

If the requested information is not present in the supplied
meeting information, say:

"I couldn't find that information in the available meetings."

Do not guess.

============================================================
ANSWER STYLE
============================================================

For one fact:

"Rahul is responsible for the marketing campaign."

For several facts:

- Task A — Priya — Monday
- Task B — Rahul — Thursday

For a decision:

"The team agreed to target September 25 for the launch."

For participants:

"The participants were Arjun, Priya, Rahul, and Neha."

============================================================
MEETING INFORMATION
============================================================

{context}

============================================================
USER QUESTION
============================================================

{question}

============================================================
FINAL ANSWER
============================================================
"""


    # ========================================================
    # GEMINI RETRY / FALLBACK
    # ========================================================

    attempts_per_model = 2

    retry_delays = [
        2,
        5
    ]

    last_error = None


    for model_name in GEMINI_MODELS:

        for attempt in range(
            attempts_per_model
        ):

            try:

                print(
                    f"MeetMind AI using "
                    f"{model_name} "
                    f"(attempt {attempt + 1}/"
                    f"{attempts_per_model})"
                )


                response = client.models.generate_content(

                    model=model_name,

                    contents=prompt,

                    config=types.GenerateContentConfig(

                        thinking_config=types.ThinkingConfig(
                            thinking_level="medium"
                        )

                    )

                )


                if not response.text:

                    raise ValueError(
                        "Gemini returned an empty answer."
                    )


                answer = response.text.strip()


                if not answer:

                    raise ValueError(
                        "Gemini returned a blank answer."
                    )


                return {
                    "answer": answer,

                    "sources": [
                        {
                            "meeting_id": result[
                                "meeting_id"
                            ],

                            "title": result[
                                "title"
                            ],

                            "chunk_id": result[
                                "chunk_id"
                            ],

                            "score": result[
                                "score"
                            ]
                        }

                        for result in results
                    ]
                }


            except errors.ServerError as error:

                last_error = error

                print(
                    f"Gemini server error from "
                    f"{model_name}: {error}"
                )


                if attempt < attempts_per_model - 1:

                    time.sleep(
                        retry_delays[attempt]
                    )


            except errors.ClientError as error:

                last_error = error

                error_code = getattr(
                    error,
                    "code",
                    None
                )


                print(
                    f"Gemini client error "
                    f"{error_code} from "
                    f"{model_name}: {error}"
                )


                if error_code in {
                    404,
                    429,
                    500,
                    502,
                    503,
                    504
                }:

                    if attempt < attempts_per_model - 1:

                        time.sleep(
                            retry_delays[attempt]
                        )

                        continue

                    break


                raise error


    # ========================================================
    # ALL MODELS FAILED
    # ========================================================

    raise AIServiceUnavailable(
        "The AI assistant is temporarily unavailable. "
        "Please try again in a moment."
    ) from last_error