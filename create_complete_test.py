import os
import shutil
import time


def create_complete_test():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_complete')
    base = base[0] if isinstance(base, tuple) else base

    dir_a = os.path.join(base, 'dir_a')
    dir_b = os.path.join(base, 'dir_b')

    if os.path.exists(base):
        shutil.rmtree(base)

    os.makedirs(dir_a, exist_ok=True)
    os.makedirs(os.path.join(dir_a, 'subdir'), exist_ok=True)
    os.makedirs(dir_b, exist_ok=True)
    os.makedirs(os.path.join(dir_b, 'subdir'), exist_ok=True)

    content_same = "This content is identical in both."
    content_diff_a = "Content from A."
    content_diff_b = "Content from B, which is different."

    with open(os.path.join(dir_a, 'conflict_newer_b.txt'), 'w') as f:
        f.write(content_diff_a)
    time.sleep(0.2)

    with open(os.path.join(dir_b, 'conflict_newer_b.txt'), 'w') as f:
        f.write(content_diff_b)
    time.sleep(0.5)

    with open(os.path.join(dir_a, 'conflict_newer_a.txt'), 'w') as f:
        f.write(content_diff_b)
    time.sleep(0.5)

    with open(os.path.join(dir_b, 'conflict_newer_a.txt'), 'w') as f:
        f.write(content_diff_a)
    time.sleep(0.2)

    with open(os.path.join(dir_a, 'same_content.txt'), 'w') as f:
        f.write(content_same)
    time.sleep(0.2)

    with open(os.path.join(dir_b, 'same_content.txt'), 'w') as f:
        f.write(content_same)
    time.sleep(0.5)

    now = time.time()
    os.utime(os.path.join(dir_a, 'same_content.txt'), (now - 5000, now - 5000))
    os.utime(os.path.join(dir_b, 'same_content.txt'), (now, now))
    time.sleep(0.2)

    with open(os.path.join(dir_a, 'only_in_a.txt'), 'w') as f:
        f.write("Only in A")
    time.sleep(0.2)

    with open(os.path.join(dir_b, 'only_in_b.txt'), 'w') as f:
        f.write("Only in B")
    time.sleep(0.2)

    with open(os.path.join(dir_a, 'subdir', 'doc_a.pdf'), 'wb') as f:
        f.write(b'%PDF-1.4 fake pdf content')
    time.sleep(0.2)

    with open(os.path.join(dir_a, 'image_a.jpg'), 'wb') as f:
        f.write(b'\xff\xd8\xff\xe0 fake jpeg content')
    time.sleep(0.2)

    with open(os.path.join(dir_b, 'image_b.jpg'), 'wb') as f:
        f.write(b'\xff\xd8\xff\xe0 another jpeg')
    time.sleep(0.2)

    with open(os.path.join(dir_a, 'script.py'), 'w') as f:
        f.write('print("hello from A")\n')
    time.sleep(0.2)

    with open(os.path.join(dir_b, 'script.py'), 'w') as f:
        f.write('print("hello from B")\n')
    time.sleep(0.5)

    print("Complete test directories created:")
    print(f"  Dir A: {dir_a}")
    print(f"  Dir B: {dir_b}")
    print(f"\nTest scenarios:")
    print(f"  [CONFLICT] conflict_newer_b.txt - B is newer, content differs")
    print(f"  [CONFLICT] conflict_newer_a.txt - A is newer, content differs")
    print(f"  [TIME-ONLY] same_content.txt - same content, different timestamps")
    print(f"  [NEW] only_in_a.txt - only in A")
    print(f"  [NEW] only_in_b.txt - only in B")
    print(f"  [NEW] subdir/doc_a.pdf - only in A")
    print(f"  [FILTER TEST] image_a.jpg, image_b.jpg - jpg files")
    print(f"  [CONFLICT] script.py - content differs, B is newer")
    return dir_a, dir_b


if __name__ == '__main__':
    create_complete_test()
