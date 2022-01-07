"""Service use only"""


import constants


class Commands:
    def __init__(self, api):
        self.api = api

    def __enter__(self):
        self.coms = {
            'команды': {'func': self.api.init.get_guide,
                        'args': {}},

            'exec': {'func': self.api.execute,
                     'args': {'user_id': self.api.vk.messages.user_id,
                              'raw': self.get_command(self.api.vk.messages.message)}},

            'конверт': {'func': self.api.init.convert,
                        'args': {'reply_message': self.api.vk.messages.reply_message}},

            'таймер': {'func': self.api.init.set_timer,
                       'args': {'api': self.api,
                                'chat_id': self.api.vk.messages.chat_id,
                                'user_id': self.api.vk.messages.user_id,
                                'username': self.api.vk.get_username(self.api.vk.messages.user_id),
                                'raw': self.get_command(self.api.vk.messages.message).lower()}},

            'выбери': {'func': self.api.init.make_choice,
                       'args': {'raw': self.get_command(self.api.vk.messages.message)}},

            'перешли': {'func': self.api.init.send_attachments,
                        'args': {'api': self.api,
                                 'attachments': self.api.vk.messages.attachments}},

            'рандомтег': {'func': self.api.init.booru.get_randtags,
                          'args': {'raw': self.get_command(self.api.vk.messages.message)}},

            'п': {'func': self.api.init.booru.get_randpics,
                  'args': {'api': self.api,
                           'chat_id': self.api.vk.messages.chat_id,
                           'raw': self.get_command(self.api.vk.messages.message)}},

            'комы': {'func': self.api.init.usercoms.get,
                     'args': {'chat_id': self.api.vk.messages.chat_id}},

            'аддком': {'func': self.api.init.usercoms.add,
                       'args': {'api': self.api,
                                'chat_id': self.api.vk.messages.chat_id,
                                'user_id': self.api.vk.messages.user_id,
                                'raw': self.get_command(self.api.vk.messages.message),
                                'attachments': self.api.vk.messages.attachments}},

            'делком': {'func': self.api.init.usercoms.delete,
                       'args': {'api': self.api,
                                'chat_id': self.api.vk.messages.chat_id,
                                'user_id': self.api.vk.messages.user_id,
                                'name': self.get_command(self.api.vk.messages.message).lower()}},
            'свитчком': {'func': self.api.init.usercoms.switch,
                         'args': {'api': self.api,
                                  'chat_id': self.api.vk.messages.chat_id,
                                  'user_id': self.api.vk.messages.user_id}},

            'геншрег': {'func': self.api.genshin.hoyolab.register_in_gdb,
                        'args': {'user_id': self.api.vk.messages.user_id,
                                 'raw': self.get_command(self.api.vk.messages.message)}},

            'геншдел': {'func': self.api.genshin.hoyolab.remove_data_from_gdb,
                        'args': {'user_id': self.api.vk.messages.user_id}},

            'резинноут': {'func': self.api.genshin.hoyolab.switch_resin_notifications,
                          'args': {'user_id': self.api.vk.messages.user_id,
                                   'raw': self.get_command(self.api.vk.messages.message).lower()}},

            'ресы': {'func': self.api.genshin.get_ascension_materials,
                     'args': {'api': self.api,
                              'chat_id': self.api.vk.messages.chat_id,
                              'character': self.get_command(self.api.vk.messages.message).lower()}},

            'бездна': {'func': self.api.genshin.get_spiral_abyss,
                       'args': {'api': self.api,
                                'chat_id': self.api.vk.messages.chat_id}},

            'фарм': {'func': self.api.genshin.get_daily_farm,
                     'args': {'api': self.api,
                              'chat_id': self.api.vk.messages.chat_id}},

            'таланты': {'func': self.api.genshin.get_boss_materials,
                        'args': {'api': self.api,
                                 'chat_id': self.api.vk.messages.chat_id}},

            'книги': {'func': self.api.genshin.get_books,
                      'args': {'api': self.api,
                               'chat_id': self.api.vk.messages.chat_id}},

            'данжи': {'func': self.api.genshin.get_domains,
                      'args': {'api': self.api,
                               'chat_id': self.api.vk.messages.chat_id}},

            'заметки': {'func': self.api.genshin.hoyolab.get_notes,
                        'args': {'user_id': self.api.vk.messages.user_id}},

            'награды': {'func': self.api.genshin.hoyolab.get_daily_reward,
                        'args': {'api': self.api,
                                 'chat_id': self.api.vk.messages.chat_id,
                                 'user_id': self.api.vk.messages.user_id}},

            'статы': {'func': self.api.genshin.hoyolab.get_stats,
                      'args': {'user_id': self.api.vk.messages.user_id}},

            'пром': {'func': self.api.genshin.hoyolab.activate_redeem,
                     'args': {'user_id': self.api.vk.messages.user_id,
                              'raw': self.get_command(self.api.vk.messages.message)}},

            'гдб': {'func': self.api.genshin.db.get_started,
                    'args': {'api': self.api,
                             'chat_id': self.api.vk.messages.chat_id,
                             'user_id': self.api.vk.messages.user_id}}
        }
        return self.coms

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.coms

    def get_command(self, raw: str):
        if raw.find(' ') != -1:
            return raw.replace(f"!{self.api.vk.messages.trigger} ", '')
        else:
            return ''


