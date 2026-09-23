# python3 bundle.py a/a.js a/y.js

import sys

base64 = '$0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'

def resolve (f, file):
    if f.startswith('./'):
        f = f[2:]
    i = f[0]
    if i != '.' and i != '/':
        f = file[:file.rfind('/')] + '/' + f
    elif f.startswith('../'):
        while f.startswith('../'):
            f = f[3:]
            file = file[:file.rfind('/')]
        f = file[:file.rfind('/')] + '/' + f
    if not f.endswith('.js'):
        f += '.js'
    return f

def substitute (text, past, new):
    i = len(past)
    j = len(new)
    a = text.find(past)
    while a != -1:
        if len(text) < a + i + 1:
            break
        elif text[a + i] in base64 or (a != 0 and text[a - 1] in base64 + '"\'.'):
            a = text.find(past, a + i)
            continue
        text = text[:a] + new + text[a + i:]
        a = text.find(past, a + j)
    return text

def parse (file, modules, texts):
    f = open(file, 'r')
    if not f.closed:
        text = f.read()
    else:
        texts[file] = ''
        return
    lines = text.split('\n')
    remove = False
    text = ''
    for line in lines:
        if line.lstrip().startswith('//'):
            continue
        i = line.find('/*')
        if not remove and i != -1 and '//*' not in line:
            j = line.find('*/')
            if j != -1:
                line = line[:i] + ' ' + line[j + 2:]
            else:
                line = line[:i]
                remove = True
        if remove:
            i = line.find('*/')
            if i != -1:
                line = line[i + 2:]
                remove = False
            else:
                continue
        line = line.rstrip()
        if line:
            text += line + '\n'
    files = {file: []}
    order = []
    texta = text
    i = text.find('import ')
    while i != -1:
        if i != 0:
            j = text[i - 1]
            if j != '\t' and j != '\n' and j != ' ':
                text = text[i + 6:]
                i = text.find('import ')
                continue
        i += 6
        while text[i] == ' ':
            i += 1
        text = text[i:]
        i = text.find('from')
        j = text.find('"')
        k = text.find("'")
        names = []
        if i != -1 and (i < j or j == -1) and (i < k or k == -1):
            while i < len(text):
                j = text[i - 1]
                k = text[i + 4]
                if (j == ' ' or j == '}') and (k == ' ' or k == '"' or k == "'"):
                    break
                i += 4
                i = text[i:].find('from')
            names = text[:i].replace(',', ' ').replace('{', ' ').replace('}', ' ').split(' ')
            names = [name for name in names if name != '']
            i += 5
            while text[i] == ' ':
                i += 1
        else:
            i = 0
        f = text[i]
        if f == '"' or f == "'":
            text = text[i + 1:]
            f = resolve(text[:text.find(f)], file)
            if f not in order:
                files[f] = []
                order.append(f)
            files[f] += names
        i = text.find('import ')
    mods = []
    modules[file] = []
    for f in order:
        if f not in texts:
            mods.append(f)
            if f not in modules:
                modules[file] = mods
                return
    declares = ['async', 'class', 'const', 'default', 'function', 'let', 'var']
    defines = ['\n', ' ', '(', ',', '.', '[']
    text = texta
    i = text.find('export ')
    while i != -1:
        text = text[i + 7:]
        for name in declares:
            i = text.find(name)
            if i != -1 and i < 3:
                text = text[i + len(name):]
        names = ''
        i = text.find('\n')
        if i != -1:
            names = text[:i]
        i = 0
        while names[i] == ' ':
            i += 1
        split = []
        if names[i] == '{':
            names = names[i + 1:]
            split = names[:names.find('}')].split(',')
        else:
            i = names.find('(')
            j = names.find('=')
            if j == -1 or (i < j and i != -1):
                split.append(names)
            else:
                while j != -1 and names[j + 1] != '>':
                    split.append(names[:j])
                    names = names[j:]
                    j = names.find(',')
                    if j == -1:
                        break
                    names = names[j:]
                    j = names.find('=')
        for name in split:
            while name[0] in defines:
                name = name[1:]
            for i in defines:
                j = name.find(i)
                if j != -1:
                    name = name[:j]
            files[file].append(name)
        i = text.find('export ')
    text = texta
    for f in files:
        path = f[:-3]
        path = ''.join([i if i in base64 else '_' for i in path])
        for name in files[f]:
            text = substitute(text, name, name + '_' + path)
    lines = text.split('\n')
    text = ''
    for line in lines:
        a = line.lstrip()
        if a.startswith('export default '):
            line = a[15:]
        elif a.startswith('export '):
            line = a[7:]
            a = line.lstrip()
            if a[0] == '{':
                continue
        if line and not a.startswith('import '):
            text += line + '\n'
    texts[file] = text

def build (file='a/a.js', output='a/y.js'):
    imported = []
    imports = [file]
    modules = {}
    texts = {}
    while len(imports) != 0:
        file = imports[0]
        if file in imported:
            imports.pop(0)
        else:
            parse(file, modules, texts)
            imports = modules[file] + imports
            if file in texts:
                imported.append(file)
    text = ''
    for file in imported:
        text += texts[file]
    with open(output, 'w') as f:
        f.write(text)

build(sys.argv[1], sys.argv[2])