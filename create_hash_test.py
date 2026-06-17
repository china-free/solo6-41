import os
import shutil
import time


def create_hash_test_dirs():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_hash_check')
    dir_a = os.path.join(base, 'dir_a')
    dir_b = os.path.join(base, 'dir_b')

    if os.path.exists(base):
        shutil.rmtree(base)

    os.makedirs(dir_a, exist_ok=True)
    os.makedirs(dir_b, exist_ok=True)

    content_a = "This content is identical in both files."
    content_b = "This content is actually DIFFERENT."

    with open(os.path.join(dir_a, 'same_content.txt'), 'w') as f:
        f.write(content_a)
    time.sleep(0.2)

    with open(os.path.join(dir_b, 'same_content.txt'), 'w') as f:
        f.write(content_a)
    time.sleep(0.2)

    now = time.time()
    os.utime(os.path.join(dir_a, 'same_content.txt'), (now - 10000, now - 10000))
    os.utime(os.path.join(dir_b, 'same_content.txt'), (now, now))

    with open(os.path.join(dir_a, 'different_content.txt'), 'w') as f:
        f.write(content_a)
    time.sleep(0.2)

    with open(os.path.join(dir_b, 'different_content.txt'), 'w') as f:
        f.write(content_b)
    time.sleep(0.2)

    with open(os.path.join(dir_a, 'only_in_a.txt'), 'w') as f:
        f.write("Only in A")
    time.sleep(0.2)

    print("Hash test directories created:")
    print(f"  Dir A: {dir_a}")
    print(f"  Dir B: {dir_b}")
    print(f"\nFiles:")
    print(f"  same_content.txt    -> same content, different timestamps (should NOT be modified)")
    print(f"  different_content.txt -> different content (SHOULD be modified)")
    print(f"  only_in_a.txt       -> only in A (should be added)")
    return dir_a, dir_b


if __name__ == '__main__':
    create_hash_test_dirs()
