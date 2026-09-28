from llm_service import analyze_transcript


transcript = """
Today we discussed the AI Meeting Action Tracker project.

Lokesh will complete the backend API by Friday.

Ravi will prepare the project presentation.

The team decided to use PostgreSQL as the database.

We will review the project on Monday.
"""


result = analyze_transcript(transcript)


print("\nGEMINI ANALYSIS:")
print("\nSummary:")
print(result.summary)


print("\nDecisions:")
for decision in result.decisions:
    print("-", decision)


print("\nAction Items:")

for action in result.action_items:
    print("Task:", action.task)
    print("Owner:", action.owner)
    print("Deadline:", action.deadline)
    print()