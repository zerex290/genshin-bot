def guide(func, unk_opt=False):
    response = [f"{'Неверно указаны опции команды, ознакомьтесь со справкой:' if unk_opt else ''}"]
    return {'data': ''.join(response) + func.__doc__}


def get_ps_pictures(func):
    def wrapper(options, api, chat_id):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'api': api, 'chat_id': chat_id}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                return {'attachments': data['data']}

        return {'message': ''.join(response)}

    return wrapper


def get_ascension_materials(func):
    def wrapper(options, api, chat_id, character):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'api': api, 'chat_id': chat_id, 'character': character}}
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


def register_in_gdb(func):
    def wrapper(self, options, user_id, raw):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'user_id': user_id, 'raw': raw}}
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


def remove_data_from_gdb(func):
    def wrapper(self, options, user_id):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'user_id': user_id}}
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


def get_notes(func):
    def another_user(self, user_id):
        return func(self, user_id)

    def wrapper(self, options, reply_message, user_id):
        behaviours = {
            '-у': {'fn': another_user, 'kwargs': {'self': self, 'user_id': reply_message.get('from_id')}},
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'user_id': user_id}}
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


def get_daily_reward(func):
    def wrapper(self, options, api, chat_id, user_id):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'api': api, 'chat_id': chat_id, 'user_id': user_id}}
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


def get_stats(func):
    def another_user(self, user_id):
        return func(self, user_id)

    def wrapper(self, options, reply_message, user_id):
        behaviours = {
            '-у': {'fn': another_user, 'kwargs': {'self': self, 'user_id': reply_message.get('from_id')}},
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'user_id': user_id}}
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


def activate_redeem(func):
    def wrapper(self, options, user_id, raw):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'user_id': user_id, 'raw': raw}}
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


def manage_resin_notifications(func):
    def turn_on(self, user_id):
        self.accounts[user_id]['resin_notify'] = True
        self.dump_accounts()
        return {'data': 'Автоматическое напоминание потратить смолу включено!'}

    def turn_off(self, user_id):
        self.accounts[user_id]['resin_notify'] = False
        self.dump_accounts()
        return {'data': 'Автоматическое напоминание потратить смолу выключено!'}

    def wrapper(self, options, user_id):
        behaviours = {
            '-вкл': {'fn': turn_on, 'kwargs': {'self': self, 'user_id': user_id}},
            '-выкл': {'fn': turn_off, 'kwargs': {'self': self, 'user_id': user_id}},
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'self': self, 'user_id': user_id}}
        }
        response = []

        if not options.issubset(set(behaviours)):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'], unk_opt=True)['data'])
        elif {'-п'}.issubset(options):
            response.append(behaviours['-п']['fn'](**behaviours['-п']['kwargs'])['data'])
        elif {'-вкл', '-выкл'}.issubset(options):
            response.append('Вы не можете одновременно использовать две противоположных по смыслу команды!')
        else:
            for opt in options:
                data = behaviours[opt]['fn'](**behaviours[opt]['kwargs'])
                response.append(data.get('data', data.get('error')))

        return {'message': ''.join(response)}

    return wrapper


def get_database(func):
    def wrapper(options, api, chat_id, user_id):
        behaviours = {
            '-п': {'fn': guide, 'kwargs': {'func': func}},
            'default': {'fn': func, 'kwargs': {'api': api, 'chat_id': chat_id, 'user_id': user_id}}
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