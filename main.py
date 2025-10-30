import argparse
import csv
import os
import sys
from urllib.parse import urlparse


REQUIRED_KEYS = {
    'package_name',
    'repo_url_or_path',
    'test_repo_mode',
    'output_image',
    'ascii_mode',
    'max_depth',
}

VALID_TEST_REPO_MODES = {'none', 'local', 'clone'}
VALID_ASCII_MODES = {'none', 'tree'}


class ConfigError(Exception):
    pass


def read_csv_config(path):
    if not os.path.isfile(path):
        raise ConfigError(f"Файл конфигурации не найден: {path}")

    cfg = {}
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                raise ConfigError("CSV пустой")

            has_header = False
            if len(header) >= 2 and header[0].strip().lower() == 'key':
                has_header = True
            else:
                key = header[0].strip()
                val = header[1].strip() if len(header) >= 2 else ''
                cfg[key] = val

            for row in reader:
                if not row:
                    continue
                if len(row) < 2:
                    raise ConfigError(f"Неверная строка CSV (ожидалось 2 колонки): {row}")
                key = row[0].strip()
                val = row[1].strip()
                if key == '':
                    raise ConfigError(f"Пустой ключ в CSV: {row}")
                cfg[key] = val

    except csv.Error as e:
        raise ConfigError(f"Ошибка чтения CSV: {e}")

    return cfg


def validate_and_normalize(cfg):
    missing = REQUIRED_KEYS - set(cfg.keys())
    if missing:
        raise ConfigError(f"Отсутствуют обязательные параметры: {', '.join(sorted(missing))}")

    out = {}

    pkg = cfg['package_name'].strip()
    if not pkg:
        raise ConfigError("package_name не может быть пустым")
    out['package_name'] = pkg

    repo = cfg['repo_url_or_path'].strip()
    if not repo:
        raise ConfigError("repo_url_or_path не может быть пустым")
    parsed = urlparse(repo)
    if parsed.scheme in ('http', 'https', 'git') and parsed.netloc:
        out['repo_url_or_path'] = repo
        out['repo_type'] = 'url'
    else:
        if os.path.exists(repo):
            out['repo_url_or_path'] = os.path.abspath(repo)
            out['repo_type'] = 'local'
        else:
            out['repo_url_or_path'] = repo
            out['repo_type'] = 'unknown'


    mode = cfg['test_repo_mode'].strip().lower()
    if mode not in VALID_TEST_REPO_MODES:
        raise ConfigError(f"test_repo_mode должен быть одним из: {', '.join(VALID_TEST_REPO_MODES)}")

    if mode == 'local' and out['repo_type'] == 'unknown':
        raise ConfigError("test_repo_mode=local, но repo_url_or_path не указывает на существующую локальную директорию")
    out['test_repo_mode'] = mode

    out_img = cfg['output_image'].strip()
    if not out_img:
        raise ConfigError("output_image не может быть пустым")

    if not os.path.splitext(out_img)[1]:
        raise ConfigError("output_image должно содержать расширение файла, например .png или .svg")
    out['output_image'] = out_img

    ascii_mode = cfg['ascii_mode'].strip().lower()
    if ascii_mode not in VALID_ASCII_MODES:
        raise ConfigError(f"ascii_mode должен быть одним из: {', '.join(VALID_ASCII_MODES)}")
    out['ascii_mode'] = ascii_mode

    max_depth_raw = cfg['max_depth'].strip()
    if max_depth_raw == '':
        raise ConfigError("max_depth не может быть пустым")
    try:
        max_depth = int(max_depth_raw)
    except ValueError:
        raise ConfigError("max_depth должен быть целым числом")
    if max_depth < 0:
        raise ConfigError("max_depth должен быть >= 0")
    out['max_depth'] = max_depth

    return out


def print_kv(cfg_norm):
    print("Параметры конфигурации (ключ=значение):")
    for k in sorted(cfg_norm.keys()):
        print(f"{k}={cfg_norm[k]}")


def main(argv=None):
    parser = argparse.ArgumentParser(description='depviz stage1 - CSV-configurable CLI prototype')
    parser.add_argument('--config', '-c', required=True, help='Путь к CSV файлу конфигурации')
    args = parser.parse_args(argv)

    try:
        cfg = read_csv_config(args.config)
    except ConfigError as e:
        print(f"Ошибка конфигурации: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        cfg_norm = validate_and_normalize(cfg)
    except ConfigError as e:
        print(f"Ошибка в параметрах: {e}", file=sys.stderr)
        sys.exit(3)

    print_kv(cfg_norm)

if __name__ == '__main__':
    main()
