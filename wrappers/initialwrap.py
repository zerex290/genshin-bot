def guide(func, unk_opt=False):
    response = [f"{'Неверно указаны опции команды, ознакомьтесь со справкой:' if unk_opt else ''}"]
    return {'data': ''.join(response) + func.__doc__}


def get_guide(func):
    def wrapper(options):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                response.append(data.get('data', data.get('error')))

        return {'message': ''.join(response)}

    return wrapper


def make_choice(func):
    def wrapper(options, raw):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'raw': raw}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                response.append(data.get('data', data.get('error')))

        return {'message': ''.join(response)}

    return wrapper


def convert(func):
    def wrapper(options, reply_message):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'reply_message': reply_message}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                response.append(data.get('data', data.get('error')))

        return {'message': ''.join(response)}

    return wrapper


def set_timer(func):
    def wrapper(options, api, chat_id, user_id, username, raw):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'api': api, 'chat_id': chat_id, 'user_id': user_id,
                                               'username': username, 'raw': raw}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                response.append(data.get('data', data.get('error')))

        return {'message': ''.join(response)}

    return wrapper


def send_attachments(func):
    def wrapper(options, api, attachments):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'api': api, 'attachments': attachments}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                return {'attachments': data.get('data'), 'message': data.get('error')}

        return {'message': ''.join(response)}

    return wrapper


def get_randtags(func):
    def wrapper(options, raw):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'raw': raw}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                response.append(data.get('data', data.get('error')))

        return {'message': ''.join(response)}

    return wrapper


def get_randpics(func):
    def wrapper(self, options, api, chat_id, raw):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'api': api, 'chat_id': chat_id, 'raw': raw}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                return behaviours[opt]['fn'](**behaviours[opt]['kwargs'])

        return {'message': ''.join(response)}

    return wrapper


def manage_user_commands(func):
    def get_status(self, chat_id):
        response = {
            'data': f"В данный момент манипуляции с пользовательскими командами являются "
                    f"{'общедоступными' if self.commands[chat_id]['ffa'] else 'ограниченными'}!"
        }
        return response

    def make_ffa(self, api, chat_id, user_id):
        if api.vk.chats.check_for_privileges(api, chat_id, user_id):
            if not self.commands[chat_id]['ffa']:
                self.commands[chat_id]['ffa'] = True
                self.dump()
                return {'data': 'Манипуляции с пользовательскими командами теперь общедоступны!'}
            else:
                return {'data': 'Манипуляции с пользовательскими командами уже являются общедоступными!'}
        else:
            return {'error': 'Ошибка: для использования данной команды требуется быть администратором чата!'}

    def make_limited(self, api, chat_id, user_id):
        if api.vk.chats.check_for_privileges(api, chat_id, user_id):
            if self.commands[chat_id]['ffa']:
                self.commands[chat_id]['ffa'] = False
                self.dump()
                return {'data': 'Манипуляции с пользовательскими командами теперь ограничены!'}
            else:
                return {'data': 'Манипуляции с пользовательскими командами уже являются ограниченными!'}
        else:
            return {'error': 'Ошибка: для использования данной команды требуется быть администратором чата!'}

    def wrapper(self, options, api, chat_id, user_id):
        behaviours = {
            '-с': {'fn': get_status, 'kwargs': {'self': self, 'chat_id': chat_id}},
            '-общ': {'fn': make_ffa, 'kwargs': {'self': self, 'api': api, 'chat_id': chat_id, 'user_id': user_id}},
            '-огр': {'fn': make_limited, 'kwargs': {'self': self, 'api': api, 'chat_id': chat_id, 'user_id': user_id}},
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'chat_id': chat_id}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        elif {'-общ', '-огр'}.issubset(options):
            response.append('Вы не можете одновременно использовать две противоположных по смыслу команды!')
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                response.append(data.get('data', data.get('error')))

        return {'message': '\n'.join(response)}

    return wrapper


def add_user_command(func):
    def wrapper(self, options, api, chat_id, user_id, raw, attachments):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'api': api, 'chat_id': chat_id,
                                               'user_id': user_id, 'raw': raw, 'attachments': attachments}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                response.append(data.get('data', data.get('error')))

        return {'message': ''.join(response)}

    return wrapper


def delete_user_command(func):
    def wrapper(self, options, api, chat_id, user_id, name):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'api': api, 'chat_id': chat_id,
                                               'user_id': user_id, 'name': name}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                response.append(data.get('data', data.get('error')))

        return {'message': ''.join(response)}

    return wrapper
