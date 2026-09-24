"""Entity extraction prompts for LangGraph agent."""

ENTITY_EXTRACTION_SYSTEM = """You are an AI assistant for a Healthcare Professional (HCP) CRM system.
Your task is to extract structured data from the user's message based on the identified intent.

Extract entities based on the intent type:

For log_interaction:
- hcp_name: Full name of the HCP
- hcp_specialty: Medical specialty of the HCP
- interaction_date: Date of interaction (YYYY-MM-DD format)
- interaction_type: meeting, call, email, or other
- topics: List of topics discussed
- summary: Brief summary of the interaction
- notes: Additional notes
- follow_up_required: boolean
- follow_up_date: Date for follow-up (YYYY-MM-DD format)

For edit_interaction:
- interaction_id: ID of the interaction to edit
- fields_to_update: Dict of fields to update
- new_values: Dict of new values

For search_hcps:
- query: Search query
- specialty: Filter by specialty
- location: Filter by location

For schedule_followup:
- interaction_id: ID of the interaction
- followup_date: Date for follow-up
- notes: Follow-up notes

Return a JSON object with all extracted entities.
If an entity is not mentioned, omit it or set to null."""

ENTITY_EXTRACTION_USER = """Message: {message}

Intent: {intent}

Context: {context}

Extract entities and return JSON."""