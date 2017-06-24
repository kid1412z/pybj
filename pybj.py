# -*- coding: utf-8 -*-
# author: zqy

from __future__ import print_function

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import requests
from datetime import datetime
from datetime import date
from datetime import timedelta
import base64 as base64
import time
import hashlib
import argparse
import random

ENTER_CAR_LIST_URL = 'https://api.jinjingzheng.zhongchebaolian.com/enterbj/platform/enterbj/entercarlist'
APPLY_URL = 'https://api.jinjingzheng.zhongchebaolian.com/enterbj/platform/enterbj/submitpaper'
ENV_CHECK_URL = 'https://api.jinjingzheng.zhongchebaolian.com/enterbj/platform/enterbj/checkenvgrade'
REQUEST_TIMEOUT_SEC = 5


class FatalError(Exception):
    """ Fatal errors. """
    pass


def load_config(config_file='./conf.ini'):
    conf = configparser.ConfigParser()
    conf.read(config_file)
    return conf


def _headers():
    return {
        'Host': 'api.jinjingzheng.zhongchebaolian.com',
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-cn',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://api.jinjingzheng.zhongchebaolian.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_2 like Mac OS X) AppleWebKit/603.2.4 (KHTML, like Gecko) Mobile/14F89',
        'Referer': 'https://api.jinjingzheng.zhongchebaolian.com/enterbj/jsp/enterbj/index.jsp'
    }


def get_enter_car_list(conf):
    """
    查询车辆和申请信息
    :param conf:
    :return: datalist of response
    :raise: requests.exceptions.RequestException HTTP request error
    """
    user_info = conf['User']
    request_data = {
        'userid': user_info['userid'],
        'appkey': 'kkk',
        'deviceid': 'ddd',
        'timestamp': str(current_time_ms()),
        'appsource': ''
    }
    token = sign(request_data, request_data['timestamp'])
    request_data['token'] = token
    r = requests.post(ENTER_CAR_LIST_URL, headers=_headers(), data=request_data, timeout=REQUEST_TIMEOUT_SEC)
    r.raise_for_status()
    content = r.json()
    if content['rescode'] == "200":
        if content.get('datalist') is None or len(content['datalist']) == 0:
            raise FatalError("车辆列表为空，请在APP中添加车辆")
        return content['datalist']
    raise RuntimeError("查询车辆信息失败 code={}, message={}".format(content['rescode'], content['resdes']))


def check_env_grade(conf, cardata):
    """
    核验环保等级
    :param conf: 配置
    :param cardata: 查询得到的车辆数据
    :return:
    """
    user_info = conf['User']
    request_data = {
        'appsource': 'bjjj',
        'userid': user_info['userid'],
        'carid': cardata['carid'],
        'licenseno': cardata['licenseno'],
        'carmodel': user_info['carmodel'],
        'carregtime': user_info['carregtime']
    }
    r = requests.post(ENV_CHECK_URL, headers=_headers(), data=request_data, timeout=REQUEST_TIMEOUT_SEC)
    r.raise_for_status()
    content = r.json()
    if content.get('rescode') == '200':
        print("核验环保等级成功：等级为：{}".format(content['envGrade']))
        return content['envGrade']

    raise RuntimeError('核验环保等级失败{}'.format(content))


def tomorrow():
    return date.today() + timedelta(days=1)


def check_enter_date(enter_date_str):
    enter_date = datetime.strptime(enter_date_str, '%Y-%m-%d').date()
    if enter_date > date.today() + timedelta(days=4) or enter_date < tomorrow():
        raise FatalError('日期不合法: {}, 请仔细阅读帮助。'.format(enter_date))


def do_apply(conf, cardata, enter_date_str, skip_check_env=None):
    user_info = conf['User']
    check_enter_date(enter_date_str)
    env_grade = user_info['env_grade'] if skip_check_env else check_env_grade(conf, cardata)
    request_data = {
        'appsource': 'bjjj',
        'hiddentime': datetime.today().strftime('%Y-%m-%d+%H:%M:%S'),
        'inbjentrancecode1': '05',
        'inbjentrancecode': '74',
        'inbjduration': 7,
        'inbjtime': enter_date_str,
        'appkey': '',
        'deviceid': '',
        'token': '',
        'timestamp': '',
        'userid': user_info['userid'],
        'licenseno': user_info['licenseno'],
        'engineno': user_info['engineno'],
        'cartypecode': '02',
        'vehicletype': '12',
        'drivingphoto': encode_photo(user_info['vihicle_licence_photo']),  # 行驶证照片
        'carphoto': encode_photo(user_info['car_photo']),  # 车辆正面照片
        'drivername': user_info['drivername'],
        'driverlicenseno': user_info['driverlicenseno'],  # 驾驶证号
        'driverphoto': encode_photo(user_info['driver_licence_photo']),  # 驾驶证照片
        'personphoto': encode_photo(user_info['person_with_id_photo']),  # 驾驶人和身份证合影
        'gpslon': '',
        'gpslat': '',
        'phoneno': '',
        'imei': '',
        'imsi': '',
        'carid': cardata['carid'],
        'carmodel': user_info['carmodel'],
        'carregtime': user_info['carregtime'],
        'envGrade': env_grade,
        'code': ''
        # 'sign': '...'
    }
    r = requests.post(APPLY_URL, headers=_headers(), data=request_data, timeout=REQUEST_TIMEOUT_SEC)
    r.raise_for_status()
    content = r.json()
    if content['rescode'] != '200':
        raise RuntimeError("申请失败 code={}, message={}".format(content['rescode'], content['resdes']))


