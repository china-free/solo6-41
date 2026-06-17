import os
import shutil
import time


def create_bidir_test_dirs():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data_bidir')
    dir_a = os.path.join(base, 'dir_a')
    dir_b = os.path.join(base, 'dir_b')

    if os.path.exists(base):
        shutil.rmtree(base)

    os.makedirs(dir_a, exist_ok=True)
    os.makedirs(dir_b, exist_ok=True)

    with open(os.path.join(dir_a, 'only_in_a.txt'), 'w') as f:
        f.write('Only in A')
    time.sleep(0.1)

    with open(os.path.join(dir_b, 'only_in_b.txt'), 'w') as f:
        f.write('Only in B')
    time.sleep(0.1)

    with open(os.path.join(dir_a, 'shared.txt'), 'w') as f:
        f.write('Old version')
    time.sleep(0.5)

    with open(os.path.join(dir_b, 'shared.txt'), 'w') as f:
        f.write('Newer version from B')
    time.sleep(0.1)

    with open(os.path.join(dir_a, 'both_same.txt'), 'w') as f:
        f.write('Same content')
    time.sleep(0.1)
    with open(os.path.join(dir_b, 'both_same.txt'), 'w') as f:
        f.write('Same content')
    time.sleep(0.1)

    print("Bidirectional test directories created:")
    print(f"  Dir A: {dir_a}")
    print(f"  Dir B: {dir_b}")
    return dir_a, dir_b


if __name__ == '__main__':
    create_bidir_test_dirs()
