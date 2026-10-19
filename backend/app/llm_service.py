import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from schemas import MeetingAnalysis


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

# Primary model + fallback models.
#
# This prevents the whole application from failing when one
# Gemini model is temporarily busy or unavailable.
#
# Gemini 3.8 Flash is currently a stable production model.
# ============================================================

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]


# ============================================================
# CUSTOM AI ERROR
# ============================================================

class AIServiceUnavailable(RuntimeError):
    """
    Raised when all configured Gemini models fail.
    """

    pass


# ============================================================
# ANALYZE TRANSCRIPT
# ============================================================

def analyze_transcript(
    transcript: str
) -> MeetingAnalysis:

    if not transcript or not transcript.strip():

        raise ValueError(
            "Transcript cannot be empty."
        )


    prompt = f"""
You are MeetMind AI, a highly accurate meeting intelligence
system.

Your task is to analyze an automatically generated meeting
transcript and return structured information.

You MUST extract:

1. Complete participant list
2. Accurate meeting summary
3. Actual decisions
4. Genuine action items
5. Correct owner for each action item
6. Correct deadline for each action item

Accuracy is more important than guessing.

============================================================
IMPORTANT: BUILD A PARTICIPANT ROSTER FIRST
============================================================

Before extracting action items or decisions, first determine
the complete set of people who actually participated in the
meeting.

Scan the ENTIRE transcript.

Look for:

- introductions
- greetings
- speaker names
- people directly addressed by name
- statements such as "I am..."
- statements such as "this is..."
- speaker labels
- people explicitly identified as members of the meeting
- people who actively speak during the meeting

A participant should normally be someone who actually
participated in the meeting.

Do NOT include someone merely because another participant
mentions that person's name.

============================================================
NAME ACCURACY
============================================================

The transcript was generated using speech recognition, so names
may contain recognition errors.

Examples:

Priya -> Preya
Rahul -> Raoul
Nora -> Norah

IMPORTANT:
Do NOT correct a name based on phonetic similarity alone.

Only canonicalize a name when the transcript itself provides
strong internal evidence that multiple spellings refer to the
same person.

When a name appears in multiple forms:

1. Find ALL occurrences of the possible name variants.
2. Compare the surrounding context of each occurrence.
3. Look for a clear, reliable occurrence of the person's name.
4. Confirm that the different forms refer to the SAME person.
5. Only then use ONE canonical spelling throughout the result.

Example:

If the transcript contains:

"Priya will finish the page"

and elsewhere:

"Preya should complete the design"

and the context clearly shows that both references are to the
same person, use:

"Priya"

However:

If the transcript contains only:

"Raha will improve the backend"

DO NOT change "Raha" to "Rahul", "Raoul", or another name merely
because it sounds similar.

If no reliable evidence supports a correction, preserve the
name as it appears in the transcript.

NEVER invent a participant's real name.

The transcript is the source of truth for names unless the
transcript itself provides strong evidence for canonicalization.

============================================================
PARTICIPANT SAFETY
============================================================

Never treat:

- ordinary words
- technical terms
- job titles
- locations
- project names
- departments
- software names

as human names.

Never convert a transcription error into a person unless
the transcript provides strong evidence.

Avoid duplicates.

If the identity of a person genuinely cannot be determined,
do not invent a name.

============================================================
OWNER EXTRACTION
============================================================

For every genuine action item, determine the responsible
person.

Use the canonical participant name from the participant roster.

Examples:

"I'll finish the API by Friday."

The speaker is the owner if the speaker identity is known.

"Priya, can you finish the page by Monday?"

Owner = Priya.

"Rahul agreed to prepare the campaign."

Owner = Rahul.

If an owner cannot be established reliably:

"owner": null

Never guess an owner.

============================================================
OWNER CONSISTENCY
============================================================

IMPORTANT:

Every non-null action-item owner MUST correspond to a person
in the participant roster unless the transcript explicitly
identifies that person as an external assignee.

Do not create a new spelling of a participant name inside
action items.

For example, if the participant roster contains:

"Priya"

do not return:

"Preya"

as an action-item owner.

============================================================
DEADLINE EXTRACTION
============================================================

Extract a deadline only when it is explicitly associated
with completing a task.

Valid examples:

- by Friday
- before Monday
- by September 25
- tomorrow
- within two days
- next Wednesday

Do NOT treat these as task deadlines unless explicitly
connected to task completion:

- meeting date
- launch date
- discussion date
- follow-up meeting date
- appointment date
- general future references

If there is no explicit deadline:

"deadline": null

============================================================
ACTION ITEM EXTRACTION
============================================================

Include ONLY genuine work someone is expected to complete.

Include:

- assigned work
- promised work
- explicitly requested work
- agreed responsibilities
- tasks with explicit ownership

Do NOT include:

- questions
- suggestions that were rejected
- general discussion
- opinions
- background information
- possible future ideas
- unresolved proposals

Keep every action item concise and specific.

============================================================
DECISION EXTRACTION
============================================================

A decision must represent something that the team actually
agreed upon, approved, selected, confirmed, or decided.

Include:

- agreed plans
- approved features
- selected dates
- accepted approaches
- explicitly confirmed decisions

Do NOT convert:

- suggestions
- questions
- possibilities
- unresolved discussions

into decisions.

============================================================
SUMMARY
============================================================

Write a concise factual summary.

Include:

- purpose of the meeting
- important discussion points
- decisions
- significant assignments
- important deadlines when relevant

Do not invent information.

============================================================
TRANSCRIPTION ERROR HANDLING
============================================================

The transcript may contain:

- spelling errors
- missing punctuation
- incorrect technical terms
- incorrect names
- broken sentences
- incorrect speaker words

Use surrounding context to understand the intended meaning.

For names specifically, do NOT silently replace a transcript
name with a different real-world name unless the transcript
contains strong internal evidence supporting that correction.

If the evidence is ambiguous:

- preserve the transcript wording
- do not guess
- do not invent a more familiar name
- use null only when a required identity cannot be established

DO NOT fabricate information.

Only correct something when the surrounding evidence strongly
supports the correction.

============================================================
FINAL VALIDATION
============================================================

Before returning the result, perform these checks:

CHECK 1:
Are all participants actual people supported by the transcript?

CHECK 2:
Are duplicate or misspelled versions of the same person merged?

CHECK 3:
Does every action-item owner match a known participant
whenever the identity is known?

CHECK 4:
Are deadlines actually task deadlines?

CHECK 5:
Are decisions actually agreed decisions?

CHECK 6:
Are action items genuine tasks?

CHECK 7:
Did you avoid inventing people, tasks, deadlines or decisions?

If evidence is insufficient, use null instead of guessing.

============================================================

MEETING TRANSCRIPT
============================================================

{transcript}
"""


    # ========================================================
    # GEMINI RETRIES
    # ========================================================

    # Each model gets up to 2 attempts.
    # If one model is temporarily unavailable, the next model
    # is attempted.
    # ========================================================

    attempts_per_model = 2

    retry_delays = [
        3,
        6
    ]


    last_error = None


    # ========================================================
    # TRY ALL MODELS
    # ========================================================

    for model_name in GEMINI_MODELS:

        for attempt in range(attempts_per_model):

            try:

                print(
                    f"Gemini analysis using "
                    f"{model_name} "
                    f"(attempt {attempt + 1}/{attempts_per_model})"
                )


                response = client.models.generate_content(

                    model=model_name,

                    contents=prompt,

                    config=types.GenerateContentConfig(

                        response_mime_type="application/json",

                        response_schema=MeetingAnalysis,

                        thinking_config=types.ThinkingConfig(
                            thinking_level="medium"
                        )

                    )

                )


                if not response.text:

                    raise ValueError(
                        "Gemini returned an empty response."
                    )


                analysis = MeetingAnalysis.model_validate_json(
                    response.text
                )


                # ====================================================
                # FINAL APPLICATION-SIDE VALIDATION
                # ====================================================

                participant_names = []

                for participant in analysis.participants:

                    name = participant.name.strip()

                    if name:

                        participant_names.append(name)


                # Remove duplicate participant names
                # while preserving order.

                unique_names = []

                seen_names = set()

                for name in participant_names:

                    key = name.casefold()

                    if key not in seen_names:

                        seen_names.add(key)

                        unique_names.append(name)


                analysis.participants = [
                    type(analysis.participants[0])(
                        name=name
                    )
                    for name in unique_names
                ] if analysis.participants else []


                # ----------------------------------------------------
                # Make sure action owners use participant names
                # when they are clearly the same person.
                #
                # We do NOT invent names here.
                # ----------------------------------------------------

                canonical_names = {
                    name.casefold(): name
                    for name in unique_names
                }


                for action in analysis.action_items:

                    if action.owner:

                        owner_key = (
                            action.owner.strip().casefold()
                        )

                        if owner_key in canonical_names:

                            action.owner = canonical_names[
                                owner_key
                            ]


                print(
                    f"Gemini analysis successful "
                    f"using {model_name}"
                )


                return analysis


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

                # 429 = rate limit
                # 404 = model unavailable
                #
                # In both cases we can try another model.

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


                # Authentication / invalid request /
                # other permanent errors should not silently
                # switch models.

                raise error


            except ValueError:

                raise


    # ========================================================
    # ALL MODELS FAILED
    # ========================================================

    print(
        "All Gemini models failed."
    )


    raise AIServiceUnavailable(
        "MeetMind AI is temporarily unavailable. "
        "All configured AI models failed. "
        "Please try again in a moment."
    ) from last_error