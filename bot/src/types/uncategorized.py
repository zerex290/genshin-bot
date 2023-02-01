from enum import Enum


class Month(Enum):
    JANUARY = 'Январь'
    FEBRUARY = 'Февраль'
    MARCH = 'Март'
    APRIL = 'Апрель'
    MAY = 'Май'
    JUNE = 'Июнь'
    JULY = 'Июль'
    AUGUST = 'Август'
    SEPTEMBER = 'Сентябрь'
    OCTOBER = 'Октябрь'
    NOVEMBER = 'Ноябрь'
    DECEMBER = 'Декабрь'


class IntMonth(Enum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12


class Weekday(Enum):
    MONDAY = 'Понедельник'
    TUESDAY = 'Вторник'
    WEDNESDAY = 'Среда'
    THURSDAY = 'Четверг'
    FRIDAY = 'Пятница'
    SATURDAY = 'Суббота'
    SUNDAY = 'Воскресенье'


class IntWeekday(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6
