import os

import cv2

from .vendor import tbpu
from .vendor.PPOCR_api import GetOcrApi, PPOCR_pipe
from .. import resource as res
from ..adb import ADB
from ..config import get_config
from ..demoviewer import demoviewer


class OCR:
    ocr_en = None
    ocr_cn = None

    @classmethod
    def _get_path(cls):
        path = get_config("user_config.yaml/paddleocr_json/path")
        if not path.endswith(".exe"):
            raise FileNotFoundError("Path should be a .exe file")
        if not os.path.exists(path):
            raise FileNotFoundError("Path not found")
        return path

    @classmethod
    def _load_model_if_not_loaded(cls):
        path = cls._get_path()
        if cls.ocr_cn is None:
            cls.ocr_cn = GetOcrApi(path, argument={
                'config_path': "models/config_chinese.txt"
            })
        if cls.ocr_en is None:
            cls.ocr_en = GetOcrApi(path, argument={
                'config_path': "models/config_en.txt"
            })

    @classmethod
    def mat_to_bytes(cls, mat):
        return cv2.imencode('.bmp', mat)[1].tobytes()

    """
    Returns:
    1. det='std': list of detected texts, which element is a dict, with keys:
        - 'text' (str): the detected text
        - 'score' (float): the confidence of the detected text
        - 'position' (List[x1: int, y1, x2, y2]): the position of the detected text
    2. std='single_line'/'multi_line': detected text, dict with keys:
        - 'text' (str): the detected text
        - 'score' (float): the confidence of the detected text
    """

    @classmethod
    def ocr(cls, mat, mode='cn', det='single_line'):
        cls._load_model_if_not_loaded()

        match mode:
            case "digit":
                model: PPOCR_pipe = cls.ocr_en
            case "en":
                model: PPOCR_pipe = cls.ocr_en
            case _:
                model: PPOCR_pipe = cls.ocr_cn

        img_bytes = cls.mat_to_bytes(mat)

        result = model.runBytes(img_bytes)
        if result['code'] > 101:
            raise RuntimeError("PaddleOCR runtime error. " + str(result))

        match det:
            case "std":
                if result['code'] == 101:
                    return []
                assert result['code'] == 100
                result = tbpu.MergePara(result)
                # rename ['data']['box'] to ['data']['position']
                for i in range(len(result["data"])):
                    result['data'][i]['position'] = result['data'][i].pop('box')
                    # position should be converted from [[LUx, LUy][RUx, RUy][LBx, LBy][RBx, RBy]] to [x1, y1, x2, y2]
                    result['data'][i]['position'] = [result['data'][i]['position'][0][0],
                                                     result['data'][i]['position'][0][1],
                                                     result['data'][i]['position'][2][0],
                                                     result['data'][i]['position'][2][1]]
                return result["data"]
            case "multi_line" | "single_line":
                if result['code'] == 101:
                    return {
                        "text": "",
                        "score": 0
                    }
                assert result['code'] == 100
                result = tbpu.MergeLine(result)
                ret = {
                    "text": "",
                    "score": 0
                }
                for r in result:
                    ret['text'] += r['text']
                    ret['score'] += r['score']
                ret['score'] /= len(result)
                return ret

    @classmethod
    def ocr_res(cls, res_path: str, mode='cn', det="single_line", force=True):
        cls._load_model_if_not_loaded()

        res_data = res.res_value(res_path)
        x1, y1, x2, y2 = [int(x) for x in res_data.split('-')]

        mat = ADB.screencap_mat(force=force)
        mat = mat[y1:y2, x1:x2]

        # demoviewer.show_img([[x1, y1, x2, y2]])

        return cls.ocr(mat, mode=mode, det=det)

    '''
    Returns:
    List of detected texts, which element is a dict, with keys: (like single_line)
    - 'text' (str): the detected text
    - 'score' (float): the confidence of the detected text
    '''

    @classmethod
    def ocr_list(cls, list_pos, mode='cn', force=True):
        cls._load_model_if_not_loaded()
        mat_screen = ADB.screencap_mat(force=force)

        demoviewer.show_img(list_pos)

        mat_list = [mat_screen[y1:y2, x1:x2] for x1, y1, x2, y2 in list_pos]

        return [cls.ocr(mat, mode=mode, det='single_line') for mat in mat_list]
