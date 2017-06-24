# -*- coding: utf-8 -*-
# author: zqy

import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock
import pybj
import json
import requests
import os


class TestJinjingzheng(unittest.TestCase):
    def test_config(self):
        conf = pybj.load_config(
            os.path.join(os.path.dirname(__file__), 'conf.ini'))
        self.assertEqual("...", conf['User']['userid'])

    def test_get_enter_car_list_201(self):
        response = requests.Response()
        response.status_code = 200
        response._content = bytes('''
                {
                  "rescode": "201",
                  "resdes": "访问过于频繁"
                }
                ''', encoding="utf-8")
        with self.assertRaises(Exception) as raise_context:
            with mock.patch('requests.post', return_value=response) as mocked:
                datalist = pybj.get_enter_car_list(jinjingzheng.load_config("./conf.ini"))
            mocked.assert_called()
        e = raise_context.exception
        self.assertEqual('查询车辆信息失败 code=201, message=访问过于频繁', str(e))

    def test_get_enter_car_list_500(self):
        response = requests.Response()
        response.status_code = 500
        with self.assertRaises(requests.RequestException) as raise_context:
            with mock.patch('requests.post', return_value=response) as mocked:
                datalist = pybj.get_enter_car_list(pybj.load_config("./conf.ini"))
        e = raise_context.exception
        self.assertEqual("500 Server Error: None for url: None", str(e))

    def test_get_enter_car_list_200(self):
        response = requests.Response()
        response.status_code = 200
        response._content = bytes('''
        {
              "datalist": [
                {
                  "carid": "456",
                  "userid": "123",
                  "licenseno": "xxxx",
                  "applyflag": "0",
                  "carapplyarr": [
                    {
                      "applyid": "12323",
                      "carid": "456",
                      "cartype": "02",
                      "engineno": "xxxxV",
                      "enterbjend": "2017-06-16",
                      "enterbjstart": "2017-06-10",
                      "existpaper": "",
                      "licenseno": "xxxx",
                      "loadpapermethod": "",
                      "remark": "123r",
                      "status": "1",
                      "syscode": "",
                      "syscodedesc": "",
                      "userid": "123"
                    }
                  ]
                }
              ],
              "rescode": "200",
              "resdes": "获取申请信息列表成功"
            }
        ''', encoding="utf-8")
        with mock.patch('requests.post', return_value=response) as mocked:
            datalist = pybj.get_enter_car_list(pybj.load_config("./conf.ini"))
            mocked.assert_called()
            self.assertEqual(json.loads('''[{"carid": "456", "userid": "123", "licenseno": "xxxx", "applyflag": "0", "carapplyarr": [
        {"applyid": "12323", "carid": "456", "cartype": "02", "engineno": "xxxxV", "enterbjend": "2017-06-16",
         "enterbjstart": "2017-06-10", "existpaper": "", "licenseno": "xxxx", "loadpapermethod": "", "remark": "123r",
         "status": "1", "syscode": "", "syscodedesc": "", "userid": "123"}]}]'''), datalist)

    def test_is_time_to_apply_None(self):
        with self.assertRaises(Exception) as cm:
            pybj.is_time_to_apply(None)
        e = cm.exception
        self.assertEqual('车辆数据为空', str(e))

    def test_sign(self):
        userid = '123'
        appkey = 'kkk'
        deviceid = 'ddd'
        timestamp = '1496994052000'
        token = pybj.sign({'userid': userid, 'appkey': appkey, 'deviceid': deviceid, 'timestamp': timestamp}, timestamp)
        self.assertEqual('BD7659423D03CC203533D2D07B658723', token)

if __name__ == '__main__':
    unittest.main()
