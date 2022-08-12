from ..models.sankaku import Post


def find_restricted_tags(post: Post, restricted_tags: tuple[str, ...]) -> bool:
    for tag in post.tags:
        if tag.name_en in restricted_tags:
            return True
    return False
