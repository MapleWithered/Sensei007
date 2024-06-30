from cnocr import CnOcr

from .. import resource as res
from ..adb import ADB
from ..demoviewer import demoviewer


class OCR:
    ocr_en = None
    ocr_cn = None

    @classmethod
    def _load_model_if_not_loaded(cls):
        if cls.ocr_en is None:
            cls.ocr_en = CnOcr(det_model_name='en_PP-OCRv3_det', rec_model_name='en_PP-OCRv3')
        if cls.ocr_cn is None:
            cls.ocr_cn = CnOcr()

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
                model: CnOcr = cls.ocr_en
            case "en":
                model: CnOcr = cls.ocr_en
            case _:
                model: CnOcr = cls.ocr_cn
        match det:
            case "std":
                return model.ocr(mat)
            case "multi_line":
                ret = {
                    "text": "",
                    "score": 0
                }
                res = model.ocr(mat)
                res.sort(key=lambda x: x['position'][1])
                for r in res:
                    ret['text'] += r['text']
                    ret['score'] += r['score']
                ret['score'] /= len(res)
                return ret
            case "single_line":
                return model.ocr_for_single_line(mat)

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

        match mode:
            case "digit":
                model = cls.ocr_en
            case "en":
                model = cls.ocr_en
            case _:
                model = cls.ocr_cn

        return model.ocr_for_single_lines(mat_list)
