def map_repository_item_result(row):
    item, votes, favourites, is_favourite, is_voted_positive, is_voted_negative = row

    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "services": item.services,
        "app_id": item.app_id,
        "user_id": item.user_id,
        "votes": votes or 0,
        "downloads": item.downloads or 0,
        "favourites": favourites or 0,
        "is_favourite": bool(is_favourite),
        "is_voted_positive": bool(is_voted_positive),
        "is_voted_negative": bool(is_voted_negative),
        "state": item.state,
    }