def is_time_to_apply(car_data):
    """
    查询是否需要办理
    :param car_data: data item in get_enter_car_list API return
    :return:
    """
    if car_data is None:
        raise FatalError("车辆数据为空")
    applies = car_data['carapplyarr']
    if applies is None or len(applies) == 0:
        return True
    latest_expire_date = datetime.strptime('2000-01-01', '%Y-%m-%d').date()
    for apply in applies:
        enterbjend = apply.get('enterbjend')
        if enterbjend is not None:
            expire_date = datetime.strptime(enterbjend, '%Y-%m-%d').date()
            if expire_date > latest_expire_date:
                latest_expire_date = expire_date
    return latest_expire_date <= date.today()


def car_to_apply(conf):
    """
    查询申请车辆的信息
    :param conf: 配置
    :return: 车辆信息
    """
    carlist = get_enter_car_list(conf)
    licenseno = conf['User']['licenseno']
    for car in carlist:
        if car.get('licenseno') == licenseno:
            return car
    raise FatalError('车牌号:{}在系统中未找到，请在APP中注册。carlist={}'.format(licenseno, carlist))


def current_time_ms():
    return int(round(round(time.time()) * 1000))


def encode_photo(filepath):
    """
    encode photo to text
    :param filepath: file encoded
    :return: encoded text
    """
    with open(filepath, mode="rb") as f:
        return base64.encodebytes(f.read()).decode("utf-8")


def decode_photo(base64_text):
    """
    decode text to photo
    :param base64_text:
    :return: decoded bytes
    """
    return base64.b64decode(bytes(base64_text, encoding="utf-8"))


def sign(data, secret):
    """
    token生成方法(不需要也可以)
    :param data: request json
    :param secret: secret str
    :return: token str
    """
    # {'userid': userid, 'appkey': 'kkk', 'deviceid': 'ddd', 'timestamp': timestamp}
    keys = sorted(data.keys())
    kvs = [key + data[key] for key in keys]
    m = hashlib.md5()
    t = ''.join([secret, ''.join(kvs), secret])
    m.update(t.encode())
    return m.hexdigest().upper()


def task(conf, enter_date_str, skip_check_env=False):
    cardata = car_to_apply(conf)
    print('Car data: {}'.format(cardata))
    if is_time_to_apply(cardata):
        do_apply(conf, cardata, enter_date_str, skip_check_env=skip_check_env)
    else:
        raise FatalError("目前不需要办理")


def parse_args():
    parser = argparse.ArgumentParser(description='Happy journey!')
    _help = 'The date you will enter: tomorrow <= yyyy-mm-dd <= today + 4days. Default tomorrow.'
    parser.add_argument('-d', '--date', default=tomorrow().strftime('%Y-%m-%d'), help=_help)
    _help = 'Retry times: retry times if fail. Default 0'
    parser.add_argument('-t', '--retry', default='0', help=_help)
    _help = '''Add this flag means you want to skip check_env_grade from server, 
               and the env_grade will be read from conf.ini. 
               This flag is made to decrease the probability of being refused when the traffic is too large.
               I recommend you check from server for the first time, 
               to make sure you fill in the right one.
            '''
    parser.add_argument('-s', '--skip_check_env_grade', action="store_true", help=_help)
    _help = 'Path to config file. Default ./conf.ini'
    parser.add_argument('-f', '--file', default='./conf.ini', help=_help)
    return parser.parse_args()


def main():
    args = parse_args()
    retry_times = int(args.retry)
    assert retry_times >= 0
    conf = load_config(args.file)
    for i in range(retry_times + 1):
        try:
            task(conf, args.date, skip_check_env=args.skip_check_env_grade)
            time.sleep(random.randrange(5, 20))
        except requests.exceptions.RequestException as e:
            print("申请失败，网络出错. {}".format(e))
            continue
        except RuntimeError as e:
            print("申请失败.{}".format(e))
            continue
        except FatalError as e:
            print("申请失败.{}".format(e))
        except Exception as e:
            print("申请失败. 未知错误：{}".format(e))
        else:
            print("申请成功，请到客户端查看。")
        break


if __name__ == '__main__':
    main()
