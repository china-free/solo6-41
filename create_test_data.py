import os
import shutil
import time


def create_test_dirs():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
    source = os.path.join(base, 'source')
    target = os.path.join(base, 'target')

    if os.path.exists(base):
        shutil.rmtree(base)

    os.makedirs(source, exist_ok=True)
    os.makedirs(target, exist_ok=True)

    os.makedirs(os.path.join(source, 'docs'), exist_ok=True)
    os.makedirs(os.path.join(source, 'images'), exist_ok=True)
    os.makedirs(os.path.join(target, 'docs'), exist_ok=True)

    with open(os.path.join(source, 'file1.txt'), 'w') as f:
        f.write('Hello World from source')
    time.sleep(0.1)

    with open(os.path.join(source, 'docs', 'readme.txt'), 'w') as f:
        f.write('This is readme')
    time.sleep(0.1)

    with open(os.path.join(source, 'images', 'pic1.jpg'), 'wb') as f:
        f.write(b'\xff\xd8\xff' + b'\x00' * 100)
    time.sleep(0.1)

    with open(os.path.join(source, 'script.py'), 'w') as f:
        f.write('print("hello")\n')
    time.sleep(0.1)

    with open(os.path.join(target, 'file1.txt'), 'w') as f:
        f.write('Old content')
    time.sleep(0.1)

    with open(os.path.join(target, 'docs', 'readme.txt'), 'w') as f:
        f.write('This is readme')
    time.sleep(0.1)

    with open(os.path.join(target, 'old_file.txt'), 'w') as f:
        f.write('This file should be deleted after sync')
    time.sleep(0.1)

    print("Test directories created:")
    print(f"  Source: {source}")
    print(f"  Target: {target}")
    return source, target


if __name__ == '__main__':
    create_test_dirs()
