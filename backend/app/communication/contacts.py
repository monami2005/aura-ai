from typing import List, Dict, Optional

# Mock/Local Contacts Registry (Can be populated from system contacts or user address book)
LOCAL_CONTACTS_REGISTRY: List[Dict[str, str]] = [
    {"name": "Riya", "category": "Friend", "disambiguation": "Riya (Friend)"},
    {"name": "Rahul", "category": "Work", "disambiguation": "Rahul (Work)"},
    {"name": "Mom", "category": "Family", "disambiguation": "Mom (Home)"},
    {"name": "Dad", "category": "Family", "disambiguation": "Dad (Home)"},
]

def resolve_contact(contact_name: str) -> Dict[str, Any]:
    """
    Search for contacts matching the query name.
    If multiple contacts match, returns ambiguous=True with options.
    If exact match, returns resolved contact.
    """
    name_clean = contact_name.strip().lower()
    matches = [c for c in LOCAL_CONTACTS_REGISTRY if name_clean in c["name"].lower()]

    if len(matches) == 1:
        return {
            "resolved": True,
            "ambiguous": False,
            "contact": matches[0],
            "name": matches[0]["name"]
        }
    elif len(matches) > 1:
        return {
            "resolved": False,
            "ambiguous": True,
            "matches": [m["disambiguation"] for m in matches],
            "clarification": f"Multiple contacts found for '{contact_name}': {', '.join(m['disambiguation'] for m in matches)}. Which one do you mean?"
        }
    else:
        # Single unlisted contact name provided by user
        return {
            "resolved": True,
            "ambiguous": False,
            "contact": {"name": contact_name},
            "name": contact_name
        }
