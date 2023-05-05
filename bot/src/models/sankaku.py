from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime

from ..types.sankaku import Rating, TagType, MediaType


@dataclass()
class Author:
    id: int
    name: str
    avatar: str
    avatar_rating: Rating


@dataclass()
class Tag:
    id: int
    name_en: str
    name_ja: Optional[str]
    type: TagType
    count: int
    post_count: int
    pool_count: int
    series_count: int
    locale: str
    rating: Rating
    version: Optional[int]
    tagName: str
    total_post_count: int
    total_pool_count: int
    name: str


@dataclass()
class Post:
    id: int
    rating: Rating
    status: str
    author: Author

    sample_url: str
    sample_width: int
    sample_height: int

    preview_url: str
    preview_width: int
    preview_height: int

    file_url: str
    width: int
    height: int

    file_size: int
    file_type: str
    created_at: datetime

    has_children: bool
    has_comments: bool
    has_notes: bool
    is_favorited: bool
    user_vote: Optional[int]
    md5: str
    parent_id: Optional[int]
    change: Optional[int]

    fav_count: int
    recommended_posts: int
    recommended_score: int
    vote_count: int
    total_score: int
    comment_count: Optional[int]

    source: str
    in_visible_pool: bool
    is_premium: bool
    is_rating_locked: bool
    is_note_locked: bool
    is_status_locked: bool
    redirect_to_signup: bool

    sequence: Any
    generation_directives: Any
    video_duration: Any
    tags: list[Tag]

    @property
    def ext(self) -> str:
        return self.file_type.split('/')[1]

    @property
    def mediatype(self) -> MediaType:
        match self.ext:
            case 'png' | 'jpeg' | 'webp':
                return MediaType.IMAGE
            case 'webm' | 'mp4':
                return MediaType.VIDEO
            case 'gif':
                return MediaType.ANIMATED_GIF
            case _:
                raise ValueError(f"Can't find MediaType for file with ext '{self.ext}'!")
