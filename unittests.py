import unittest
from helper import time_converter, date_converter, report_time_converter, new_time_converter, translate_hours


class Testing(unittest.TestCase):
    def test_time_converter(self):
        self.assertEqual(time_converter('8'), 8.0)
        self.assertEqual(time_converter('8ч'), 8.0)
        self.assertEqual(time_converter('8 часов'), 8.0)
        self.assertEqual(time_converter('8,3часов'), 8.3)
        self.assertEqual(time_converter('8,3'), 8.3)
        self.assertEqual(time_converter('8.3'), 8.3)
        self.assertEqual(time_converter('3часа'), 3.0)

    def test_date_converter(self):
        self.assertEqual(date_converter('6.5.22'), '06.05.2022')
        self.assertEqual(date_converter('06.05.22'), '06.05.2022')
        self.assertEqual(date_converter('6.5.2022'), '06.05.2022')
        self.assertEqual(date_converter('06.05.2022'), '06.05.2022')
        self.assertEqual(date_converter('06.05'), '06.05.2022')
        self.assertEqual(date_converter('6.5'), '06.05.2022')

    def test_report_time_converter(self):
        self.assertEqual(report_time_converter('16:45'), (16, 45))
        self.assertEqual(report_time_converter('21:34'), (21, 34))
        self.assertEqual(report_time_converter('00:01'), (0, 1))

    def test_new_time_converter(self):
        self.assertEqual(new_time_converter(12), 12)
        self.assertEqual(new_time_converter(23), 23)
        self.assertEqual(new_time_converter(1), '01')
        self.assertEqual(new_time_converter(7), '07')
        self.assertEqual(new_time_converter(9), '09')

    def test_translate_hours(self):
        self.assertEqual(translate_hours(32), 'часа')
        self.assertEqual(translate_hours(26), 'часов')
        self.assertEqual(translate_hours(1), 'час')
        self.assertEqual(translate_hours(0.5), 'часа')
        self.assertEqual(translate_hours(11), 'часов')
