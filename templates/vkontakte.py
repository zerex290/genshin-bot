"""Service use only"""


class Files:
    ATTACHMENT_TYPES = {
        'photo': lambda p: f"photo{p['owner_id']}_{p['id']}_{p['access_key']}",
        'doc': lambda d: f"doc{d['owner_id']}_{d['id']}",
        'audio': lambda a: f"audio{a['owner_id']}_{a['id']}",
        'video': lambda v: f"video{v['owner_id']}_{v['id']}_{v['access_key']}",
        'photo_wall': lambda pw: f"photo{pw['owner_id']}_{pw['id']}"
    }

    UPLOAD_TYPES = {
        'photo': lambda u, dir_, peer: u.photo_messages(dir_, peer_id=peer),
        'doc': lambda u, dir_, peer, title: u.document_message(dir_, peer_id=peer, title=title),
        'photo_wall': lambda u, dir_, peer: u.photo_wall(dir_, group_id=peer)
    }


class Chats:
    @staticmethod
    def new_chat(chat_id: int, members: list) -> dict:
        response = {
            'id': chat_id,
            'ffa': True,
            'members': members,
            'stats': {}
        }
        return response

    @staticmethod
    def members(members: list) -> list:
        response = []

        for mem in members:
            response.append(
                {
                    'id': mem['member_id'],
                    'invited_by': mem['invited_by'],
                    'join_date': mem['join_date'],
                    'is_owner': mem.get('is_owner', False),
                    'is_admin': mem.get('is_admin', False),
                    'can_kick': mem.get('can_kick', False),
                    'resin_notify': False
                }
            )
        return response
