COMMON_FAMILY_RELATIONS = ["Father", "Mother", "Child", "Elderly"]


def normalize_family_member_selection(selected_value, family_members):
    if selected_value in (None, ""):
        return None

    if isinstance(selected_value, int):
        selected_id = selected_value
    else:
        cleaned_value = str(selected_value).strip()
        if cleaned_value.lower() in {"", "self", "me", "myself"}:
            return None
        if not cleaned_value.isdigit():
            return None
        selected_id = int(cleaned_value)

    for member in family_members or []:
        if int(member.get("id")) == selected_id:
            return selected_id

    return None


def build_family_member_options(family_members):
    options = [{"value": "", "label": "For Myself"}]
    for member in family_members or []:
        options.append({
            "value": str(member.get("id")),
            "label": format_family_member_label(member.get("name"), member.get("relation")),
        })
    return options


def format_family_member_label(member_name, relation, fallback="For Myself"):
    name = str(member_name or "").strip()
    relation_value = str(relation or "").strip()

    if name and relation_value:
        return f"{name} ({relation_value})"
    if name:
        return name
    if relation_value:
        return relation_value
    return fallback
