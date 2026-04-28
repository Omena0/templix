from .build import generate
import json
import os

def main():
    if os.path.exists('config.json'):
        with open('config.json') as f:
            conf = json.load(f)

    conf = {"source": "src", "output": "build"}

    with open('config.json', 'w') as f:
        json.dump(conf, f)

    generate(conf)
    print(f'Built page to {conf['output']}/')

if __name__ == '__main__':
    main()