class PayloadTypes:
    def __init__(self, api, event):
        self.api = api
        self.event = event
        self.payloads = {
            'filters': {
                'characters_elem': [constants.Genshin.ELEMENT[v]['ru'] for v in constants.Genshin.ELEMENT],
                'weapons_type': [constants.Genshin.WEAPON_TYPES[v] for v in constants.Genshin.WEAPON_TYPES],
                'artifacts_type': [constants.Genshin.ARTIFACT_TYPES[v] for v in constants.Genshin.ARTIFACT_TYPES],
                'enemies_type': [constants.Genshin.ENEMY_TYPES[v] for v in constants.Genshin.ENEMY_TYPES]
            },

            'lists': {
                'characters': self.api.genshin.db.characters.characters,
                'weapons': self.api.genshin.db.weapons.weapons,
                'artifacts': self.api.genshin.db.artifacts.artifacts,
                'enemies': self.api.genshin.db.enemies.enemies
            }
        }

    def __enter__(self):
        self.responses = {
            'menu': {'func': self.api.genshin.db.get_started,
                     'args': {'api': self.api,
                              'chat_id': self.event.obj.get('peer_id'),
                              'user_id': self.event.obj.get('user_id')}},

            'characters': {'func': self.api.genshin.db.get_filtered_list,
                           'args': {'api': self.api,
                                    'user_id': self.event.obj.get('user_id'),
                                    'payloads': self.payloads,
                                    'payload_type': self.event.obj.payload.get('type'),
                                    'filter_': self.event.obj.payload.get('filter'),
                                    'page_': self.event.obj.payload.get('page')}},

            'characters_elem': {'func': self.api.genshin.db.get_filters,
                                'args': {'api': self.api,
                                         'chat_id': self.event.obj.get('peer_id'),
                                         'user_id': self.event.obj.get('user_id'),
                                         'payloads': self.payloads,
                                         'payload_type': self.event.obj.payload.get('type')}},

            'character': {'func': self.api.genshin.db.get_character,
                          'args': {'api': self.api,
                                   'user_id': self.event.obj.get('user_id'),
                                   'name': self.event.obj.payload.get('name'),
                                   'data': self.event.obj.payload.get('data'),
                                   'filter_': self.event.obj.payload.get('filter')}},

            'weapons': {'func': self.api.genshin.db.get_filtered_list,
                        'args': {'api': self.api,
                                 'user_id': self.event.obj.get('user_id'),
                                 'payloads': self.payloads,
                                 'payload_type': self.event.obj.payload.get('type'),
                                 'filter_': self.event.obj.payload.get('filter'),
                                 'page_': self.event.obj.payload.get('page')}},

            'weapons_type': {'func': self.api.genshin.db.get_filters,
                             'args': {'api': self.api,
                                      'chat_id': self.event.obj.get('peer_id'),
                                      'user_id': self.event.obj.get('user_id'),
                                      'payloads': self.payloads,
                                      'payload_type': self.event.obj.payload.get('type')}},

            'weapon': {'func': self.api.genshin.db.get_weapon,
                       'args': {'api': self.api,
                                'user_id': self.event.obj.get('user_id'),
                                'name': self.event.obj.payload.get('name'),
                                'data': self.event.obj.payload.get('data'),
                                'filter_': self.event.obj.payload.get('filter')}},


            'artifacts': {'func': self.api.genshin.db.get_filtered_list,
                          'args': {'api': self.api,
                                   'user_id': self.event.obj.get('user_id'),
                                   'payloads': self.payloads,
                                   'payload_type': self.event.obj.payload.get('type'),
                                   'filter_': self.event.obj.payload.get('filter'),
                                   'page_': self.event.obj.payload.get('page')}},

            'artifacts_type': {'func': self.api.genshin.db.get_filters,
                               'args': {'api': self.api,
                                        'chat_id': self.event.obj.get('peer_id'),
                                        'user_id': self.event.obj.get('user_id'),
                                        'payloads': self.payloads,
                                        'payload_type': self.event.obj.payload.get('type')}},

            'artifact': {'func': self.api.genshin.db.get_artifact,
                         'args': {'api': self.api,
                                  'user_id': self.event.obj.get('user_id'),
                                  'name': self.event.obj.payload.get('name'),
                                  'filter_': self.event.obj.payload.get('filter')}},

            'enemies': {'func': self.api.genshin.db.get_filtered_list,
                        'args': {'api': self.api,
                                 'user_id': self.event.obj.get('user_id'),
                                 'payloads': self.payloads,
                                 'payload_type': self.event.obj.payload.get('type'),
                                 'filter_': self.event.obj.payload.get('filter'),
                                 'page_': self.event.obj.payload.get('page')}},

            'enemies_type': {'func': self.api.genshin.db.get_filters,
                             'args': {'api': self.api,
                                      'chat_id': self.event.obj.get('peer_id'),
                                      'user_id': self.event.obj.get('user_id'),
                                      'payloads': self.payloads,
                                      'payload_type': self.event.obj.payload.get('type')}},

            'enemie': {'func': self.api.genshin.db.get_enemy,
                       'args': {'api': self.api,
                                'user_id': self.event.obj.get('user_id'),
                                'name': self.event.obj.payload.get('name'),
                                'data': self.event.obj.payload.get('data'),
                                'filter_': self.event.obj.payload.get('filter')}},
        }
        return self.responses

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.responses
