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

def substitute (match, next, text):
    a = text.find(match)
    i = len(match)
    j = len(next)
    while a != -1:
        if text[a + i] in base64 or (a != 0 and text[a - 1] in base64 + '"\'.'):
            a = text.find(match, a + i)
        else:
            text = text[:a] + next + text[a + i:]
            a = text.find(match, a + j)
    return text

def parse (file, modules, texts):
    try:
        with open(file, 'r') as f:
            text = f.read()
    except:
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
    defaults = {}
    exports = {file: {}}
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
        defaulted = ''
        names = {}
        text = text[i:]
        i = text.find('from')
        j = text.find('"')
        k = text.find("'")
        if i != -1 and (i < j or j == -1) and (i < k or k == -1):
            length = len(text)
            while i < length:
                j = text[i - 1]
                k = text[i + 4]
                if (j == ' ' or j == '}') and (k == ' ' or k == '"' or k == "'"):
                    break
                i += 4
                i = text[i:].find('from')
            variables = text[:i]
            j = variables.find('{')
            if j != -1:
                split = variables[j + 1:variables.find('}')].split(',')
                variables = variables[:j]
                for name in split:
                    name = name.lstrip().rstrip()
                    j = name.find(' as ')
                    if j != -1:
                        names[name[:j]] = name[j + 4:]
                    elif name:
                        names[name] = name
            name = variables[:variables.find(',')]
            name = name.lstrip().rstrip()
            if name:
                defaulted = name
                names[name] = name
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
                exports[f] = {}
                order.append(f)
            if defaulted:
                defaults[f] = defaulted
            for name in names:
                exports[f][name] = names[name]
        i = text.find('import ')
    dependencies = False
    mods = []
    for f in order:
        if f not in texts:
            mods.append(f)
            if f not in modules:
                dependencies = True
    if dependencies:
        modules[file] = mods
        return
    declares = ['async', 'class', 'const', 'default', 'function', 'let', 'var']
    defines = ['\n', ' ', '(', ',', '.', '[']
    text = texta
    i = text.find('export ')
    while i != -1:
        text = text[i + 7:]
        if text.find('default ') == 0:
            i = text.find('export ')
            continue
        for name in declares:
            i = text.find(name)
            if i != -1 and i < 3:
                text = text[i + len(name):]
        i = text.find('\n')
        if i != -1:
            variables = text[:i]
            i = 0
            length = len(variables)
            while i < length and variables[i] == ' ':
                i += 1
            split = []
            if i < length and variables[i] == '{':
                variables = variables[i + 1:]
                split = variables[:variables.find('}')].split(',')
            else:
                i = variables.find('(')
                j = variables.find('=')
                if j == -1 or (i < j and i != -1):
                    split.append(variables)
                else:
                    while j != -1 and variables[j + 1] != '>':
                        split.append(variables[:j])
                        variables = variables[j:]
                        j = variables.find(',')
                        if j == -1:
                            break
                        variables = variables[j:]
                        j = variables.find('=')
            for name in split:
                while name[0] in defines:
                    name = name[1:]
                for i in defines:
                    j = name.find(i)
                    if j != -1:
                        name = name[:j]
                exports[file][name] = name
        i = text.find('export ')
    defaulted = ''
    text = texta
    for f in exports:
        path = f[:-3]
        path = ''.join([i if i in base64 else '_' for i in path])
        if f == file:
            defaulted = path
        exported = exports[f]
        for named in exported:
            name = exported[named]
            if f in defaults and defaults[f] == name:
                text = substitute(name, '_' + path, text)
            else:
                text = substitute(name, named + '_' + path, text)
    lines = text.split('\n')
    text = ''
    for line in lines:
        a = line.lstrip()
        if a.startswith('export default '):
            line = '_' + defaulted + ' = ' + a[15:]
        elif a.startswith('export '):
            line = a[7:]
            a = line.lstrip()
            if a[0] == '{':
                continue
        if line and not a.startswith('import '):
            text += line + '\n'
    texts[file] = text

def build (file, output):
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
            if file in modules:
                imports = modules[file] + imports
            if file in texts:
                imported.append(file)
                imports.pop(0)
    text = ''
    for file in imported:
        text += texts[file]
    with open(output, 'w') as f:
        f.write(text)

build(sys.argv[1] if len(sys.argv) > 1 else 'a/a.js', sys.argv[2] if len(sys.argv) > 2 else 'a/y.js')