from ..models.sankaku import Post


def find_forbidden_tags(post: Post, forbidden_tags: tuple[str, ...]) -> bool:
    for tag in post.tags:
        if tag.name_en in forbidden_tags:
            return True
    return False
