import os

from arona.resource import _load_res_yaml, _get_resource_real_path


def read_used_resources() -> set[str]:
    res_data = _load_res_yaml()

    def get_resources(data) -> set[str]:
        res_set = set()
        if isinstance(data, dict):
            for k, v in data.items():
                res_set.update(get_resources(v))
        elif isinstance(data, list):
            for v in data:
                res_set.update(get_resources(v))
        elif isinstance(data, str):
            res_set.add(data)
        return res_set

    return get_resources(res_data)


def run():
    res_set = read_used_resources()
    print(res_set)
    res_path = _get_resource_real_path()
    bak_path = os.path.join(res_path, 'bak')
    os.makedirs(bak_path, exist_ok=True)
    for root, dirs, files in os.walk(res_path):
        for file in files:
            if (file.endswith('.png') or file.endswith('.jpg')) and (file not in res_set):
                file_path = os.path.join(root, file)
                print(f"Unused resource: {file_path}")
                bak_file_path = os.path.join(bak_path, file)
                os.rename(file_path, bak_file_path)


if __name__ == '__main__':
    run()