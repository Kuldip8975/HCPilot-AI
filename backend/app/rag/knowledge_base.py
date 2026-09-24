"""
Knowledge base for the customer-support chat widget on the marketing
homepage.

This is written for a first-time visitor who has NO idea what this
software is or how to use it - not for a technical audience. Every chunk
answers a "how do I actually do X" or "what does this thing do" question
in plain language, the way a real product's support/help-center article
would. No internal architecture terms (agent, LLM, MCP, tech stack, etc.)
belong here - that's implementation detail, not something a confused new
user asked about.

Each entry is one retrievable "chunk": a short, self-contained piece of
text with its own title. Keeping chunks short and topically focused (one
task per chunk) is what makes retrieval work well - a giant wall of text
about everything is much harder to match accurately against a specific
question than a dozen focused, task-oriented paragraphs.
"""

from typing import Any, Dict, List

KNOWLEDGE_BASE: List[Dict[str, str]] = [
    {
        "id": "what-is-this",
        "title": "What is HcPilot AI / what does this app do",
        "text": (
            "HcPilot AI is an application (software / app / product) built for "
            "pharma and healthcare sales reps. The main idea behind this app: "
            "keep track of the doctors and specialists (HCPs) they visit, "
            "without the usual paperwork. Instead of filling long forms after "
            "every meeting, you just type or say what happened, and the app "
            "fills in the details for you automatically. It also shows you a "
            "dashboard of your activity and reminds you about follow-up "
            "visits. In short: this app helps you log visits faster and never "
            "lose track of a doctor relationship."
        ),
    },
    {
        "id": "features-overview",
        "title": "What features does HcPilot AI have",
        "text": (
            "The main features of HcPilot AI: (1) log a visit by typing or "
            "talking and let AI fill the form for you, (2) a directory to add "
            "and search doctors (HCPs), (3) automatic visit history for every "
            "doctor, (4) follow-up reminders so nothing gets missed, and (5) a "
            "dashboard summarizing your activity. These features together "
            "replace manual paperwork with a few clicks."
        ),
    },
    {
        "id": "getting-started",
        "title": "How do I get started / sign up",
        "text": (
            "Click 'Sign Up' at the top of this page, enter your name, email, "
            "and a password, and you're in - no approval wait, no setup steps. "
            "Once you're logged in, add the doctors you work with and start "
            "logging your visits."
        ),
    },
    {
        "id": "login-help",
        "title": "I can't log in / forgot my password",
        "text": (
            "Make sure you're using the same email you signed up with. If "
            "you've forgotten your password, use the 'Forgot password?' link "
            "on the login page to reset it. If you don't have an account yet, "
            "use 'Sign Up' instead - login only works after you've registered."
        ),
    },
    {
        "id": "add-hcp",
        "title": "How do I add a doctor / HCP",
        "text": (
            "Go to the HCPs page from the menu and click 'Add HCP'. Fill in "
            "their name, specialty, organization, and location, then save. "
            "They'll now show up whenever you search for them or log a visit."
        ),
    },
    {
        "id": "find-hcp",
        "title": "How do I find a doctor I already added",
        "text": (
            "Go to the HCPs page and use the search box at the top - you can "
            "search by name, specialty (e.g. 'Oncology'), or location. Click "
            "on any result to see their full profile and every visit you've "
            "logged with them."
        ),
    },
    {
        "id": "log-interaction",
        "title": "How do I log a visit / interaction",
        "text": (
            "To log a visit, go to 'Log Interaction'. You'll see a form on "
            "one side and a chat box on the other. The easiest way to log "
            "your visit: in the chat box, type what happened during the "
            "visit - for example 'Met Dr. Chen, talked about Product X, she "
            "seemed interested' - and the visit form fills itself in "
            "automatically. Check that everything about the visit looks "
            "right, then click Save to log it. You can also log a visit by "
            "filling the form by hand if you'd rather not use the chat."
        ),
    },
    {
        "id": "edit-review",
        "title": "What if the auto-filled form gets something wrong",
        "text": (
            "That's completely fine - nothing is saved until you click Save. "
            "Every field the AI fills in is a normal, editable form field, so "
            "just click into it and fix or clear whatever isn't right before "
            "saving."
        ),
    },
    {
        "id": "voice-input",
        "title": "How do I use voice / talk instead of typing",
        "text": (
            "On the Log Interaction chat box, click the microphone icon, speak "
            "naturally about the visit, and click it again to stop. Your "
            "speech is automatically converted to text and the form fills in "
            "the same way it would if you had typed it - handy right after a "
            "visit when typing is awkward."
        ),
    },
    {
        "id": "history",
        "title": "Where do I see my past visits with a doctor",
        "text": (
            "Open that doctor's profile from the HCPs page - every interaction "
            "you've ever logged with them is listed there, most recent first, "
            "with the date, what was discussed, and any notes."
        ),
    },
    {
        "id": "followups",
        "title": "How do follow-ups work",
        "text": (
            "When logging a visit, tick 'Follow-up required' and pick a date - "
            "or just tell the AI chat 'schedule a follow-up with Dr. Chen next "
            "month'. Upcoming follow-ups show up on your dashboard so you "
            "never forget one."
        ),
    },
    {
        "id": "dashboard",
        "title": "What does the dashboard show me",
        "text": (
            "Your dashboard gives you a quick summary: how many visits you've "
            "logged, how many doctors you've engaged with, how many "
            "follow-ups are due, and a chart of your activity over the past "
            "week - so you can see your workload at a glance."
        ),
    },
    {
        "id": "security",
        "title": "Is my data safe / who can see it",
        "text": (
            "Your account is protected with a password and a secure login "
            "system. Only you can see the visits and doctors you've logged - "
            "there's no sharing between different reps' accounts."
        ),
    },
    {
        "id": "mobile",
        "title": "Can I use this on my phone",
        "text": (
            "Yes - the app works in any mobile browser, so you can log a "
            "visit right after leaving a doctor's office, from your phone, "
            "without needing to be at a computer."
        ),
    },
    {
        "id": "pricing",
        "title": "How much does it cost / is there a free trial",
        "text": (
            "Signing up and using HcPilot AI is free to try - just click "
            "'Get Started Free' or 'Sign Up' and create an account, no credit "
            "card needed."
        ),
    },
]


def get_knowledge_base() -> List[Dict[str, str]]:
    """Return the knowledge base chunks."""
    return KNOWLEDGE_BASE